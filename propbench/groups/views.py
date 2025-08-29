from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import PropertyGroup
from .forms import PropertyGroupForm, GroupNameFormSet, GroupDefinitionFormSet, LANGUAGE_CHOICES


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
    """Create a new property group with names and definitions."""
    if request.method == 'POST':
        form = PropertyGroupForm(request.POST, user=request.user)
        name_formset = GroupNameFormSet(request.POST, prefix='names')
        definition_formset = GroupDefinitionFormSet(request.POST, prefix='definitions')
        
        if form.is_valid() and name_formset.is_valid() and definition_formset.is_valid():
            group_instance = form.save(commit=False)
            
            # Ensure user fields are set
            group_instance.created_by = request.user
            group_instance.updated_by = request.user
            group_instance.save()
            
            # Save formsets
            name_formset.instance = group_instance
            name_formset.save()
            
            definition_formset.instance = group_instance
            definition_formset.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            messages.success(request, 'Property Group created successfully!')
            return redirect('groups:group_detail', pk=group_instance.pk)
    else:
        form = PropertyGroupForm(user=request.user)
        name_formset = GroupNameFormSet(prefix='names')
        definition_formset = GroupDefinitionFormSet(prefix='definitions')
    
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
