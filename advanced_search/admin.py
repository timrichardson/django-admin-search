# -*- coding: utf-8 -*-
from django.contrib.admin import ModelAdmin
from django.db.models import Q
from django import forms
from django.utils import timezone


class BaseAdvacedSearchAdmin(ModelAdmin):
    change_list_template = 'admin/custom_change_list.html'
    advanced_search_fields = {}
    
    def lookup_allowed(self, lookup):
        if lookup in self.advanced_search_form().fields.keys():
            return True
        return super(BaseAdvacedSearchAdmin, self).lookup_allowed(lookup)
    
    def get_queryset(self, request):
        qs = super(BaseAdvacedSearchAdmin, self).get_queryset(request)
        return self.advanced_search(request, qs)

    def changelist_view(self, request, extra_context=None, **kwargs):
        advanced_search_form = self.advanced_search_form(request.GET)
        extra_context = {'asf':advanced_search_form}
        
        request.GET._mutable=True
        for key in advanced_search_form.fields.keys():
            try:
                temp = request.GET.pop(key)
            except KeyError:
                pass # there is no field of the form in the dict so we don't remove it
            else:
                if temp!=['']: #there is a field but it's empty so it's useless
                    self.advanced_search_fields[key] = temp 
        request.GET_mutable=False
        
        return super(BaseAdvacedSearchAdmin, self).changelist_view(request, extra_context=extra_context)

    def advanced_search(self, request, qs):
        qs = qs.filter(self.advanced_search_query(request, Q(), self.advanced_search_fields))
        
        # Clear CACHED Get values
        self.advanced_search_fields = {}

        return qs
    
    def advanced_search_form(self, request=None):
        return self.search_form(data=request)

    def advanced_search_query(self, request, query, get_values):
        for key, value in self.advanced_search_form().fields.items():
            key_value = get_values[key][0] if key in get_values else None

            if hasattr(self, ('search_' + key)):
                query &= getattr(self, 'search_' + key)(request, key_value, get_values)
                continue

            if key_value is None:
                continue

            if isinstance(value, forms.CharField) or isinstance(value, forms.TextInput):
                field_query = key + '__icontains'
                query &= Q(**{field_query: key_value})

            if isinstance(value, forms.BooleanField) or isinstance(value, forms.ChoiceField) or isinstance(value, forms.ModelChoiceField):
                field_query = key
                query &= Q(**{field_query: key_value})

            if isinstance(value, forms.DateField):
                field_query = key + value.widget.attrs['data_filter']
                key_value = timezone.datetime.strptime(key_value, "%d/%m/%Y")
                query &= Q(**{field_query: key_value})

            if isinstance(value, forms.DateTimeField):
                field_query = key + value.widget.attrs['data_filter']
                key_value = timezone.datetime.strptime(key_value, "%d/%m/%Y %H:%M:%S")
                query &= Q(**{field_query: key_value})
        
        return query