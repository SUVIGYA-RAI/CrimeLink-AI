"""
Integration tests for the Entities app.
Covers Person, Vehicle, Organization, Location, and PhoneRecord CRUD views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from cases.models import Case
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord
import datetime


def make_user(username, password='pass1234', role='investigator'):
    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.create(user=user, role=role)
    return user


def make_case(user):
    return Case.objects.create(
        case_number='CL-ENT-001',
        title='Entity Test Case',
        description='Used in entity tests.',
        case_type='fraud',
        status='open',
        priority='medium',
        created_by=user,
    )


# ---------------------------------------------------------------------------
# Person Tests
# ---------------------------------------------------------------------------

class PersonListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest1')
        self.client.login(username='enttest1', password='pass1234')
        self.person = Person.objects.create(full_name='Alice Bob', gender='female')

    def test_list_returns_200(self):
        r = self.client.get(reverse('entities:person_list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_person(self):
        r = self.client.get(reverse('entities:person_list'))
        self.assertContains(r, 'Alice Bob')

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('entities:person_list'))
        self.assertEqual(r.status_code, 302)

    def test_search_person(self):
        r = self.client.get(reverse('entities:person_list') + '?search=Alice')
        self.assertContains(r, 'Alice Bob')


class PersonCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest2')
        self.client.login(username='enttest2', password='pass1234')

    def test_create_page_loads(self):
        r = self.client.get(reverse('entities:person_create'))
        self.assertEqual(r.status_code, 200)

    def test_create_saves_person(self):
        self.client.post(reverse('entities:person_create'), {
            'full_name': 'Charlie Delta',
            'gender': 'male',
            'age': 30,
            'phone_number': '9000000001',
            'address': '1 Test St',
            'description': 'Test person',
            'related_cases': [],
        })
        self.assertTrue(Person.objects.filter(full_name='Charlie Delta').exists())


class PersonDetailDeleteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest3')
        self.client.login(username='enttest3', password='pass1234')
        self.person = Person.objects.create(full_name='Eve Falcon', gender='female')

    def test_detail_returns_200(self):
        r = self.client.get(reverse('entities:person_detail', args=[self.person.pk]))
        self.assertEqual(r.status_code, 200)

    def test_detail_404_for_invalid(self):
        r = self.client.get(reverse('entities:person_detail', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_delete_removes_person(self):
        pk = self.person.pk
        self.client.post(reverse('entities:person_delete', args=[pk]))
        self.assertFalse(Person.objects.filter(pk=pk).exists())


# ---------------------------------------------------------------------------
# Vehicle Tests
# ---------------------------------------------------------------------------

class VehicleViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest4')
        self.client.login(username='enttest4', password='pass1234')
        self.case = make_case(self.user)
        self.vehicle = Vehicle.objects.create(
            registration_number='XX01YY0001',
            vehicle_type='car',
            model_name='Maruti Swift',
            color='White',
            related_case=self.case,
        )

    def test_list_returns_200(self):
        r = self.client.get(reverse('entities:vehicle_list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_vehicle(self):
        r = self.client.get(reverse('entities:vehicle_list'))
        self.assertContains(r, 'XX01YY0001')

    def test_detail_returns_200(self):
        r = self.client.get(reverse('entities:vehicle_detail', args=[self.vehicle.pk]))
        self.assertEqual(r.status_code, 200)

    def test_create_page_loads(self):
        r = self.client.get(reverse('entities:vehicle_create'))
        self.assertEqual(r.status_code, 200)

    def test_create_saves_vehicle(self):
        self.client.post(reverse('entities:vehicle_create'), {
            'registration_number': 'NEW01AB0099',
            'vehicle_type': 'motorcycle',
            'model_name': 'Hero Splendor',
            'color': 'Red',
            'related_case': self.case.pk,
        })
        self.assertTrue(Vehicle.objects.filter(registration_number='NEW01AB0099').exists())


# ---------------------------------------------------------------------------
# Organization Tests
# ---------------------------------------------------------------------------

class OrganizationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest5')
        self.client.login(username='enttest5', password='pass1234')
        self.case = make_case(self.user)
        self.org = Organization.objects.create(
            name='Test Corp',
            organization_type='company',
            description='A test organization.',
        )

    def test_list_returns_200(self):
        r = self.client.get(reverse('entities:organization_list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_org(self):
        r = self.client.get(reverse('entities:organization_list'))
        self.assertContains(r, 'Test Corp')

    def test_create_page_loads(self):
        r = self.client.get(reverse('entities:organization_create'))
        self.assertEqual(r.status_code, 200)

    def test_detail_returns_200(self):
        r = self.client.get(reverse('entities:organization_detail', args=[self.org.pk]))
        self.assertEqual(r.status_code, 200)


# ---------------------------------------------------------------------------
# Location Tests
# ---------------------------------------------------------------------------

class LocationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest6')
        self.client.login(username='enttest6', password='pass1234')
        self.loc = Location.objects.create(
            location_name='Crime Scene Alpha',
            city='Mumbai',
            state='Maharashtra',
        )

    def test_list_returns_200(self):
        r = self.client.get(reverse('entities:location_list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_location(self):
        r = self.client.get(reverse('entities:location_list'))
        self.assertContains(r, 'Crime Scene Alpha')

    def test_create_page_loads(self):
        r = self.client.get(reverse('entities:location_create'))
        self.assertEqual(r.status_code, 200)

    def test_detail_returns_200(self):
        r = self.client.get(reverse('entities:location_detail', args=[self.loc.pk]))
        self.assertEqual(r.status_code, 200)


# ---------------------------------------------------------------------------
# PhoneRecord Tests
# ---------------------------------------------------------------------------

class PhoneRecordViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('enttest7')
        self.client.login(username='enttest7', password='pass1234')
        self.case = make_case(self.user)
        self.record = PhoneRecord.objects.create(
            caller_number='9000001111',
            receiver_number='9000002222',
            call_date=datetime.date(2024, 10, 1),
            call_time=datetime.time(10, 0),
            duration=120,
            related_case=self.case,
        )

    def test_list_returns_200(self):
        r = self.client.get(reverse('entities:phone_record_list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_record(self):
        r = self.client.get(reverse('entities:phone_record_list'))
        self.assertContains(r, '9000001111')

    def test_detail_returns_200(self):
        r = self.client.get(reverse('entities:phone_record_detail', args=[self.record.pk]))
        self.assertEqual(r.status_code, 200)

    def test_create_page_loads(self):
        r = self.client.get(reverse('entities:phone_record_create'))
        self.assertEqual(r.status_code, 200)

    def test_create_saves_record(self):
        self.client.post(reverse('entities:phone_record_create'), {
            'caller_number': '9111111111',
            'receiver_number': '9222222222',
            'call_date': '2024-11-01',
            'call_time': '09:00:00',
            'duration': 60,
            'related_case': self.case.pk,
        })
        self.assertTrue(PhoneRecord.objects.filter(caller_number='9111111111').exists())
