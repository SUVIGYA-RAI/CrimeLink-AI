from django.db import models
from django.contrib.auth.models import User

class UploadedFile(models.Model):
    """Tracks files uploaded by investigators."""
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('txt', 'Text Document'),
        ('csv_calls', 'Call Detail Records CSV'),
        ('csv_financial', 'Financial Transactions CSV'),
    ]
    file = models.FileField(upload_to='uploads/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')  # pending, processing, completed, error
    processing_summary = models.TextField(blank=True)

    def __str__(self):
        return f"{self.filename} ({self.get_file_type_display()})"

class CallRecord(models.Model):
    """Synthetic call detail record imported from a CSV."""
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.SET_NULL, null=True, related_name='call_records')
    caller_number = models.CharField(max_length=15)
    receiver_number = models.CharField(max_length=15)
    call_date = models.DateField()
    call_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text='Duration in seconds')
    related_case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True, related_name='call_records')

    def __str__(self):
        return f"{self.caller_number} → {self.receiver_number} ({self.call_date})"

class FinancialTransaction(models.Model):
    """Synthetic financial transaction imported from a CSV."""
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.SET_NULL, null=True, related_name='financial_transactions')
    sender_id = models.CharField(max_length=50)
    receiver_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=30)
    related_case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True, related_name='financial_transactions')

    def __str__(self):
        return f"{self.sender_id} → {self.receiver_id} ({self.amount})"
