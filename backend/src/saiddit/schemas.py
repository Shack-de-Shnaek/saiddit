from datetime import datetime

from django.contrib.auth import get_user_model

from ninja import Schema, ModelSchema

class UserSchema(ModelSchema):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']

class UserListSchema(ModelSchema):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email']
