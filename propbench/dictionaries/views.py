from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PropertyDictionary
from .forms import PropertyDictionaryForm

@login_required
def dictionary_list(request):
    """Display list of dictionaries"""
    dictionaries = PropertyDictionary.objects.all()
    return render(request, 'dictionaries/dictionary_list.html', {'dictionaries': dictionaries})

@login_required
def dictionary_detail(request, dictionary_id):
    """Display dictionary details"""
    dictionary = get_object_or_404(PropertyDictionary, guid=dictionary_id)
    return render(request, 'dictionaries/dictionary_detail.html', {'dictionary': dictionary})

@login_required
def dictionary_create(request):
    """Create a new dictionary"""
    if request.method == 'POST':
        form = PropertyDictionaryForm(request.POST, user=request.user)
        if form.is_valid():
            dictionary = form.save(commit=False)
            dictionary.created_by = request.user
            dictionary.updated_by = request.user
            dictionary.save()
            messages.success(request, f"Dictionary '{dictionary.name}' created successfully")
            return redirect('dictionary_detail', dictionary_id=dictionary.guid)
    else:
        form = PropertyDictionaryForm(user=request.user)
    
    return render(request, 'dictionaries/dictionary_form.html', {'form': form, 'is_new': True})

@login_required
def dictionary_edit(request, dictionary_id):
    """Edit an existing dictionary"""
    dictionary = get_object_or_404(PropertyDictionary, guid=dictionary_id)
    
    if request.method == 'POST':
        form = PropertyDictionaryForm(request.POST, instance=dictionary, user=request.user)
        if form.is_valid():
            dictionary = form.save()
            messages.success(request, f"Dictionary '{dictionary.name}' updated successfully")
            return redirect('dictionary_detail', dictionary_id=dictionary.guid)
    else:
        form = PropertyDictionaryForm(instance=dictionary, user=request.user)
    
    return render(request, 'dictionaries/dictionary_form.html', 
                 {'form': form, 'dictionary': dictionary, 'is_new': False})

@login_required
def dictionary_delete(request, dictionary_id):
    """Delete a dictionary"""
    dictionary = get_object_or_404(PropertyDictionary, guid=dictionary_id)
    
    if request.method == 'POST':
        name = dictionary.name
        dictionary.delete()
        messages.success(request, f"Dictionary '{name}' deleted successfully")
        return redirect('dictionary_list')
    
    return render(request, 'dictionaries/dictionary_delete.html', {'dictionary': dictionary})
