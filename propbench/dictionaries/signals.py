from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from dictionaries.models import PropertyDictionary
from audit.models import Audit


@receiver(pre_save, sender=PropertyDictionary)
def track_dictionary_changes(sender, instance, **kwargs):
    """
    Track changes to dictionary lifecycle status.
    """
    # If the instance is new, there's nothing to compare
    if not instance.pk:
        return
    
    # Get the old instance from the database
    try:
        old_instance = PropertyDictionary.objects.get(pk=instance.pk)
    except PropertyDictionary.DoesNotExist:
        return
    
    # Check for status changes and update date fields
    if old_instance.status != instance.status:
        # Status change detected
        now = timezone.now()
        
        if instance.status == 'active' and old_instance.status != 'active':
            instance.date_of_activation = now
        
        elif instance.status == 'deprecated' and old_instance.status != 'deprecated':
            instance.date_of_deprecation = now
        
        elif instance.status == 'inactive' and old_instance.status != 'inactive':
            instance.date_of_deactivation = now


@receiver(post_save, sender=PropertyDictionary)
def audit_dictionary_save(sender, instance, created, **kwargs):
    """
    Create audit log entries for dictionary creation and updates.
    """
    if not hasattr(instance, '_change_user'):
        # Skip if no user information is available
        return
    
    user = instance._change_user
    
    # Prepare the serialized data for audit
    data = {
        'guid': str(instance.guid),
        'name': instance.name,
        'description': instance.description,
        'registration_authority': instance.registration_authority,
        'version': instance.version,
        'status': instance.status,
        'is_default': instance.is_default,
        'extended_attributes': instance.extended_attributes,
        'metadata': instance.metadata
    }
    
    if created:
        # Creating a new dictionary
        Audit.objects.create(
            entity_type='PropertyDictionary',
            entity_id=str(instance.guid),
            action='create',
            user=user,
            data_after=data,
            reason=getattr(instance, '_change_reason', 'Initial creation')
        )
    else:
        # Updating existing dictionary
        old_data = getattr(instance, '_data_before', {})
        
        # Determine the action based on status changes
        if 'status' in old_data and old_data['status'] != instance.status:
            if instance.status == 'active':
                action = 'activate'
            elif instance.status == 'deprecated':
                action = 'deprecate'
            elif instance.status == 'inactive':
                action = 'deactivate'
            else:
                action = 'status_change'
        else:
            action = 'update'
        
        # Create the audit entry
        Audit.objects.create(
            entity_type='PropertyDictionary',
            entity_id=str(instance.guid),
            action=action,
            user=user,
            data_before=old_data,
            data_after=data,
            reason=getattr(instance, '_change_reason', 'Update')
        )


@receiver(post_delete, sender=PropertyDictionary)
def audit_dictionary_delete(sender, instance, **kwargs):
    """
    Create audit log entries for dictionary deletion.
    """
    if not hasattr(instance, '_change_user'):
        # Skip if no user information is available
        return
    
    user = instance._change_user
    
    # Prepare the serialized data for audit
    data = {
        'guid': str(instance.guid),
        'name': instance.name,
        'description': instance.description,
        'registration_authority': instance.registration_authority,
        'version': instance.version,
        'status': instance.status,
        'is_default': instance.is_default,
        'extended_attributes': instance.extended_attributes,
        'metadata': instance.metadata
    }
    
    # Create the audit entry
    Audit.objects.create(
        entity_type='PropertyDictionary',
        entity_id=str(instance.guid),
        action='delete',
        user=user,
        data_before=data,
        reason=getattr(instance, '_change_reason', 'Deletion')
    )
