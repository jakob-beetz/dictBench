from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ChangeRequest

@login_required
def change_request_list(request):
    """List all change requests with filtering."""
    requests = ChangeRequest.objects.all().order_by('-submitted_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Filter by request type if provided
    type_filter = request.GET.get('type')
    if type_filter:
        requests = requests.filter(request_type=type_filter)
    
    return render(request, 'requests/change_request_list.html', {
        'requests': requests,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': ChangeRequest.STATUS_CHOICES,
        'type_choices': ChangeRequest.REQUEST_TYPE_CHOICES,
    })

@login_required
def change_request_detail(request, pk):
    """Display detailed view of a change request."""
    change_request = get_object_or_404(ChangeRequest, guid=pk)
    
    return render(request, 'requests/change_request_detail.html', {
        'change_request': change_request,
    })

@login_required
def change_request_create(request):
    """Create a new change request."""
    if request.method == 'POST':
        # Handle form submission here
        messages.success(request, 'Change request submitted successfully')
        return redirect('requests:change_request_list')
    
    return render(request, 'requests/change_request_form.html', {'is_new': True})

@login_required
def change_request_review(request, pk):
    """Review a change request."""
    change_request = get_object_or_404(ChangeRequest, guid=pk)
    
    if request.method == 'POST':
        # Handle review submission here
        decision = request.POST.get('decision')
        comments = request.POST.get('comments', '')
        
        if decision in ['APPROVED', 'REJECTED']:
            change_request.status = decision
            change_request.reviewed_by = request.user
            change_request.review_comments = comments
            change_request.save()
            
            messages.success(request, f'Change request {decision.lower()}')
            return redirect('requests:change_request_detail', pk=pk)
    
    return render(request, 'requests/change_request_review.html', {
        'change_request': change_request,
    })

@login_required
def change_request_implement(request, pk):
    """Implement an approved change request."""
    change_request = get_object_or_404(ChangeRequest, guid=pk)
    
    if change_request.status != 'APPROVED':
        messages.error(request, 'Only approved requests can be implemented')
        return redirect('requests:change_request_detail', pk=pk)
    
    if request.method == 'POST':
        # Handle implementation here
        change_request.status = 'IMPLEMENTED'
        change_request.implemented_by = request.user
        change_request.save()
        
        messages.success(request, 'Change request implemented successfully')
        return redirect('requests:change_request_detail', pk=pk)
    
    return render(request, 'requests/change_request_implement.html', {
        'change_request': change_request,
    })