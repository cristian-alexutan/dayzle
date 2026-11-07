"""API serializers for the accounts app."""

from rest_framework import serializers

from ..models import User


class GoogleLoginInputSerializer(serializers.Serializer):
    credential = serializers.CharField(trim_whitespace=True)


class UserProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "display_name"]
        read_only_fields = fields

    def get_display_name(self, user: User) -> str:
        full_name = user.get_full_name().strip()
        return full_name or user.username


class SessionStateSerializer(serializers.Serializer):
    """Current visitor identity: anonymous guest or signed-in user."""

    is_authenticated = serializers.BooleanField(read_only=True)
    guest_id = serializers.UUIDField(read_only=True)
    user = UserProfileSerializer(read_only=True, allow_null=True)
