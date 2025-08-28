from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Property

@login_required
def property_list(request):
    """List all properties."""
    properties = Property.objects.all()
    return render(request, 'properties/property_list.html', {'properties': properties})

@login_required
def property_detail(request, pk):
    """Show property details."""
    prop = get_object_or_404(Property, pk=pk)
    return render(request, 'properties/property_detail.html', {'property': prop})

@login_required
def property_create(request):
    """Create a new property."""
    if request.method == 'POST':
        # Handle form submission here
        messages.success(request, 'Property created successfully')
        return redirect('properties:property_list')
    return render(request, 'properties/property_form.html', {'is_new': True})

@login_required
def property_edit(request, pk):
    """Edit an existing property."""
    prop = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        # Handle form submission here
        messages.success(request, 'Property updated successfully')
        return redirect('properties:property_detail', pk=prop.pk)
    return render(request, 'properties/property_form.html', {'property': prop, 'is_new': False})

@login_required
def property_delete(request, pk):
    """Delete a property."""
    prop = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        name = str(prop)
        prop.delete()
        messages.success(request, f'Property "{name}" deleted successfully')
        return redirect('properties:property_list')
    return render(request, 'properties/property_delete.html', {'property': prop})
