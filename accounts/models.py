"""
Accounts app models.
We extend Django's built-in User model with an Investigator Profile.
"""

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends Django's User model to add role information.
    Each User has one UserProfile (one-to-one relationship).
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('investigator', 'Investigator'),
    ]

    # Link to Django's built-in User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='investigator')
    phone_number = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    badge_number = models.CharField(max_length=20, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def is_admin(self):
        """Check if the user is an admin."""
        return self.role == 'admin'
