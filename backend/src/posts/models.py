from django.db import models
from django.db.models import OuterRef, Subquery, Sum, Count
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property

from saiddit.models import BaseModel

DELETED_USER_DISPLAY = 'Deleted User'


def vote_score(vote_model, target_field):
    """Sum of vote_type over the votes pointing at the outer row, 0 if none.

    A correlated subquery rather than Sum() over a join, so it stays correct
    when stacked with other aggregates such as Count('replies').
    """
    totals = (
        vote_model.objects.filter(**{target_field: OuterRef('pk')})
        .order_by()
        .values(target_field)
        .annotate(total=Sum('vote_type'))
        .values('total')
    )
    return Coalesce(Subquery(totals, output_field=models.IntegerField()), 0)


def user_vote_type(vote_model, target_field, user):
    """The given user's vote on the outer row: 1, -1, or 0 when they have none.

    Annotated rather than resolved per row, so a page of posts or comments
    still costs one query.
    """
    if not user or not user.is_authenticated:
        return models.Value(0, output_field=models.IntegerField())

    votes = vote_model.objects.filter(
        **{target_field: OuterRef('pk')}, user=user
    ).values('vote_type')

    return Coalesce(Subquery(votes, output_field=models.IntegerField()), 0)


class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            score=vote_score(PostVote, 'post'),
            comment_count=Count('comments', distinct=True)
        )


class CommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(score=vote_score(CommentVote, 'comment'))


class Post(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='posts')
    space = models.ForeignKey('space.Space', on_delete=models.SET_NULL, null=True, related_name='posts')
    comments = GenericRelation(
        'posts.Comment',
        content_type_field='parent_type',
        object_id_field='parent_id',
        related_query_name='post',
    )

    objects = PostManager()

    # Rows fetched through PostManager already carry the annotated score in
    # __dict__, which shadows this; it only runs for instances loaded some
    # other way (a fresh save, the base manager, a generic FK).
    @cached_property
    def score(self):
        return self.votes.aggregate(total=Coalesce(Sum('vote_type'), 0))['total']

    @property
    def author_display(self):
        return self.author.username if self.author else DELETED_USER_DISPLAY

    def can_be_deleted_by(self, user):
        """The author, or a moderator of the space it was posted in."""
        if not user or not user.is_authenticated:
            return False

        if self.author_id == user.pk:
            return True

        return self.space is not None and self.space.is_moderator(user)

    def clean(self):
        super().clean()

        if not self.title.strip():
            raise ValidationError({'title': 'Title cannot be blank.'})

        if not self.content.strip():
            raise ValidationError({'content': 'Content cannot be blank.'})

        # A private space only accepts posts from its members.
        if self.space and self.author and not self.space.allows_contributions_from(self.author):
            raise ValidationError({'space': 'You must be a member of this space to post in it.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        new = self.pk is None
        super().save(*args, **kwargs)
        if new:
            self.refresh_from_db()
            PostVote.objects.create(post=self, user=self.author, vote_type=PostVote.UPVOTE)

    def __str__(self):
        return self.title


class PostImage(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/')

    def __str__(self):
        return f"Image for post: {self.post.title}"

class Comment(BaseModel):
    parent = GenericForeignKey('parent_type', 'parent_id')
    parent_id = models.PositiveIntegerField()
    parent_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='comments')
    content = models.TextField()
    # Generic foreign keys have no database-level cascade; this GenericRelation
    # is what makes Django's collector delete replies along with their parent.
    replies = GenericRelation(
        'posts.Comment',
        content_type_field='parent_type',
        object_id_field='parent_id',
        related_query_name='parent_comment',
    )

    objects = CommentManager()

    

    # NB: not `post` - Post.comments declares related_query_name='post',
    # which puts a reverse accessor of that name on Comment.
    @property
    def root_post(self):
        """Walk up the reply chain to the Post this comment hangs off."""
        node = self.parent

        while isinstance(node, Comment):
            node = node.parent

        return node if isinstance(node, Post) else None

    @property
    def space(self):
        root_post = self.root_post
        return root_post.space if root_post else None

    # Same fallback as Post.score.
    @cached_property
    def score(self):
        return self.votes.aggregate(total=Coalesce(Sum('vote_type'), 0))['total']

    def can_be_deleted_by(self, user):
        """The author, or a moderator of the space the comment sits in."""
        if not user or not user.is_authenticated:
            return False

        if self.author_id == user.pk:
            return True

        space = self.space
        return space is not None and space.is_moderator(user)

    def clean(self):
        super().clean()

        if not self.parent:
            raise ValidationError("Parent object must be set for a comment.")

        if self.parent_type not in (ContentType.objects.get_for_model(Post), ContentType.objects.get_for_model(Comment)):
            raise ValidationError("Parent object must be either a Post or a Comment.")

        if isinstance(self.parent, Comment) and self.parent.pk == self.pk:
            raise ValidationError("A comment cannot be its own parent.")

        if not self.content.strip():
            raise ValidationError({'content': 'Content cannot be blank.'})

        # Commenting follows the same membership rule as posting.
        space = self.space
        if space and self.author and not space.allows_contributions_from(self.author):
            raise ValidationError('You must be a member of this space to comment in it.')

    def save(self, *args, **kwargs):
        new = self.pk is None
        super().save(*args, **kwargs)
        if new:
            self.refresh_from_db()
            CommentVote.objects.create(comment=self, user=self.author, vote_type=CommentVote.UPVOTE)

    def __str__(self):
        author_username = DELETED_USER_DISPLAY
        if self.author:
            author_username = self.author.username

        return f"Comment on {self.parent} by {author_username}"

    class Meta:
        indexes = [
            models.Index(fields=['parent_type', 'parent_id']),
        ]

class BaseVote(BaseModel):
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_CHOICES = (
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    )

    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    vote_type = models.SmallIntegerField(choices=VOTE_CHOICES)

    @property
    def user_display(self):
        return self.user.username if self.user else DELETED_USER_DISPLAY

    class Meta:
        abstract = True

class PostVote(BaseVote):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')

    def __str__(self):
        return f"{self.user_display} voted {self.get_vote_type_display()} on {self.post.title}"

    class Meta:
        unique_together = ('post', 'user')

class CommentVote(BaseVote):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='votes')

    def __str__(self):
        return f"{self.user_display} voted {self.get_vote_type_display()} on comment {self.comment.id}"

    class Meta:
        unique_together = ('comment', 'user')
