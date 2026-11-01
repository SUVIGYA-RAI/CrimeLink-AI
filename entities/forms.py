"""
Entities app forms.
Forms for Person, Vehicle, Organization, Location, and PhoneRecord.
"""

from django import forms
from .models import Person, Vehicle, Organization, Location, PhoneRecord


class PersonForm(forms.ModelForm):
    """Form for adding/editing a Person."""

    class Meta:
        model = Person
        fields = ['full_name', 'age', 'gender', 'phone_number', 'address', 'description', 'related_cases']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Physical description, background...'}),
            'related_cases': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        }


class VehicleForm(forms.ModelForm):
    """Form for adding/editing a Vehicle."""

    class Meta:
        model = Vehicle
        fields = ['registration_number', 'vehicle_type', 'model_name', 'color', 'owner', 'related_case']
        widgets = {
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MH12AB1234'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vehicle model'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Color'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'related_case': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_registration_number(self):
        reg = self.cleaned_data.get('registration_number')
        return reg.upper() if reg else reg


class OrganizationForm(forms.ModelForm):
    """Form for adding/editing an Organization."""

    class Meta:
        model = Organization
        fields = ['name', 'organization_type', 'address', 'description', 'related_cases']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization name'}),
            'organization_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'related_cases': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        }


class LocationForm(forms.ModelForm):
    """Form for adding/editing a Location."""

    class Meta:
        model = Location
        fields = ['location_name', 'address', 'city', 'state', 'related_cases']
        widgets = {
            'location_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'related_cases': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        }


class PhoneRecordForm(forms.ModelForm):
    """Form for adding/editing a PhoneRecord."""

    class Meta:
        model = PhoneRecord
        fields = ['caller_number', 'receiver_number', 'call_date', 'call_time', 'duration', 'related_case']
        widgets = {
            'caller_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caller number'}),
            'receiver_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receiver number'}),
            'call_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'call_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in seconds'}),
            'related_case': forms.Select(attrs={'class': 'form-select'}),
        }
