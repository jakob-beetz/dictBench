from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps

from audit.models import Audit

User = get_user_model()


def _create_audit_log(sender, instance, action, data_before=None, data_after=None, user=None, reason=None):
    """
    Helper function to create audit log entries.
    """
    # Get the model name
    entity_type = sender.__name__
    
    # Get the entity ID
    entity_id = str(instance.pk)
    
    # Create the audit log entry
    Audit.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user=user or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None),
        data_before=data_before,
        data_after=data_after,
        reason=reason
    )


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """
    Signal handler to create audit logs for model saves.
    """
    # Skip audit logs for audit model itself to avoid infinite recursion
    if sender == Audit:
        return
    
    # Skip models we don't want to audit
    excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
    excluded_models = ['LogEntry', 'Session', 'ContentType']
    
    if sender._meta.app_label in excluded_apps or sender.__name__ in excluded_models:
        return
    
    # Create audit log
    action = 'create' if created else 'update'
    
    # Data after the save operation
    data_after = {
        field.name: str(getattr(instance, field.name))
        for field in sender._meta.fields
        if not field.name.endswith('_ptr') and field.name not in ['password']
    }
    
    _create_audit_log(
        sender=sender,
        instance=instance,
        action=action,
        data_after=data_after
    )


@receiver(pre_delete)
def audit_pre_delete(sender, instance, **kwargs):
    """
    Signal handler to create audit logs before model deletion.
    """
    # Skip audit logs for audit model itself to avoid infinite recursion
    if sender == Audit:
        return
    
    # Skip models we don't want to audit
    excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
    excluded_models = ['LogEntry', 'Session', 'ContentType']
    
    if sender._meta.app_label in excluded_apps or sender.__name__ in excluded_models:
        return
    
    # Data before deletion
    data_before = {
        field.name: str(getattr(instance, field.name))
        for field in sender._meta.fields
        if not field.name.endswith('_ptr') and field.name not in ['password']
    }
    
    _create_audit_log(
        sender=sender,
        instance=instance,
        action='delete',
        data_before=data_before
    )
