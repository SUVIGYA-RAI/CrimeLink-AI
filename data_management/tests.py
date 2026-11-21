from django.test import TestCase
from django.contrib.auth.models import User
from data_management.models import UploadedFile, CallRecord, FinancialTransaction
from datetime import date, time


class DataManagementModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testofficer', password='password123')

    def test_uploaded_file_creation(self):
        file_obj = UploadedFile.objects.create(
            filename='fir_sample.txt',
            file_type='txt',
            uploaded_by=self.user,
            status='completed',
            processing_summary='Extracted 500 chars'
        )
        self.assertEqual(file_obj.filename, 'fir_sample.txt')
        self.assertEqual(file_obj.status, 'completed')
        self.assertIn('fir_sample.txt', str(file_obj))

    def test_call_record_creation(self):
        call = CallRecord.objects.create(
            caller_number='9876543210',
            receiver_number='9123456780',
            call_date=date(2024, 1, 15),
            call_time=time(14, 30),
            duration=120
        )
        self.assertEqual(call.caller_number, '9876543210')
        self.assertEqual(call.duration, 120)

    def test_financial_transaction_creation(self):
        txn = FinancialTransaction.objects.create(
            sender_id='ACC001',
            receiver_id='ACC002',
            amount=50000.00,
            transaction_date=date(2024, 1, 15),
            transaction_type='transfer'
        )
        self.assertEqual(txn.sender_id, 'ACC001')
        self.assertEqual(float(txn.amount), 50000.00)

    def test_delete_file_and_associated_records(self):
        from ai_analysis.models import ExtractedEntity
        upload = UploadedFile.objects.create(
            filename='fir_to_delete.txt',
            file_type='txt',
            uploaded_by=self.user,
            status='completed'
        )
        ExtractedEntity.objects.create(
            uploaded_file=upload,
            entity_text='Vikram Malhotra',
            entity_type='PERSON',
            extraction_method='spacy'
        )
        CallRecord.objects.create(
            uploaded_file=upload,
            caller_number='9876543210',
            receiver_number='9123456780',
            call_date=date(2024, 1, 15),
            call_time=time(14, 30),
            duration=120
        )
        # Use test client to call delete_file
        self.client.login(username='testofficer', password='password123')
        response = self.client.get(f'/data_management/delete/{upload.pk}/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UploadedFile.objects.filter(pk=upload.pk).exists())
        self.assertFalse(ExtractedEntity.objects.filter(uploaded_file_id=upload.pk).exists())
        self.assertFalse(CallRecord.objects.filter(uploaded_file_id=upload.pk).exists())
