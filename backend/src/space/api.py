from typing import Literal

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import django_auth

from posts.models import Post, PostVote, user_vote_type
from posts.schemas import PostCreateSchema, PostDetailSchema, PostListSchema

from space.models import Space, SpaceMembership
from space.schemas import (
    ModeratorSchema,
    SpaceCreateSchema,
    SpaceDetailSchema,
    SpaceListSchema,
    SpaceMemberSchema,
    SpaceUpdateSchema,
)

router = Router()


def visible_spaces(user):
    """Public spaces, plus private ones the user belongs to."""
    if not user.is_authenticated:
        return Space.objects.filter(is_private=False)

    return Space.objects.filter(
        Q(is_private=False) | Q(memberships__user=user)
    ).distinct()


POST_ORDERING = {
    'new': '-created_at',
    'old': 'created_at',
    'votes': '-score',
}


@router.get('/', response=list[SpaceListSchema], auth=None)
def list_spaces(request):
    return visible_spaces(request.user).order_by('name')


@router.post('/', response={201: SpaceDetailSchema}, auth=django_auth)
def create_space(request, payload: SpaceCreateSchema):
    space = Space(
        name=payload.name,
        description=payload.description,
        is_private=payload.is_private,
        created_by=request.user,
    )

    space.save()
    return 201, space


# Declared ahead of '/{slug}' so 'search' is never taken for a slug.
@router.get('/search', response=list[SpaceListSchema], auth=None)
@paginate
def search_spaces(request, q: str = Query(..., min_length=1, max_length=255)):
    """Spaces the user can see whose name or description contains `q`."""
    q = q.strip()

    if not q:
        raise HttpError(422, 'Search query cannot be blank.')

    return visible_spaces(request.user).filter(
        Q(name__icontains=q) | Q(description__icontains=q)
    ).order_by('name', 'pk')


# Declared ahead of '/{slug}' so 'my-spaces' is never taken for a slug.
@router.get('/my-spaces', response=list[SpaceListSchema], auth=django_auth)
def list_my_spaces(request):
    """Spaces the signed-in user is a member of."""
    # Membership implies visibility, so private spaces need no extra filter.
    return Space.objects.filter(memberships__user=request.user).distinct().order_by('name')


@router.get('/{slug}', response={200: SpaceDetailSchema}, auth=None)
def get_space(request, slug: str):
    return 200, get_object_or_404(visible_spaces(request.user), slug=slug)


@router.patch('/{slug}', response={200: SpaceDetailSchema}, auth=django_auth)
def update_space(request, slug: str, payload: SpaceUpdateSchema):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    if not space.can_be_edited_by(request.user):
        raise PermissionDenied('Only the creator can update this space.')

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(space, field, value)

    space.save()
    return 200, space


@router.delete('/{slug}', response={204: None}, auth=django_auth)
def delete_space(request, slug: str):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    if not space.can_be_deleted_by(request.user):
        raise PermissionDenied('Only the creator can delete this space.')

    space.delete()
    return 204, None


@router.get('/{slug}/posts', response=list[PostListSchema], auth=None)
@paginate
def list_space_posts(request, slug: str, sort: Literal['new', 'old', 'votes'] = 'new'):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    # PostManager annotates score, which the 'votes' sort relies on.
    # Images come back with the page rather than one query per post.
    posts = (
        space.posts.select_related('author', 'space')
        .prefetch_related('images')
        .annotate(my_vote=user_vote_type(PostVote, 'post', request.user))
    )
    # Ties on score fall back to newest, then id, so paging stays stable.
    return posts.order_by(POST_ORDERING[sort], '-created_at', '-pk')


@router.post('/{slug}/posts', response={201: PostDetailSchema}, auth=django_auth)
def create_space_post(request, slug: str, payload: PostCreateSchema):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    # Post.clean() enforces the private-space membership rule on save.
    post = Post(
        title=payload.title,
        content=payload.content,
        author=request.user,
        space=space,
    )
    post.save()
    return 201, post


@router.get('/{slug}/members', response={200: list[SpaceMemberSchema]}, auth=None)
def list_members(request, slug: str):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)
    return 200, space.memberships.select_related('user').order_by('user__username')


@router.post('/{slug}/join', response={201: SpaceMemberSchema}, auth=django_auth)
def join_space(request, slug: str):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    if not space.can_be_joined_by(request.user):
        raise PermissionDenied('This space is private; you have to be invited.')

    membership, created = SpaceMembership.objects.get_or_create(
        user=request.user, space=space
    )
    if not created:
        raise HttpError(409, 'You are already a member of this space.')

    return 201, membership


@router.post('/{slug}/leave', response={204: None}, auth=django_auth)
def leave_space(request, slug: str):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    membership = SpaceMembership.objects.filter(user=request.user, space=space).first()
    if membership is None:
        raise Http404('You are not a member of this space.')

    # SpaceMembership.delete() refuses to let the creator leave.
    membership.delete()
    return 204, None


@router.post('/{slug}/moderators', response={200: SpaceMemberSchema}, auth=django_auth)
def add_moderator(request, slug: str, payload: ModeratorSchema):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    if not space.can_manage_moderators(request.user):
        raise PermissionDenied('Only the creator can manage moderators.')

    membership = get_object_or_404(space.memberships, user__username=payload.username)
    membership.is_moderator = True
    membership.save()
    return 200, membership


@router.delete('/{slug}/moderators/{username}', response={204: None}, auth=django_auth)
def remove_moderator(request, slug: str, username: str):
    space = get_object_or_404(visible_spaces(request.user), slug=slug)

    if not space.can_manage_moderators(request.user):
        raise PermissionDenied('Only the creator can manage moderators.')

    membership = get_object_or_404(space.memberships, user__username=username)
    # SpaceMembership.clean() refuses to demote the creator.
    membership.is_moderator = False
    membership.save()
    return 204, None
