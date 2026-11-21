from django import forms
from .models import UploadedFile

class UploadedFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'file': 'Select file to upload',
        }

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        max_size_mb = 10
        if uploaded.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(f'File size must be under {max_size_mb} MB.')
        ext = uploaded.name.split('.')[-1].lower()
        allowed = ['pdf', 'txt', 'csv']
        if ext not in allowed:
            raise forms.ValidationError('Unsupported file extension.')
        return uploaded