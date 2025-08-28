from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Audit
from .serializers import AuditSerializer, AuditListSerializer


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for audit logs.
    
    This viewset provides read-only access to audit logs,
    with filtering and search capabilities.
    """
    queryset = Audit.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'action', 'user']
    search_fields = ['entity_id', 'reason']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return AuditListSerializer
        return AuditSerializer
    
    @action(detail=False, methods=['get'])
    def entity_history(self, request):
        """
        Get the audit history for a specific entity.
        """
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        
        if not entity_type or not entity_id:
            return Response({
                'error': 'Both entity_type and entity_id are required'
            }, status=400)
        
        audits = Audit.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by('-timestamp')
        
        page = self.paginate_queryset(audits)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(audits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """
        Get the audit history for a specific user.
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id is required'
            }, status=400)
        
        audits = Audit.objects.filter(user_id=user_id).order_by('-timestamp')
        
        page = self.paginate_queryset(audits)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(audits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """
        Get the most recent audit logs.
        """
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        audits = Audit.objects.all().order_by('-timestamp')[:limit]
        serializer = self.get_serializer(audits, many=True)
        return Response(serializer.data)

@login_required
def audit_list(request):
    """List all audit entries with filtering and pagination."""
    audits = Audit.objects.all().order_by('-timestamp')
    
    # Filter by entity type if provided
    entity_type_filter = request.GET.get('entity_type')
    if entity_type_filter:
        audits = audits.filter(entity_type=entity_type_filter)
    
    # Filter by action if provided
    action_filter = request.GET.get('action')
    if action_filter:
        audits = audits.filter(action=action_filter)
    
    # Filter by user if provided
    user_filter = request.GET.get('user')
    if user_filter:
        audits = audits.filter(user__username__icontains=user_filter)
    
    # Pagination
    paginator = Paginator(audits, 25)  # Show 25 audits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get distinct values for filters
    entity_types = Audit.objects.values_list('entity_type', flat=True).distinct()
    actions = Audit.objects.values_list('action', flat=True).distinct()
    
    return render(request, 'audit/audit_list.html', {
        'page_obj': page_obj,
        'entity_types': entity_types,
        'actions': actions,
        'entity_type_filter': entity_type_filter,
        'action_filter': action_filter,
        'user_filter': user_filter,
    })

@login_required
def audit_detail(request, pk):
    """Display detailed view of an audit entry."""
    audit = get_object_or_404(Audit, guid=pk)
    
    return render(request, 'audit/audit_detail.html', {
        'audit': audit,
    })

@login_required
def entity_audit_history(request, entity_type, entity_id):
    """Display audit history for a specific entity."""
    audits = Audit.objects.filter(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(audits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'audit/entity_audit_history.html', {
        'page_obj': page_obj,
        'entity_type': entity_type,
        'entity_id': entity_id,
    })
