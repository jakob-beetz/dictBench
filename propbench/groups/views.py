from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PropertyGroup

@login_required
def group_list(request):
    """List all property groups."""
    groups = PropertyGroup.objects.all()
    return render(request, 'groups/group_list.html', {'groups': groups})

@login_required
def group_detail(request, pk):
    """Show group details."""
    group = get_object_or_404(PropertyGroup, pk=pk)
    return render(request, 'groups/group_detail.html', {'group': group})

@login_required
def group_create(request):
    """Create a new property group."""
    if request.method == 'POST':
        # Handle form submission here
        messages.success(request, 'Group created successfully')
        return redirect('groups:group_list')
    return render(request, 'groups/group_form.html', {'is_new': True})

@login_required
def group_edit(request, pk):
    """Edit an existing property group."""
    group = get_object_or_404(PropertyGroup, pk=pk)
    if request.method == 'POST':
        # Handle form submission here
        messages.success(request, 'Group updated successfully')
        return redirect('groups:group_detail', pk=group.pk)
    return render(request, 'groups/group_form.html', {'group': group, 'is_new': False})

@login_required
def group_delete(request, pk):
    """Delete a property group."""
    group = get_object_or_404(PropertyGroup, pk=pk)
    if request.method == 'POST':
        name = str(group)
        group.delete()
        messages.success(request, f'Group "{name}" deleted successfully')
        return redirect('groups:group_list')
    return render(request, 'groups/group_delete.html', {'group': group})
