from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from cases.models import Case
from data_management.models import UploadedFile, CallRecord, FinancialTransaction
from data_management.services.csv_processor import validate_and_preview_csv
from datetime import date, time


class CsvProcessorTest(SimpleTestCase):
    def test_financial_csv_preview_includes_columns_and_rows(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'financial.csv'
            csv_path.write_text(
                'sender_id,receiver_id,amount,transaction_date,transaction_type\n'
                'ACC001,ACC002,125.50,2024-01-15,transfer\n',
                encoding='utf-8',
            )

            result = validate_and_preview_csv(csv_path)

        self.assertTrue(result['valid'])
        self.assertEqual(
            result['columns'],
            ['sender_id', 'receiver_id', 'amount', 'transaction_date', 'transaction_type'],
        )
        self.assertEqual(
            result['preview_rows'],
            [['ACC001', 'ACC002', '125.5', '2024-01-15', 'transfer']],
        )


class CsvImportWorkflowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='csvimporter', password='password123')
        self.case = Case.objects.create(
            case_number='CSV-CASE-001',
            title='CSV Import Case',
            description='Case for imported dataset tests.',
            created_by=self.user,
        )
        self.client.login(username='csvimporter', password='password123')

    def create_uploaded_csv(self, filename, contents, file_type):
        return UploadedFile.objects.create(
            file=SimpleUploadedFile(filename, contents.encode('utf-8'), content_type='text/csv'),
            filename=filename,
            file_type=file_type,
            uploaded_by=self.user,
            status='pending_review',
        )

    def test_import_requires_a_case(self):
        contents = (
            'caller_number,receiver_number,call_date,call_time,duration\n'
            '9876543210,9123456780,2024-01-10,09:15:00,120\n'
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            uploaded_file = self.create_uploaded_csv('calls.csv', contents, 'csv_calls')
            response = self.client.post(
                reverse('data_management:confirm_import_csv', args=[uploaded_file.pk]),
                {'related_case': ''},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('data_management:preview_csv', args=[uploaded_file.pk]))
        self.assertEqual(CallRecord.objects.count(), 0)

    def test_call_csv_import_links_rows_to_selected_case(self):
        contents = (
            'caller_number,receiver_number,call_date,call_time,duration\n'
            '9876543210,9123456780,2024-01-10,09:15:00,120\n'
            ',9123456781,2024-01-10,09:30:00,60\n'
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            uploaded_file = self.create_uploaded_csv('calls.csv', contents, 'csv_calls')
            preview = self.client.get(reverse('data_management:preview_csv', args=[uploaded_file.pk]))
            self.assertContains(preview, self.case.case_number)

            response = self.client.post(
                reverse('data_management:confirm_import_csv', args=[uploaded_file.pk]),
                {'related_case': self.case.pk},
            )
            case_response = self.client.get(reverse('cases:case_detail', args=[self.case.pk]))

        self.assertRedirects(response, reverse('data_management:file_list'))
        record = CallRecord.objects.get()
        self.assertEqual(record.related_case, self.case)
        self.assertEqual(record.uploaded_file, uploaded_file)
        uploaded_file.refresh_from_db()
        self.assertIn('Skipped 1 invalid row(s)', uploaded_file.processing_summary)
        self.assertContains(case_response, record.caller_number)

    def test_financial_csv_import_links_rows_to_selected_case(self):
        contents = (
            'sender_id,receiver_id,amount,transaction_date,transaction_type\n'
            'ACC001,ACC002,125.50,2024-01-15,transfer\n'
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            uploaded_file = self.create_uploaded_csv('transactions.csv', contents, 'csv_financial')
            response = self.client.post(
                reverse('data_management:confirm_import_csv', args=[uploaded_file.pk]),
                {'related_case': self.case.pk},
            )
            case_response = self.client.get(reverse('cases:case_detail', args=[self.case.pk]))

        self.assertRedirects(response, reverse('data_management:file_list'))
        transaction = FinancialTransaction.objects.get()
        self.assertEqual(transaction.related_case, self.case)
        self.assertEqual(transaction.uploaded_file, uploaded_file)
        self.assertContains(case_response, transaction.sender_id)


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
