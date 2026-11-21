from django.test import TestCase
from django.contrib.auth.models import User
from data_management.models import UploadedFile, CallRecord, FinancialTransaction
from ai_analysis.models import ExtractedEntity, EntityRelationship, AnalysisAlert
from ai_analysis.services.entity_extractor import extract_entities
from ai_analysis.services.anomaly_detector import detect_call_anomalies, detect_transaction_anomalies
from datetime import date, time


class AIAnalysisServicesTest(TestCase):
    def test_entity_extractor_regex(self):
        text = "Suspect Ramesh Kumar called 9876543210 and fled in vehicle MH 12 AB 3456. Later Ramesh Kumar was seen again with 9876543210."
        entities = extract_entities(text)
        types = [e['type'] for e in entities]
        texts = [e['text'] for e in entities]
        self.assertIn('PHONE_NUMBER', types)
        self.assertIn('9876543210', texts)
        self.assertIn('VEHICLE_NUMBER', types)
        self.assertIn('MH 12 AB 3456', texts)
        # Verify deduplication: repeated mentions appear only once
        phone_count = [e for e in entities if e['text'] == '9876543210']
        self.assertEqual(len(phone_count), 1)
        name_count = [e for e in entities if 'kumar' in e['text'].lower()]
        self.assertEqual(len(name_count), 1)

    def test_extracted_entity_model(self):
        user = User.objects.create_user(username='officer1', password='password123')
        upload = UploadedFile.objects.create(
            filename='report.txt',
            file_type='txt',
            uploaded_by=user
        )
        entity = ExtractedEntity.objects.create(
            uploaded_file=upload,
            entity_text='Vikram Malhotra',
            entity_type='PERSON',
            extraction_method='spacy',
            confidence=0.95
        )
        self.assertEqual(entity.review_status, 'pending')
        self.assertEqual(str(entity), 'Vikram Malhotra (PERSON) – pending')

    def test_call_anomaly_detection(self):
        # Create 7 calls between same pair to trigger threshold (>5)
        for i in range(7):
            CallRecord.objects.create(
                caller_number='9998887770',
                receiver_number='9991112220',
                call_date=date(2024, 1, 10),
                call_time=time(10, i),
                duration=60
            )
        alerts = detect_call_anomalies()
        self.assertGreaterEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, 'Unusual Call Frequency')

    def test_transaction_anomaly_detection(self):
        # Normal small transactions
        for i in range(5):
            FinancialTransaction.objects.create(
                sender_id=f'USER{i}',
                receiver_id='MERCHANT',
                amount=100.00,
                transaction_date=date(2024, 1, 10),
                transaction_type='payment'
            )
        # Giant transaction: 50000 compared to ~100 mean
        FinancialTransaction.objects.create(
            sender_id='USER_SPIKE',
            receiver_id='MERCHANT',
            amount=50000.00,
            transaction_date=date(2024, 1, 11),
            transaction_type='transfer'
        )
        alerts = detect_transaction_anomalies()
        self.assertTrue(any(a.alert_type == 'Unusually Large Transaction' for a in alerts))

    def test_approve_entity_syncs_to_persons(self):
        from entities.models import Person
        user = User.objects.create_user(username='officer_sync', password='password123')
        upload = UploadedFile.objects.create(
            filename='fir_sync.txt',
            file_type='txt',
            uploaded_by=user
        )
        entity = ExtractedEntity.objects.create(
            uploaded_file=upload,
            entity_text='Devendra Rawat',
            entity_type='PERSON',
            extraction_method='spacy',
            review_status='pending'
        )
        self.client.login(username='officer_sync', password='password123')
        response = self.client.get(f'/ai_analysis/entities/review/{entity.pk}/approve/', follow=True)
        self.assertEqual(response.status_code, 200)
        entity.refresh_from_db()
        self.assertEqual(entity.review_status, 'approved')
        # Check that Person was actually created in entities database
        self.assertTrue(Person.objects.filter(full_name='Devendra Rawat').exists())
