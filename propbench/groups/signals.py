from django.db.models.signals import post_save, pre_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from groups.models import PropertyGroup, PropertyGroupMembership
from audit.models import Audit


@receiver(post_save, sender=PropertyGroup)
def audit_group_save(sender, instance, created, **kwargs):
    """
    Create audit log entries for group creation and updates.
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
        'type': instance.type,
        'dictionary_id': str(instance.dictionary.guid) if instance.dictionary else None,
        'parent_group_id': str(instance.parent_group.guid) if instance.parent_group else None,
        'extended_attributes': instance.extended_attributes,
        'metadata': instance.metadata
    }
    
    if created:
        # Creating a new group
        Audit.objects.create(
            entity_type='PropertyGroup',
            entity_id=str(instance.guid),
            action='create',
            user=user,
            data_after=data,
            reason=getattr(instance, '_change_reason', 'Initial creation')
        )
    else:
        # Updating existing group
        old_data = getattr(instance, '_data_before', {})
        
        # Create the audit entry
        Audit.objects.create(
            entity_type='PropertyGroup',
            entity_id=str(instance.guid),
            action='update',
            user=user,
            data_before=old_data,
            data_after=data,
            reason=getattr(instance, '_change_reason', 'Update')
        )


@receiver(pre_save, sender=PropertyGroup)
def track_group_changes(sender, instance, **kwargs):
    """
    Track changes to groups for audit logging.
    """
    # If the instance is new, there's nothing to compare
    if not instance.pk:
        return
    
    # Get the old instance from the database
    try:
        old_instance = PropertyGroup.objects.get(pk=instance.pk)
    except PropertyGroup.DoesNotExist:
        return
    
    # Store the old instance data for audit logging
    if hasattr(instance, '_change_user'):
        # Create a data snapshot for audit
        instance._data_before = {
            'guid': str(old_instance.guid),
            'name': old_instance.name,
            'description': old_instance.description,
            'type': old_instance.type,
            'dictionary_id': str(old_instance.dictionary.guid) if old_instance.dictionary else None,
            'parent_group_id': str(old_instance.parent_group.guid) if old_instance.parent_group else None,
            'extended_attributes': old_instance.extended_attributes,
            'metadata': old_instance.metadata
        }


@receiver(post_delete, sender=PropertyGroup)
def audit_group_delete(sender, instance, **kwargs):
    """
    Create audit log entries for group deletion.
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
        'type': instance.type,
        'dictionary_id': str(instance.dictionary.guid) if instance.dictionary else None,
        'parent_group_id': str(instance.parent_group.guid) if instance.parent_group else None,
        'extended_attributes': instance.extended_attributes,
        'metadata': instance.metadata
    }
    
    # Create the audit entry
    Audit.objects.create(
        entity_type='PropertyGroup',
        entity_id=str(instance.guid),
        action='delete',
        user=user,
        data_before=data,
        reason=getattr(instance, '_change_reason', 'Deletion')
    )


@receiver(post_save, sender=PropertyGroupMembership)
def audit_group_membership_change(sender, instance, created, **kwargs):
    """
    Audit when properties are added to or updated in groups.
    """
    if not hasattr(instance.group, '_change_user'):
        # Skip if no user information is available
        return
    
    user = instance.group._change_user
    
    data = {
        'group_id': str(instance.group.guid),
        'property_id': str(instance.property.guid),
        'order': instance.order,
        'is_required': instance.is_required,
        'metadata': instance.metadata
    }
    
    if created:
        # Property added to group
        Audit.objects.create(
            entity_type='PropertyGroupMembership',
            entity_id=f"{instance.group.guid}_{instance.property.guid}",
            action='relationship_add',
            user=user,
            data_after=data,
            reason=getattr(instance.group, '_change_reason', 'Added property to group')
        )
    else:
        # Property membership updated
        Audit.objects.create(
            entity_type='PropertyGroupMembership',
            entity_id=f"{instance.group.guid}_{instance.property.guid}",
            action='update',
            user=user,
            data_after=data,
            reason=getattr(instance.group, '_change_reason', 'Updated property in group')
        )


@receiver(post_delete, sender=PropertyGroupMembership)
def audit_group_membership_delete(sender, instance, **kwargs):
    """
    Audit when properties are removed from groups.
    """
    if not hasattr(instance.group, '_change_user'):
        # Skip if no user information is available
        return
    
    user = instance.group._change_user
    
    data = {
        'group_id': str(instance.group.guid),
        'property_id': str(instance.property.guid),
        'order': instance.order,
        'is_required': instance.is_required,
        'metadata': instance.metadata
    }
    
    # Property removed from group
    Audit.objects.create(
        entity_type='PropertyGroupMembership',
        entity_id=f"{instance.group.guid}_{instance.property.guid}",
        action='relationship_remove',
        user=user,
        data_before=data,
        reason=getattr(instance.group, '_change_reason', 'Removed property from group')
    )
