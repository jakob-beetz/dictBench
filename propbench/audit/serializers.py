from rest_framework import serializers
from .models import Audit


class AuditSerializer(serializers.ModelSerializer):
    """
    Serializer for Audit model.
    """
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Audit
        fields = [
            'id', 'entity_type', 'entity_id', 'action', 'timestamp',
            'user', 'user_username', 'data_before', 'data_after',
            'reason', 'extended_attributes', 'metadata'
        ]
        read_only_fields = ['id', 'user', 'user_username', 'timestamp']


class AuditListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for Audit model used in list views.
    """
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Audit
        fields = [
            'id', 'entity_type', 'entity_id', 'action', 'timestamp',
            'user_username', 'reason'
        ]


class RollbackSerializer(serializers.Serializer):
    """
    Serializer for rollback operations.
    """
    audit_id = serializers.UUIDField(
        help_text="ID of the audit entry to rollback to."
    )
    reason = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="Reason for the rollback."
    )
