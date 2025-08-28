from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from properties.models import Property
from audit.models import Audit


@receiver(pre_save, sender=Property)
def track_property_changes(sender, instance, **kwargs):
    """
    Track changes to property lifecycle status.
    """
    # If the instance is new, there's nothing to compare
    if not instance.pk:
        return
    
    # Get the old instance from the database
    try:
        old_instance = Property.objects.get(pk=instance.pk)
    except Property.DoesNotExist:
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
    
    # Track version and revision changes
    if instance.version_number != old_instance.version_number:
        instance.date_of_version = timezone.now()
    
    if instance.revision_number != old_instance.revision_number:
        instance.date_of_revision = timezone.now()
    
    # Store the old instance data for audit logging
    if hasattr(instance, '_change_user'):
        # Create a data snapshot for audit
        instance._data_before = {
            'guid': str(old_instance.guid),
            'version_number': old_instance.version_number,
            'revision_number': old_instance.revision_number,
            'status': old_instance.status,
            'data_type': old_instance.data_type,
            'unit_of_measurement': old_instance.unit_of_measurement,
            'dictionary_id': str(old_instance.dictionary.guid) if old_instance.dictionary else None,
            'extended_attributes': old_instance.extended_attributes,
            'metadata': old_instance.metadata
        }


@receiver(post_save, sender=Property)
def audit_property_save(sender, instance, created, **kwargs):
    """
    Create audit log entries for property creation and updates.
    """
    if not hasattr(instance, '_change_user'):
        # Skip if no user information is available
        return
    
    user = instance._change_user
    
    # Prepare the serialized data for audit
    data = {
        'guid': str(instance.guid),
        'version_number': instance.version_number,
        'revision_number': instance.revision_number,
        'status': instance.status,
        'data_type': instance.data_type,
        'unit_of_measurement': instance.unit_of_measurement,
        'dictionary_id': str(instance.dictionary.guid) if instance.dictionary else None,
        'extended_attributes': instance.extended_attributes,
        'metadata': instance.metadata
    }
    
    # Try to get names for easier identification in audit logs
    try:
        names = list(instance.names.all().values('name', 'language'))
        if names:
            data['names'] = names
    except:
        pass
    
    if created:
        # Creating a new property
        Audit.objects.create(
            entity_type='Property',
            entity_id=str(instance.guid),
            action='create',
            user=user,
            data_after=data,
            reason=getattr(instance, '_change_reason', 'Initial creation')
        )
    else:
        # Updating existing property
        old_data = getattr(instance, '_data_before', {})
        
        # Determine the action based on status changes
        if 'status' in old_data and old_data['status'] != instance.status:
            if instance.status == 'active':
                action = 'activate'
            elif instance.status == 'deprecated':
                action = 'deprecate'
            elif instance.status == 'inactive':
                action = 'deactivate'
            elif instance.status == 'candidate':
                action = 'submit'
            else:
                action = 'status_change'
        else:
            action = 'update'
        
        # Create the audit entry
        Audit.objects.create(
            entity_type='Property',
            entity_id=str(instance.guid),
            action=action,
            user=user,
            data_before=old_data,
            data_after=data,
            reason=getattr(instance, '_change_reason', 'Update')
        )


@receiver(post_delete, sender=Property)
def audit_property_delete(sender, instance, **kwargs):
    """
    Create audit log entries for property deletion.
    """
    if not hasattr(instance, '_change_user'):
        # Skip if no user information is available
        return
    
    user = instance._change_user
    
    # Prepare the serialized data for audit
    data = {
        'guid': str(instance.guid),
        'version_number': instance.version_number,
        'revision_number': instance.revision_number,
        'status': instance.status,
        'data_type': instance.data_type,
        'unit_of_measurement': instance.unit_of_measurement,
        'dictionary_id': str(instance.dictionary.guid) if instance.dictionary else None,
        'extended_attributes': instance.extended_attributes,
        'metadata': instance.metadata
    }
    
    # Create the audit entry
    Audit.objects.create(
        entity_type='Property',
        entity_id=str(instance.guid),
        action='delete',
        user=user,
        data_before=data,
        reason=getattr(instance, '_change_reason', 'Deletion')
    )
