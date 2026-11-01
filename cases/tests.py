"""
Integration tests for the Cases app.
Covers list, detail, create, edit, delete views and search/filter.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from cases.models import Case


def make_user(username, password='pass1234', role='investigator'):
    """Helper: create a user with an attached UserProfile."""
    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.create(user=user, role=role)
    return user


def make_case(user, case_number='CL-T-001', title='Test Case', **kwargs):
    """Helper: create a Case record."""
    defaults = dict(
        case_number=case_number,
        title=title,
        description='A test investigation case.',
        case_type='fraud',
        location='Test City',
        status='open',
        priority='medium',
        created_by=user,
    )
    defaults.update(kwargs)
    return Case.objects.create(**defaults)


class CaseListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('casetest1')
        self.client.login(username='casetest1', password='pass1234')
        self.case = make_case(self.user)

    def test_list_returns_200(self):
        r = self.client.get(reverse('cases:case_list'))
        self.assertEqual(r.status_code, 200)

    def test_list_shows_case(self):
        r = self.client.get(reverse('cases:case_list'))
        self.assertContains(r, self.case.case_number)

    def test_search_finds_case(self):
        r = self.client.get(reverse('cases:case_list') + '?search=Test+Case')
        self.assertContains(r, self.case.case_number)

    def test_search_no_match_returns_empty(self):
        r = self.client.get(reverse('cases:case_list') + '?search=XYZ_NO_MATCH')
        self.assertNotContains(r, self.case.case_number)

    def test_filter_by_status(self):
        r = self.client.get(reverse('cases:case_list') + '?status=open')
        self.assertContains(r, self.case.case_number)

    def test_filter_by_priority(self):
        r = self.client.get(reverse('cases:case_list') + '?priority=medium')
        self.assertContains(r, self.case.case_number)

    def test_list_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('cases:case_list'))
        self.assertEqual(r.status_code, 302)


class CaseDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('casetest2')
        self.client.login(username='casetest2', password='pass1234')
        self.case = make_case(self.user, case_number='CL-T-002')

    def test_detail_returns_200(self):
        r = self.client.get(reverse('cases:case_detail', args=[self.case.pk]))
        self.assertEqual(r.status_code, 200)

    def test_detail_shows_title(self):
        r = self.client.get(reverse('cases:case_detail', args=[self.case.pk]))
        self.assertContains(r, self.case.title)

    def test_detail_404_for_invalid_pk(self):
        r = self.client.get(reverse('cases:case_detail', args=[99999]))
        self.assertEqual(r.status_code, 404)


class CaseCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('casetest3')
        self.client.login(username='casetest3', password='pass1234')

    def test_create_page_loads(self):
        r = self.client.get(reverse('cases:case_create'))
        self.assertEqual(r.status_code, 200)

    def test_create_saves_case(self):
        self.client.post(reverse('cases:case_create'), {
            'case_number': 'CL-NEW-001',
            'title': 'Newly Created Case',
            'description': 'Created in test.',
            'case_type': 'theft',
            'location': 'New Town',
            'status': 'open',
            'priority': 'low',
        })
        self.assertTrue(Case.objects.filter(case_number='CL-NEW-001').exists())

    def test_create_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse('cases:case_create'))
        self.assertEqual(r.status_code, 302)

    def test_create_duplicate_case_number_fails(self):
        make_case(self.user, case_number='CL-DUP-001')
        r = self.client.post(reverse('cases:case_create'), {
            'case_number': 'CL-DUP-001',
            'title': 'Duplicate',
            'description': 'Should fail.',
            'case_type': 'fraud',
            'location': 'Anywhere',
            'status': 'open',
            'priority': 'low',
        })
        # Form should be re-displayed (200), not redirect
        self.assertEqual(r.status_code, 200)


class CaseEditDeleteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('casetest4')
        self.client.login(username='casetest4', password='pass1234')
        self.case = make_case(self.user, case_number='CL-T-003')

    def test_edit_page_loads(self):
        r = self.client.get(reverse('cases:case_edit', args=[self.case.pk]))
        self.assertEqual(r.status_code, 200)

    def test_edit_updates_case(self):
        self.client.post(reverse('cases:case_edit', args=[self.case.pk]), {
            'case_number': self.case.case_number,
            'title': 'Updated Title',
            'description': self.case.description,
            'case_type': self.case.case_type,
            'location': self.case.location,
            'status': 'closed',
            'priority': self.case.priority,
        })
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, 'closed')
        self.assertEqual(self.case.title, 'Updated Title')

    def test_delete_page_loads(self):
        r = self.client.get(reverse('cases:case_delete', args=[self.case.pk]))
        self.assertEqual(r.status_code, 200)

    def test_delete_removes_case(self):
        pk = self.case.pk
        self.client.post(reverse('cases:case_delete', args=[pk]))
        self.assertFalse(Case.objects.filter(pk=pk).exists())
