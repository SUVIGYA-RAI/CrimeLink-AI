"""
Cases app forms.
CaseForm for creating and editing investigation cases.
"""

from django import forms
from .models import Case


class CaseForm(forms.ModelForm):
    """ModelForm for creating and editing a Case."""

    class Meta:
        model = Case
        fields = ['case_number', 'title', 'description', 'case_type', 'location', 'status', 'priority']
        widgets = {
            'case_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CL-2024-001'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Case title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the case details...'
            }),
            'case_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Case location'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'case_number': 'Case Number',
            'case_type': 'Case Type',
        }

    def clean_case_number(self):
        """Ensure case number format is valid."""
        case_number = self.cleaned_data.get('case_number')
        if not case_number:
            raise forms.ValidationError("Case number is required.")
        return case_number.upper()  # Store case numbers in uppercase
