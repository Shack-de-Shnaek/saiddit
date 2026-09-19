from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from saiddit.models import BaseModel

class Space(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    description = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='created_spaces')

    def is_member(self, user):
        if not user or not user.is_authenticated:
            return False

        return self.memberships.filter(user=user).exists()

    def is_moderator(self, user):
        if not user or not user.is_authenticated:
            return False

        if self.created_by_id == user.pk:
            return True

        return self.memberships.filter(user=user, is_moderator=True).exists()

    def can_be_edited_by(self, user):
        """Only the creator may edit or delete a space."""
        if not user or not user.is_authenticated:
            return False

        return self.created_by_id == user.pk

    def can_be_deleted_by(self, user):
        return self.can_be_edited_by(user)

    def can_manage_moderators(self, user):
        return self.can_be_edited_by(user)

    def can_be_joined_by(self, user):
        """Private spaces are joined by invitation, not by asking."""
        if not user or not user.is_authenticated:
            return False

        return not self.is_private

    def allows_contributions_from(self, user):
        """Anyone may contribute to a public space; private ones need membership."""
        if not user or not user.is_authenticated:
            return False

        return not self.is_private or self.is_member(user)

    def clean(self):
        super().clean()

        if not self.name.strip():
            raise ValidationError({'name': 'Name cannot be blank.'})

    def save(self, *args, **kwargs):
        self.name = self.name.strip()

        if not self.slug:
            self.slug = slugify(self.name)

        self.full_clean()
        super().save(*args, **kwargs)

        # The creator moderates their own space from the moment it exists.
        if self.created_by_id:
            SpaceMembership.objects.get_or_create(
                user_id=self.created_by_id,
                space=self,
                defaults={'is_moderator': True},
            )

    def __str__(self):
        return self.name

class SpaceMembership(BaseModel):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='memberships')
    is_moderator = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'space')

    @property
    def is_space_creator(self):
        return self.space.created_by_id == self.user_id

    def clean(self):
        super().clean()

        # The creator's own moderator status is not revocable.
        if self.is_space_creator and not self.is_moderator:
            raise ValidationError(
                {'is_moderator': 'The creator of a space cannot be removed as a moderator.'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_space_creator:
            raise ValidationError('The creator cannot leave their own space.')

        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} in {self.space.name}"
