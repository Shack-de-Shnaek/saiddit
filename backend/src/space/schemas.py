from datetime import datetime

from ninja import Schema, ModelSchema

from saiddit.schemas import UserSchema, UserListSchema

from space.models import Space, SpaceMembership

class ModeratorSchema(Schema):
    username: str

class SpaceCreateSchema(ModelSchema):
    class Meta:
        model = Space
        fields = ['name', 'description', 'is_private']

class SpaceUpdateSchema(ModelSchema):
    class Meta:
        model = Space
        fields = ['name', 'description', 'is_private']
        fields_optional = '__all__'

class SpaceDetailSchema(ModelSchema):
    class Meta:
        model = Space
        fields = ['id', 'name', 'slug', 'description', 'is_private', 'created_by', 'created_at']

class SpaceListSchema(ModelSchema):
    class Meta:
        model = Space
        fields = ['id', 'name', 'slug', 'is_private']

class SpaceMemberSchema(ModelSchema):
    user: UserListSchema

    class Meta:
        model = SpaceMembership
        fields = ['id', 'user', 'is_moderator']

class SpaceMembersSchema(SpaceListSchema):
    members: list[UserListSchema]

    class Meta:
        model = SpaceMembership
        fields = ['id', 'name', 'slug', 'is_private', 'members']
