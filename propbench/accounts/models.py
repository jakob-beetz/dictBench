from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """
    Custom user model for PropBench that extends Django's built-in User model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Role-based permissions
    is_expert = models.BooleanField(default=False, help_text="Designates whether this user has expert privileges.")
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en-EN')
    
    # Activity tracking
    last_active = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
