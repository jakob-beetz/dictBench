from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps
from django.conf import settings

def _create_audit_log(instance, action, data_before=None, data_after=None, reason=None, user=None):
    """Helper function to create audit logs for different actions."""
    # Check if audit signals are disabled
    if getattr(settings, 'DISABLE_AUDIT_SIGNALS', False):
        return
        
    # Get the Audit model only when needed
    try:
        Audit = apps.get_model('audit', 'Audit')
    except Exception:
        return  # Audit app not ready
    
    try:
        Audit.objects.create(
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            action=action,
            timestamp=timezone.now(),
            user=user,
            data_before=data_before,
            data_after=data_after,
            reason=reason
        )
    except Exception:
        # Silently fail to avoid breaking the application
        pass

# Signal handlers
@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Track changes before saving a model instance."""
    # Check if audit signals are disabled
    if getattr(settings, 'DISABLE_AUDIT_SIGNALS', False):
        return
        
    # Skip for Audit model itself to avoid recursion
    if sender.__name__ == 'Audit':
        return
    
    # Store original state for comparing after save
    if instance.pk:
        try:
            # Get the original instance from database
            original = sender.objects.get(pk=instance.pk)
            # Store the original data in the instance for later use
            instance._original_data = {
                field.name: getattr(original, field.name) 
                for field in original._meta.fields 
                if not field.primary_key
            }
        except Exception:
            # Instance doesn't exist yet or error occurred
            instance._original_data = {}
    else:
        # New instance
        instance._original_data = {}

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Create audit log after saving a model instance."""
    # Check if audit signals are disabled
    if getattr(settings, 'DISABLE_AUDIT_SIGNALS', False):
        return
        
    # Skip for Audit model itself to avoid recursion
    if sender.__name__ == 'Audit':
        return
    
    # Get current data
    current_data = {
        field.name: getattr(instance, field.name) 
        for field in instance._meta.fields 
        if not field.primary_key
    }
    
    # Get original data (from pre_save)
    original_data = getattr(instance, '_original_data', {})
    
    # Get the user who made the change
    user = getattr(instance, 'updated_by', None)
    
    _create_audit_log(
        instance=instance,
        action='create' if created else 'update',
        user=user,
        data_before=original_data,
        data_after=current_data
    )

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Create audit log after deleting a model instance."""
    # Check if audit signals are disabled
    if getattr(settings, 'DISABLE_AUDIT_SIGNALS', False):
        return
        
    # Skip for Audit model itself to avoid recursion
    if sender.__name__ == 'Audit':
        return
    
    # Get the data before deletion
    data_before = {
        field.name: getattr(instance, field.name) 
        for field in instance._meta.fields 
        if not field.primary_key
    }
    
    # Get the user who made the change
    user = getattr(instance, 'updated_by', None)
    
    _create_audit_log(
        instance=instance,
        action='delete',
        user=user,
        data_before=data_before,
        data_after={}
    )
