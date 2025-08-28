from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from properties.models import Property


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
