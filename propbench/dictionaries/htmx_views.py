from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_htmx.http import trigger_client_event

from .models import PropertyDictionary
from .forms import PropertyDictionaryForm
from audit.models import Audit


class DictionaryListView(LoginRequiredMixin, ListView):
    model = PropertyDictionary
    template_name = 'dictionaries/dictionary_list.html'
    context_object_name = 'dictionaries'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
            
        # Filter by status if provided
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class DictionaryDetailView(LoginRequiredMixin, DetailView):
    model = PropertyDictionary
    template_name = 'dictionaries/dictionary_detail.html'
    context_object_name = 'dictionary'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get audit logs for this dictionary
        dictionary = self.get_object()
        context['audit_logs'] = Audit.objects.filter(
            entity_type='PropertyDictionary',
            entity_id=str(dictionary.guid)
        ).order_by('-timestamp')[:10]
        
        # Get groups and properties in this dictionary
        context['groups'] = dictionary.groups.all()
        context['properties'] = dictionary.properties.all()
        
        return context


class DictionaryCreateView(LoginRequiredMixin, CreateView):
    model = PropertyDictionary
    form_class = PropertyDictionaryForm
    template_name = 'dictionaries/dictionary_form.html'
    success_url = reverse_lazy('dictionaries:dictionary_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Dictionary '{form.instance.name}' was created successfully.")
        
        if self.request.htmx:
            response = HttpResponse()
            trigger_client_event(response, 'showMessage', {
                'message': f"Dictionary '{form.instance.name}' was created successfully.",
                'level': 'success'
            })
            response['HX-Redirect'] = self.get_success_url()
        return response


class DictionaryUpdateView(LoginRequiredMixin, UpdateView):
    model = PropertyDictionary
    form_class = PropertyDictionaryForm
    template_name = 'dictionaries/dictionary_form.html'
    context_object_name = 'dictionary'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('dictionaries:dictionary_detail', kwargs={'pk': self.object.guid})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Dictionary '{form.instance.name}' was updated successfully.")
        
        if self.request.htmx:
            response = HttpResponse()
            trigger_client_event(response, 'showMessage', {
                'message': f"Dictionary '{form.instance.name}' was updated successfully.",
                'level': 'success'
            })
            response['HX-Redirect'] = self.get_success_url()
        return response


class DictionaryDeleteView(LoginRequiredMixin, DeleteView):
    model = PropertyDictionary
    template_name = 'dictionaries/dictionary_confirm_delete.html'
    success_url = reverse_lazy('dictionaries:dictionary_list')
    context_object_name = 'dictionary'
    
    def delete(self, request, *args, **kwargs):
        dictionary = self.get_object()
        messages.success(request, f"Dictionary '{dictionary.name}' was deleted successfully.")
        return super().delete(request, *args, **kwargs)


@require_http_methods(["POST"])
def set_default_dictionary(request, pk):
    """Set a dictionary as the default dictionary."""
    dictionary = get_object_or_404(PropertyDictionary, guid=pk)
    
    # Update all dictionaries to not be default
    PropertyDictionary.objects.update(is_default=False)
    
    # Set this dictionary as default
    dictionary.is_default = True
    dictionary.save()
    
    messages.success(request, f"'{dictionary.name}' is now the default dictionary.")
    
    if request.htmx:
        context = {'dictionaries': PropertyDictionary.objects.all()}
        return render(request, 'dictionaries/partials/dictionary_list_items.html', context)
    
    return redirect('dictionaries:dictionary_list')


@method_decorator(csrf_exempt, name='dispatch')
class DictionaryAuditView(LoginRequiredMixin, ListView):
    """View for displaying audit logs for a specific dictionary."""
    model = Audit
    template_name = 'dictionaries/dictionary_audit.html'
    context_object_name = 'audit_logs'
    paginate_by = 20
    
    def get_queryset(self):
        dictionary_id = self.kwargs.get('pk')
        return Audit.objects.filter(
            entity_type='PropertyDictionary',
            entity_id=dictionary_id
        ).order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dictionary_id = self.kwargs.get('pk')
        context['dictionary'] = get_object_or_404(PropertyDictionary, guid=dictionary_id)
        return context


@login_required
def dictionary_list(request):
    """Display list of property dictionaries."""
    dictionaries = PropertyDictionary.objects.all().order_by('-is_default', 'name')
    
    return render(request, 'dictionaries/htmx/dictionary_list.html', {
        'dictionaries': dictionaries,
    })


@login_required
def dictionary_create(request):
    """Create a new property dictionary."""
    if request.method == 'POST':
        form = PropertyDictionaryForm(request.POST, user=request.user)
        
        if form.is_valid():
            dictionary = form.save()
            messages.success(request, f"Dictionary '{dictionary.name}' created successfully.")
            
            if request.htmx:
                return redirect(reverse('dictionaries:dictionary_detail', kwargs={'pk': dictionary.guid}))