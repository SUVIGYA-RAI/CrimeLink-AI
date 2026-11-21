"""
Case-Centric Workflows & Entity Architecture Test Suite
-------------------------------------------------------
Verifies:
- Workflow A: Manual case management & entity link/unlink
- Workflow B: Case-centric AI extraction & atomic approval
- Workflow C: Re-extraction & deduplication
- Workflow D: Missing case context & orphan prevention
- Workflow E: Regression tests across models, views, and network graph
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import UserProfile
from cases.models import Case
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord
from data_management.models import UploadedFile
from ai_analysis.models import ExtractedCase, ExtractedEntity, EntityRelationship
from ai_analysis.services.entity_extractor import extract_case_centric_data
from network_analysis.services.graph_builder import build_graph


class CaseCentricWorkflowsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='investigator_test', password='password123')
        UserProfile.objects.create(user=self.user, role='investigator')
        self.client.login(username='investigator_test', password='password123')

    # ─────────────────────────────────────────────────────────────────────────
    # WORKFLOW A: Manual Case Management & Direct Entity Link / Unlink
    # ─────────────────────────────────────────────────────────────────────────
    def test_workflow_a_manual_case_management(self):
        """
        1. Create a case.
        2. Add Person, Vehicle, Org, Loc, Phone directly with ?case_id.
        3. Verify all records are associated with the case.
        4. Edit case and manage associations.
        5. Unlink entities without deleting them.
        """
        # 1. Create a case
        resp = self.client.post(reverse('cases:case_create'), {
            'case_number': 'CL-WORKFLOW-01',
            'title': 'Armed Robbery at Jeweler',
            'description': 'Robbery investigation involving multiple suspects.',
            'case_type': 'theft',
            'location': 'Connaught Place, Delhi',
            'status': 'open',
            'priority': 'high',
        })
        self.assertEqual(resp.status_code, 302)
        case = Case.objects.get(case_number='CL-WORKFLOW-01')

        # 2. Add Person directly from case
        resp = self.client.post(f"{reverse('entities:person_create')}?case_id={case.pk}", {
            'full_name': 'Amit Verma',
            'phone_number': '9876543210',
            'gender': 'male',
            'description': 'Suspect seen on CCTV',
            'case_id': case.pk,
        })
        self.assertRedirects(resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        person = Person.objects.get(full_name='Amit Verma')
        self.assertIn(case, person.related_cases.all())

        # 3. Add Vehicle directly from case
        resp = self.client.post(f"{reverse('entities:vehicle_create')}?case_id={case.pk}", {
            'registration_number': 'DL04AB1234',
            'vehicle_type': 'car',
            'model_name': 'Honda City',
            'color': 'Silver',
            'case_id': case.pk,
        })
        self.assertRedirects(resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        vehicle = Vehicle.objects.get(registration_number='DL04AB1234')
        self.assertIn(case, vehicle.related_cases.all())

        # 4. Add Organization directly from case
        resp = self.client.post(f"{reverse('entities:organization_create')}?case_id={case.pk}", {
            'name': 'Apex Bullion Traders',
            'organization_type': 'company',
            'case_id': case.pk,
        })
        self.assertRedirects(resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        org = Organization.objects.get(name='Apex Bullion Traders')
        self.assertIn(case, org.related_cases.all())

        # 5. Add Location directly from case
        resp = self.client.post(f"{reverse('entities:location_create')}?case_id={case.pk}", {
            'location_name': 'Block B Market',
            'city': 'New Delhi',
            'state': 'Delhi',
            'case_id': case.pk,
        })
        self.assertRedirects(resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        loc = Location.objects.get(location_name='Block B Market')
        self.assertIn(case, loc.related_cases.all())

        # 6. Add Phone Record directly from case
        resp = self.client.post(f"{reverse('entities:phone_record_create')}?case_id={case.pk}", {
            'caller_number': '9876543210',
            'receiver_number': '9111222333',
            'call_date': '2026-11-20',
            'call_time': '14:30:00',
            'duration': 240,
            'case_id': case.pk,
        })
        self.assertRedirects(resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        record = PhoneRecord.objects.get(caller_number='9876543210', receiver_number='9111222333')
        self.assertEqual(record.related_case, case)

        # 7. Verify Case Detail page renders all associated entities
        detail_resp = self.client.get(reverse('cases:case_detail', kwargs={'pk': case.pk}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, 'Amit Verma')
        self.assertContains(detail_resp, 'DL04AB1234')
        self.assertContains(detail_resp, 'Apex Bullion Traders')
        self.assertContains(detail_resp, 'Block B Market')
        self.assertContains(detail_resp, '9876543210')

        # 8. Unlink Vehicle from case without deleting the vehicle entity
        unlink_resp = self.client.get(reverse('cases:case_unlink_entity', kwargs={
            'pk': case.pk,
            'entity_type': 'vehicle',
            'entity_id': vehicle.pk,
        }))
        self.assertRedirects(unlink_resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        self.assertNotIn(case, vehicle.related_cases.all())
        self.assertTrue(Vehicle.objects.filter(pk=vehicle.pk).exists(), "Vehicle entity must not be deleted upon unlink!")

        # 9. Link an existing vehicle back to the case
        link_resp = self.client.post(reverse('cases:case_link_entity', kwargs={'pk': case.pk}), {
            'entity_type': 'vehicle',
            'entity_id': vehicle.pk,
        })
        self.assertRedirects(link_resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        self.assertIn(case, vehicle.related_cases.all())

        # 10. Edit Case and verify association checkboxes
        edit_resp = self.client.post(reverse('cases:case_edit', kwargs={'pk': case.pk}), {
            'case_number': case.case_number,
            'title': 'Armed Robbery at Jeweler - Updated',
            'description': case.description,
            'case_type': case.case_type,
            'location': case.location,
            'status': 'under_investigation',
            'priority': 'high',
            'associated_persons': [person.pk],
            'associated_vehicles': [vehicle.pk],
            'associated_organizations': [],  # remove org via edit
            'associated_locations': [loc.pk],
        })
        self.assertRedirects(edit_resp, reverse('cases:case_detail', kwargs={'pk': case.pk}))
        case.refresh_from_db()
        self.assertEqual(case.title, 'Armed Robbery at Jeweler - Updated')
        self.assertIn(person, case.persons.all())
        self.assertIn(vehicle, case.vehicles.all())
        self.assertNotIn(org, case.organizations.all())
        self.assertTrue(Organization.objects.filter(pk=org.pk).exists(), "Organization entity must not be deleted!")

    # ─────────────────────────────────────────────────────────────────────────
    # WORKFLOW B: Case-Centric AI Extraction & Atomic Approval
    # ─────────────────────────────────────────────────────────────────────────
    def test_workflow_b_case_centric_ai_extraction(self):
        """
        1. Extract structured case and entities from document text.
        2. Verify case-level extraction payload.
        3. Review and approve the staged case.
        4. Verify permanent Case and entity DB records are created and linked.
        5. Verify Network Analysis graph reflects the relationships.
        """
        sample_fir_text = """
        FIRST INFORMATION REPORT
        FIR No: FIR-DEL-2024-889
        Place of Occurrence: Sector 62, Noida, Uttar Pradesh

        Complainant Vikram Malhotra reported an online cyber fraud incident.
        Accused suspect Rajesh Sharma, using mobile phone +919811223344, transferred illicit funds
        to an account connected with Matrix Financial Solutions.
        The suspect fled the scene in a black Toyota Fortuner bearing registration number DL10XY9999.
        Subsequent calls were traced from 9811223344 to 9822334455 regarding money laundering.
        """

        # 1. Run extraction service
        extracted_data = extract_case_centric_data(sample_fir_text, filename="FIR_Sample_889.txt")
        cases = extracted_data.get('cases', [])
        self.assertEqual(len(cases), 1)

        c0 = cases[0]
        self.assertEqual(c0['case_number'], 'FIR-DEL-2024-889')
        self.assertIn('cyber_crime', (c0['case_type'], c0['title'].lower()))
        self.assertTrue(any('Toyota Fortuner' in v['model_name'] or 'DL10XY9999' in v['registration_number'] for v in c0['vehicles']))

        # 2. Stage in ExtractedCase model
        uploaded_file = UploadedFile.objects.create(
            filename='FIR_Sample_889.txt',
            file_type='txt',
            uploaded_by=self.user,
            status='completed',
        )

        staged_case = ExtractedCase.objects.create(
            uploaded_file=uploaded_file,
            case_number=c0['case_number'],
            title=c0['title'],
            description=c0['description'],
            case_type='cyber_crime',
            incident_location='Sector 62, Noida',
            extracted_data=c0,
            review_status='pending',
        )

        # 3. Approve via review action view
        resp = self.client.post(reverse('ai_analysis:review_extracted_case_action', kwargs={
            'case_id': staged_case.pk,
            'action': 'approve',
        }), {
            'case_number': staged_case.case_number,
            'title': staged_case.title,
            'case_type': 'cyber_crime',
            'location': staged_case.incident_location,
            'description': staged_case.description,
        })

        self.assertEqual(resp.status_code, 302)
        permanent_case = Case.objects.get(case_number='FIR-DEL-2024-889')
        self.assertRedirects(resp, reverse('cases:case_detail', kwargs={'pk': permanent_case.pk}))

        # 4. Verify entities linked to the case
        staged_case.refresh_from_db()
        self.assertEqual(staged_case.review_status, 'approved')
        self.assertEqual(staged_case.committed_case, permanent_case)

        # Vehicle must exist and be linked to case
        vehicle = Vehicle.objects.filter(registration_number='DL10XY9999').first()
        self.assertIsNotNone(vehicle)
        self.assertIn(permanent_case, vehicle.related_cases.all())

        # Case must have persons
        self.assertTrue(permanent_case.persons.exists())

        # 5. Verify Network Analysis graph contains this case and edges
        graph = build_graph(include_pending=False)
        case_node_id = f"case:{permanent_case.pk}"
        self.assertIn(case_node_id, graph.nodes)
        self.assertTrue(graph.out_degree(case_node_id) > 0)

    # ─────────────────────────────────────────────────────────────────────────
    # WORKFLOW C: Re-extraction & Deduplication
    # ─────────────────────────────────────────────────────────────────────────
    def test_workflow_c_reextraction_and_deduplication(self):
        """
        Rerunning extraction on the same document must not create duplicate cases
        or duplicate entities.
        """
        uploaded_file = UploadedFile.objects.create(
            filename='FIR_Dup_Test.txt',
            file_type='txt',
            uploaded_by=self.user,
            status='completed',
        )

        case_data = {
            'case_number': 'CL-DUP-TEST-01',
            'title': 'Deduplication Verification Case',
            'description': 'Testing idempotency of extraction.',
            'case_type': 'fraud',
            'location': 'Mumbai',
            'persons': [{'full_name': 'Sanjay Gupta', 'phone_number': '9800011122', 'role': 'Suspect'}],
            'vehicles': [{'registration_number': 'MH01AB9999', 'model_name': 'Innova', 'vehicle_type': 'car', 'color': 'White'}],
            'organizations': [{'name': 'Gupta Trading Co', 'organization_type': 'company'}],
            'locations': [{'location_name': 'Nariman Point', 'city': 'Mumbai', 'state': 'Maharashtra'}],
            'phone_records': [],
            'relationships': [],
        }

        # 1. First staging & approval
        staged_1 = ExtractedCase.objects.create(
            uploaded_file=uploaded_file,
            case_number=case_data['case_number'],
            title=case_data['title'],
            extracted_data=case_data,
            review_status='pending',
        )

        self.client.post(reverse('ai_analysis:review_extracted_case_action', kwargs={
            'case_id': staged_1.pk,
            'action': 'approve',
        }), {
            'case_number': case_data['case_number'],
            'title': case_data['title'],
            'case_type': 'fraud',
            'location': 'Mumbai',
            'description': case_data['description'],
        })

        case_count_1 = Case.objects.filter(case_number='CL-DUP-TEST-01').count()
        person_count_1 = Person.objects.filter(full_name='Sanjay Gupta').count()
        vehicle_count_1 = Vehicle.objects.filter(registration_number='MH01AB9999').count()

        self.assertEqual(case_count_1, 1)
        self.assertEqual(person_count_1, 1)
        self.assertEqual(vehicle_count_1, 1)

        # 2. Second staging with same data & re-approval
        staged_2 = ExtractedCase.objects.create(
            uploaded_file=uploaded_file,
            case_number=case_data['case_number'],
            title=case_data['title'],
            extracted_data=case_data,
            review_status='pending',
        )

        self.client.post(reverse('ai_analysis:review_extracted_case_action', kwargs={
            'case_id': staged_2.pk,
            'action': 'approve',
        }), {
            'case_number': case_data['case_number'],
            'title': case_data['title'],
            'case_type': 'fraud',
            'location': 'Mumbai',
            'description': case_data['description'],
        })

        # Counts must NOT duplicate!
        case_count_2 = Case.objects.filter(case_number='CL-DUP-TEST-01').count()
        person_count_2 = Person.objects.filter(full_name='Sanjay Gupta').count()
        vehicle_count_2 = Vehicle.objects.filter(registration_number='MH01AB9999').count()

        self.assertEqual(case_count_2, 1, "Duplicate Case must not be created on re-extraction approval!")
        self.assertEqual(person_count_2, 1, "Duplicate Person must not be created on re-extraction approval!")
        self.assertEqual(vehicle_count_2, 1, "Duplicate Vehicle must not be created on re-extraction approval!")

    # ─────────────────────────────────────────────────────────────────────────
    # WORKFLOW D: Missing Case Context (Orphan Prevention)
    # ─────────────────────────────────────────────────────────────────────────
    def test_workflow_d_missing_case_context_no_orphan_entities(self):
        """
        If a document has extracted entities but is rejected or unapproved,
        no permanent entity records should be committed to Person, Vehicle, Org, Loc tables.
        """
        uploaded_file = UploadedFile.objects.create(
            filename='Ambiguous_Notes.txt',
            file_type='txt',
            uploaded_by=self.user,
            status='completed',
        )

        raw_data = {
            'case_number': '',
            'title': 'Ambiguous Note',
            'description': 'Brief note with suspicious mentions.',
            'case_type': 'other',
            'location': '',
            'persons': [{'full_name': 'Unknown Shady Contact', 'phone_number': '9999888877', 'role': 'Person of Interest'}],
            'vehicles': [{'registration_number': 'DL99ZZ0000', 'model_name': 'Unknown', 'vehicle_type': 'car', 'color': 'Black'}],
            'organizations': [{'name': 'Unverified Syndicate', 'organization_type': 'criminal_network'}],
            'locations': [],
            'phone_records': [],
            'relationships': [],
        }

        staged_case = ExtractedCase.objects.create(
            uploaded_file=uploaded_file,
            case_number='',
            title='Ambiguous Note',
            extracted_data=raw_data,
            review_status='pending',
        )

        # In pending state, nothing must exist in permanent tables
        self.assertFalse(Person.objects.filter(full_name='Unknown Shady Contact').exists())
        self.assertFalse(Vehicle.objects.filter(registration_number='DL99ZZ0000').exists())
        self.assertFalse(Organization.objects.filter(name='Unverified Syndicate').exists())

        # Reject the extraction
        reject_resp = self.client.get(reverse('ai_analysis:review_extracted_case_action', kwargs={
            'case_id': staged_case.pk,
            'action': 'reject',
        }))
        self.assertEqual(reject_resp.status_code, 302)

        staged_case.refresh_from_db()
        self.assertEqual(staged_case.review_status, 'rejected')

        # Still nothing must exist in permanent tables
        self.assertFalse(Person.objects.filter(full_name='Unknown Shady Contact').exists(), "Orphan Person must NOT be committed upon rejection!")
        self.assertFalse(Vehicle.objects.filter(registration_number='DL99ZZ0000').exists(), "Orphan Vehicle must NOT be committed upon rejection!")
        self.assertFalse(Organization.objects.filter(name='Unverified Syndicate').exists(), "Orphan Organization must NOT be committed upon rejection!")
