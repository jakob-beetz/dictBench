from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Property
from .forms import PropertyForm, PropertyNameFormSet, PropertyDefinitionFormSet, LANGUAGE_CHOICES

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
        form = PropertyForm(request.POST, user=request.user)
        name_formset = PropertyNameFormSet(request.POST, prefix='names')
        definition_formset = PropertyDefinitionFormSet(request.POST, prefix='definitions')
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            property_instance = form.save(commit=False)
            
            # Ensure user fields are set
            property_instance.created_by = request.user
            property_instance.updated_by = request.user
            property_instance.save()
            
            # Save formsets
            name_formset.instance = property_instance
            name_formset.save()
            
            definition_formset.instance = property_instance
            definition_formset.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            messages.success(request, 'Property created successfully!')
            return redirect('properties:property_detail', pk=property_instance.pk)
    else:
        form = PropertyForm(user=request.user)
        name_formset = PropertyNameFormSet(prefix='names')
        definition_formset = PropertyDefinitionFormSet(prefix='definitions')
    
    context = {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'is_new': True,
        'language_choices': LANGUAGE_CHOICES,
    }
    return render(request, 'properties/property_form.html', context)

@login_required
def property_edit(request, pk):
    """Edit an existing property."""
    prop = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=prop, user=request.user)
        name_formset = PropertyNameFormSet(request.POST, instance=prop)
        definition_formset = PropertyDefinitionFormSet(request.POST, instance=prop)
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            with transaction.atomic():
                property_instance = form.save()
                name_formset.save()
                definition_formset.save()
                
                # Get primary name for success message
                primary_name = property_instance.names.first()
                name_display = primary_name.name if primary_name else "Property"
                
                messages.success(request, f'Property "{name_display}" updated successfully')
                return redirect('properties:property_detail', pk=property_instance.guid)
    else:
        form = PropertyForm(instance=prop, user=request.user)
        name_formset = PropertyNameFormSet(instance=prop)
        definition_formset = PropertyDefinitionFormSet(instance=prop)
    
    return render(request, 'properties/property_form.html', {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'language_choices': LANGUAGE_CHOICES,
        'property': prop, 
        'is_new': False
    })

@login_required
def property_delete(request, pk):
    """Delete a property."""
    prop = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        name = prop.names.first().name if prop.names.exists() else str(prop)
        prop.delete()
        messages.success(request, f'Property "{name}" deleted successfully')
        return redirect('properties:property_list')
    
    return render(request, 'properties/property_delete.html', {'property': prop})
