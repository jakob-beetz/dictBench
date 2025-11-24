from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import PropertyGroup, PropertyGroupMembership, GroupName, GroupDefinition
from properties.models import Property
from .forms import PropertyGroupForm, GroupNameFormSet, GroupDefinitionFormSet, LANGUAGE_CHOICES, GroupAddPropertiesForm


@login_required
def group_list(request):
    """List all property groups."""
    groups = PropertyGroup.objects.all()
    
    # Add inherited properties count for each group
    groups_with_counts = []
    for group in groups:
        inherited_count = 0
        if group.parent_group:
            parent = group.parent_group
            while parent:
                inherited_count += PropertyGroupMembership.objects.filter(group=parent).count()
                parent = parent.parent_group
        
        groups_with_counts.append({
            'group': group,
            'direct_count': PropertyGroupMembership.objects.filter(group=group).count(),
            'inherited_count': inherited_count
        })
    
    return render(request, 'groups/group_list.html', {'groups_with_counts': groups_with_counts})

@login_required
def group_detail(request, pk):
    group = get_object_or_404(PropertyGroup, pk=pk)
    
    # Get memberships with related property data to avoid N+1 queries
    memberships = PropertyGroupMembership.objects.filter(
        group=group
    ).select_related('property').prefetch_related('property__names').order_by('order', 'property__pa_code')
    
    # Get parent hierarchy (all ancestors)
    parent_hierarchy = []
    if group.parent_group:
        parent = group.parent_group
        while parent:
            parent_hierarchy.append(parent)
            parent = parent.parent_group
    
    # Get inherited properties from parent groups with ordering
    inherited_properties = []
    inherited_order_start = 0
    if group.parent_group:
        parent = group.parent_group
        while parent:
            parent_memberships = PropertyGroupMembership.objects.filter(
                group=parent
            ).select_related('property').prefetch_related('property__names').order_by('order', 'property__pa_code')
            
            for membership in parent_memberships:
                inherited_properties.append({
                    'membership': membership,
                    'parent_group': parent,
                    'display_order': inherited_order_start + (membership.order or 0)
                })
            
            inherited_order_start += parent_memberships.count()
            parent = parent.parent_group  # Traverse up the hierarchy
    
    # Calculate display order for direct properties (start after inherited)
    direct_properties = []
    direct_order_start = len(inherited_properties)
    for membership in memberships:
        direct_properties.append({
            'membership': membership,
            'display_order': direct_order_start + (membership.order or 0)
        })
    
    return render(request, 'groups/group_detail.html', {
        'group': group,
        'memberships': memberships,
        'inherited_properties': inherited_properties,
        'parent_hierarchy': parent_hierarchy,
        'direct_properties': direct_properties,
    })

@login_required
def group_toggle_required(request, pk, property_pk):
    """Toggle the required status of a property in a group"""
    if request.method == "POST":
        group = get_object_or_404(PropertyGroup, pk=pk)
        property_obj = get_object_or_404(Property, pk=property_pk)
        
        membership = PropertyGroupMembership.objects.filter(
            group=group,
            property=property_obj
        ).first()
        
        if membership:
            membership.is_required = not membership.is_required
            membership.save()
            status = "required" if membership.is_required else "optional"
            messages.success(request, f'Property {property_obj.pa_code} is now {status}')
        else:
            messages.error(request, 'Property membership not found')
    
    return redirect('groups:group_detail', pk=pk)

@login_required
def group_create(request):
    """Create a new property group with names and definitions."""
    if request.method == 'POST':
        form = PropertyGroupForm(request.POST, user=request.user)
        name_formset = GroupNameFormSet(request.POST, prefix='names')
        definition_formset = GroupDefinitionFormSet(request.POST, prefix='definitions')
        
        # Debug print
        print("Name formset errors:", name_formset.errors)
        print("Name non_form_errors:", name_formset.non_form_errors())
        print("Definition formset errors:", definition_formset.errors)
        print("Definition non_form_errors:", definition_formset.non_form_errors())
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            group_instance = form.save(commit=False)
            group_instance.created_by = request.user
            group_instance.updated_by = request.user
            group_instance.save()
            
            name_formset.instance = group_instance
            name_formset.save()
            
            definition_formset.instance = group_instance
            definition_formset.save()
            
            form.save_m2m()
            
            messages.success(request, 'Property Group created successfully!')
            return redirect('groups:group_detail', pk=group_instance.pk)
        else:
            # Show validation errors
            if not form.is_valid():
                messages.error(request, f'Form errors: {form.errors}')
            if not name_formset.is_valid():
                messages.error(request, f'Name formset errors: {name_formset.errors}')
            if not definition_formset.is_valid():
                messages.error(request, f'Definition formset errors: {definition_formset.errors}')
    else:
        form = PropertyGroupForm(user=request.user)
        name_formset = GroupNameFormSet(prefix='names', queryset=GroupName.objects.none())
        definition_formset = GroupDefinitionFormSet(prefix='definitions', queryset=GroupDefinition.objects.none())
    
    context = {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'is_new': True,
        'language_choices': LANGUAGE_CHOICES,
    }
    return render(request, 'groups/group_form.html', context)


@login_required 
def group_edit(request, pk):
    """Edit an existing property group."""
    group = get_object_or_404(PropertyGroup, pk=pk)
    
    if request.method == 'POST':
        form = PropertyGroupForm(request.POST, instance=group, user=request.user)
        name_formset = GroupNameFormSet(request.POST, instance=group, prefix='names')
        definition_formset = GroupDefinitionFormSet(request.POST, instance=group, prefix='definitions')
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            group_instance = form.save(commit=False)
            group_instance.updated_by = request.user
            group_instance.save()
            
            name_formset.save()
            definition_formset.save()
            form.save_m2m()
            
            messages.success(request, 'Property Group updated successfully!')
            return redirect('groups:group_detail', pk=group_instance.pk)
    else:
        form = PropertyGroupForm(instance=group, user=request.user)
        name_formset = GroupNameFormSet(instance=group, prefix='names')
        definition_formset = GroupDefinitionFormSet(instance=group, prefix='definitions')
    
    context = {
        'form': form,
        'name_formset': name_formset,
        'definition_formset': definition_formset,
        'group': group,
        'is_new': False,
        'language_choices': LANGUAGE_CHOICES,
    }
    return render(request, 'groups/group_form.html', context)

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

@login_required
def group_add_properties(request, pk):
    group = get_object_or_404(PropertyGroup, pk=pk)
    
    # Get direct properties
    direct_properties = PropertyGroupMembership.objects.filter(
        group=group
    ).select_related('property').prefetch_related('property__names').order_by('order', 'property__pa_code')
    
    # Get inherited properties from parent groups
    inherited_properties = []
    if group.parent_group:
        parent = group.parent_group
        while parent:
            parent_memberships = PropertyGroupMembership.objects.filter(
                group=parent
            ).select_related('property').prefetch_related('property__names').order_by('order', 'property__pa_code')
            
            for membership in parent_memberships:
                inherited_properties.append({
                    'membership': membership,
                    'parent_group': parent
                })
            
            parent = parent.parent_group
    
    if request.method == "POST":
        form = GroupAddPropertiesForm(request.POST, group=group)
        if form.is_valid():
            props = form.cleaned_data['properties']
            
            # Get the max current order to append new properties at the end
            try:
                max_order = PropertyGroupMembership.objects.filter(
                    group=group
                ).aggregate(models.Max('order'))['order__max'] or 0
            except:
                max_order = 0
            
            # Create membership rows
            added_count = 0
            for idx, prop in enumerate(props, start=1):
                membership, created = PropertyGroupMembership.objects.get_or_create(
                    group=group,
                    property=prop,
                    defaults={
                        'is_required': False,
                        'order': max_order + idx
                    }
                )
                if created:
                    added_count += 1
            
            if added_count > 0:
                messages.success(request, f'Added {added_count} properties to {group.name}')
            else:
                messages.info(request, 'No new properties were added (they may already be in the group)')
            
            return redirect('groups:group_detail', pk=group.pk)
    else:
        form = GroupAddPropertiesForm(group=group)
    
    return render(request, 'groups/group_add_properties.html', {
        'group': group,
        'form': form,
        'direct_properties': direct_properties,
        'inherited_properties': inherited_properties,
    })

@login_required
def group_remove_property(request, pk, property_pk):
    """Remove a property from a group"""
    group = get_object_or_404(PropertyGroup, pk=pk)
    property_obj = get_object_or_404(Property, pk=property_pk)
    
    if request.method == "POST":
        membership = PropertyGroupMembership.objects.filter(
            group=group,
            property=property_obj
        ).first()
        
        if membership:
            membership.delete()
            messages.success(request, f'Removed {property_obj.pa_code} from {group.name}')
        else:
            messages.warning(request, 'Property was not in this group')
    
    return redirect('groups:group_detail', pk=group.pk)
