from typing import Literal

from ninja import Schema, ModelSchema

from saiddit.schemas import UserSchema, UserListSchema

from posts.models import Post, PostImage, Comment, PostVote, CommentVote
from space.schemas import SpaceListSchema

class PostCreateSchema(ModelSchema):
    class Meta:
        model = Post
        fields = ['title', 'content']

class CommentCreateSchema(ModelSchema):
    class Meta:
        model = Comment
        fields = ['content']

class VoteSchema(Schema):
    vote_type: Literal[1, -1]

class PostImageSchema(ModelSchema):
    image: str

    class Meta:
        model = PostImage
        fields = ['id', 'image']

    @staticmethod
    def resolve_image(obj):
        # An ImageField serializes to its name in storage by default; what a
        # client actually needs is something it can put in a src attribute.
        return obj.image.url if obj.image else ''

class PostVoteSchema(ModelSchema):
    user: UserListSchema | None

    class Meta:
        model = PostVote
        fields = ['id', 'user', 'vote_type']

class CommentVoteSchema(ModelSchema):
    user: UserListSchema | None

    class Meta:
        model = CommentVote
        fields = ['id', 'user', 'vote_type']

class CommentListSchema(ModelSchema):
    author: UserListSchema | None
    # Replies are paged separately; this says whether there are any to fetch.
    reply_count: int = 0
    score: int
    # The requesting user's own vote: 1, -1, or 0. Annotated by the endpoints.
    my_vote: int = 0

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']

class CommentDetailSchema(ModelSchema):
    author: UserSchema | None
    replies: list['CommentDetailSchema'] = []
    score: int
    # The requesting user's own vote: 1, -1, or 0. Annotated by the endpoints.
    my_vote: int = 0

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at', 'updated_at']

CommentDetailSchema.model_rebuild()

class PostListSchema(ModelSchema):
    author: UserListSchema | None
    space: SpaceListSchema | None
    # Prefetched by the listing endpoints; see list_space_posts.
    images: list[PostImageSchema] = []
    score: int
    # The requesting user's own vote: 1, -1, or 0. Annotated by the endpoints.
    my_vote: int = 0
    comment_count: int

    class Meta:
        model = Post
        fields = ['id', 'title', 'author', 'space', 'created_at']

class PostDetailSchema(ModelSchema):
    author: UserSchema | None
    space: SpaceListSchema | None
    images: list[PostImageSchema] = []
    score: int
    # The requesting user's own vote: 1, -1, or 0. Annotated by the endpoints.
    my_vote: int = 0

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'space', 'created_at', 'updated_at']
