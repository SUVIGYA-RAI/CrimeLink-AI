"""
Accounts app admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Show UserProfile inline when editing a User in admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    """Extend the default UserAdmin to include profile info."""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')

    def get_role(self, obj):
        """Display role in the admin list."""
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return 'No Profile'
    get_role.short_description = 'Role'


# Unregister default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
