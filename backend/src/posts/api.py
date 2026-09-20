from typing import Literal

from django.contrib.contenttypes.models import ContentType
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import File, Router
from ninja.files import UploadedFile
from ninja.pagination import paginate
from ninja.security import django_auth

from posts.models import Comment, CommentVote, Post, PostImage, PostVote, user_vote_type
from posts.schemas import (
    CommentCreateSchema,
    CommentDetailSchema,
    CommentListSchema,
    CommentVoteSchema,
    PostDetailSchema,
    PostImageSchema,
    PostListSchema,
    PostVoteSchema,
    VoteSchema,
)

router = Router()

# How a post listing may be sorted, and the column each choice orders on.
# 'votes' leans on the score PostManager annotates.
PostSort = Literal['new', 'old', 'votes']

POST_ORDERING = {
    'new': '-created_at',
    'old': 'created_at',
    'votes': '-score',
}


def post_page(queryset, user, sort):
    """A post queryset ready to be paged and serialized as PostListSchema.

    Author, space and images come back with the page rather than one query per
    post, and the caller's own vote is annotated instead of resolved per row.
    """
    return (
        queryset.select_related('author', 'space')
        .prefetch_related('images')
        .annotate(my_vote=user_vote_type(PostVote, 'post', user))
        # Ties on score fall back to newest, then id, so paging stays stable.
        .order_by(POST_ORDERING[sort], '-created_at', '-pk')
    )


# Bounds on an upload; a post is a handful of pictures, not an album.
MAX_POST_IMAGES = 10
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def validate_image_upload(upload):
    """Reject anything that is not really an image.

    A model ImageField only checks this when a form cleans it -- full_clean()
    on the model happily accepts a text file -- so the check has to be explicit.
    forms.ImageField is what opens the file with Pillow and verifies it.
    """
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError(
            {'images': f'{upload.name} is larger than the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit.'}
        )

    try:
        forms.ImageField().clean(upload)
    except ValidationError:
        raise ValidationError({'images': f'{upload.name} is not an image.'})
    finally:
        # clean() reads to the end; the file still has to be saved.
        upload.seek(0)


def visible_post(user, post_id):
    """A post in a space the user is allowed to see."""
    post = get_object_or_404(
        Post.objects.annotate(my_vote=user_vote_type(PostVote, 'post', user)), pk=post_id
    )

    if post.space and post.space.is_private and not post.space.is_member(user):
        raise Http404('No Post matches the given query.')

    return post


def visible_comment(user, comment_id):
    comment = get_object_or_404(
        Comment.objects.annotate(my_vote=user_vote_type(CommentVote, 'comment', user)),
        pk=comment_id,
    )
    space = comment.space

    if space and space.is_private and not space.is_member(user):
        raise Http404('No Comment matches the given query.')

    return comment


def comments_under(parent, user=None):
    """Direct children of a post or comment, newest first, with reply counts."""
    return (
        Comment.objects.filter(
            parent_type=ContentType.objects.get_for_model(parent),
            parent_id=parent.pk,
        )
        .select_related('author')
        .annotate(
            reply_count=Count('replies'),
            my_vote=user_vote_type(CommentVote, 'comment', user),
        )
        .order_by('-created_at', '-pk')
    )


@router.get('/feed', response=list[PostListSchema], auth=None)
@paginate
def list_feed(request, sort: PostSort = 'new'):
    """The home feed: posts from the spaces the caller belongs to.

    A guest has no memberships to read, so they get the public spaces instead
    of an empty page. Spaceless posts (their space was deleted) are left out.
    """
    if request.user.is_authenticated:
        posts = Post.objects.filter(space__memberships__user=request.user)
    else:
        posts = Post.objects.filter(space__is_private=False)

    return post_page(posts, request.user, sort)


@router.get('/{post_id}', response={200: PostDetailSchema}, auth=None)
def get_post(request, post_id: int):
    return 200, visible_post(request.user, post_id)


@router.post('/{post_id}/images', response={201: list[PostImageSchema]}, auth=django_auth)
def add_post_images(request, post_id: int, images: list[UploadedFile] = File(...)):
    """Attach images to a post the caller wrote."""
    post = visible_post(request.user, post_id)

    if post.author_id != request.user.pk:
        raise PermissionDenied('Only the author can attach images to this post.')

    if post.images.count() + len(images) > MAX_POST_IMAGES:
        raise ValidationError(
            {'images': f'A post can have at most {MAX_POST_IMAGES} images.'}
        )

    # Checked up front, so a bad file in the batch stores none of them.
    for upload in images:
        validate_image_upload(upload)

    created = []

    with transaction.atomic():
        for upload in images:
            image = PostImage(post=post, image=upload)
            image.full_clean()
            image.save()
            created.append(image)

    return 201, created


@router.delete('/{post_id}', response={204: None}, auth=django_auth)
def delete_post(request, post_id: int):
    post = visible_post(request.user, post_id)

    if not post.can_be_deleted_by(request.user):
        raise PermissionDenied('Only the author or a space moderator can delete this post.')

    # The GenericRelation on Post takes its comment tree with it.
    post.delete()
    return 204, None


@router.get('/{post_id}/comments', response=list[CommentListSchema], auth=None)
@paginate
def list_comments(request, post_id: int):
    """Top-level comments on a post; replies come from list_replies."""
    return comments_under(visible_post(request.user, post_id), request.user)


@router.post('/{post_id}/comments', response={201: CommentDetailSchema}, auth=django_auth)
def add_comment(request, post_id: int, payload: CommentCreateSchema):
    post = visible_post(request.user, post_id)

    # Comment.clean() enforces the space's membership rule.
    comment = Comment(
        parent_type=ContentType.objects.get_for_model(Post),
        parent_id=post.pk,
        author=request.user,
        content=payload.content,
    )
    comment.save()
    return 201, comment


@router.get('/comments/{comment_id}/replies', response=list[CommentListSchema], auth=None)
@paginate
def list_replies(request, comment_id: int):
    return comments_under(visible_comment(request.user, comment_id), request.user)


@router.post('/comments/{comment_id}/replies', response={201: CommentDetailSchema}, auth=django_auth)
def reply_to_comment(request, comment_id: int, payload: CommentCreateSchema):
    parent = visible_comment(request.user, comment_id)

    reply = Comment(
        parent_type=ContentType.objects.get_for_model(Comment),
        parent_id=parent.pk,
        author=request.user,
        content=payload.content,
    )
    reply.save()
    return 201, reply


@router.delete('/comments/{comment_id}', response={204: None}, auth=django_auth)
def delete_comment(request, comment_id: int):
    comment = visible_comment(request.user, comment_id)

    if not comment.can_be_deleted_by(request.user):
        raise PermissionDenied('Only the author or a space moderator can delete this comment.')

    # The GenericRelation on Comment takes nested replies with it.
    comment.delete()
    return 204, None


@router.post('/{post_id}/vote', response={200: PostVoteSchema}, auth=django_auth)
def vote_on_post(request, post_id: int, payload: VoteSchema):
    post = visible_post(request.user, post_id)

    if post.space and not post.space.allows_contributions_from(request.user):
        raise PermissionDenied('You must be a member of this space to vote in it.')

    vote, _ = PostVote.objects.update_or_create(
        post=post, user=request.user, defaults={'vote_type': payload.vote_type}
    )
    return 200, vote


@router.delete('/{post_id}/vote', response={204: None}, auth=django_auth)
def unvote_post(request, post_id: int):
    post = visible_post(request.user, post_id)
    PostVote.objects.filter(post=post, user=request.user).delete()
    return 204, None


@router.post('/comments/{comment_id}/vote', response={200: CommentVoteSchema}, auth=django_auth)
def vote_on_comment(request, comment_id: int, payload: VoteSchema):
    comment = visible_comment(request.user, comment_id)
    space = comment.space

    if space and not space.allows_contributions_from(request.user):
        raise PermissionDenied('You must be a member of this space to vote in it.')

    vote, _ = CommentVote.objects.update_or_create(
        comment=comment, user=request.user, defaults={'vote_type': payload.vote_type}
    )
    return 200, vote


@router.delete('/comments/{comment_id}/vote', response={204: None}, auth=django_auth)
def unvote_comment(request, comment_id: int):
    comment = visible_comment(request.user, comment_id)
    CommentVote.objects.filter(comment=comment, user=request.user).delete()
    return 204, None
