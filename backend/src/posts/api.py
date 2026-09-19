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
    PostVoteSchema,
    VoteSchema,
)

router = Router()

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
