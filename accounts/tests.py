"""
Basic tests for CrimeLink AI - accounts app.
Tests authentication, registration, and access controls.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from cases.models import Case


class AccountsTest(TestCase):
    """Tests for user authentication and accounts."""

    def setUp(self):
        """Set up test data before each test."""
        self.client = Client()
        # Create a test investigator
        self.user = User.objects.create_user(
            username='testinv',
            password='testpass123',
            first_name='Test',
            last_name='Investigator'
        )
        UserProfile.objects.create(user=self.user, role='investigator')

        # Create admin user
        self.admin = User.objects.create_user(
            username='testadmin',
            password='adminpass123',
        )
        UserProfile.objects.create(user=self.admin, role='admin')

    def test_login_page_loads(self):
        """Test that the login page loads correctly."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CrimeLink AI')

    def test_valid_login(self):
        """Test that a user can log in with valid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testinv',
            'password': 'testpass123'
        })
        # Should redirect to dashboard after login
        self.assertRedirects(response, reverse('dashboard:home'))

    def test_invalid_login(self):
        """Test that invalid credentials do not log in."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testinv',
            'password': 'wrongpassword'
        })
        # Should stay on login page
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        """Test that unauthenticated users can't access the dashboard."""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_register_page_loads(self):
        """Test that registration page loads."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_new_user(self):
        """Test that a new user can be registered."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password1': 'Str0ng@Pass1',
            'password2': 'Str0ng@Pass1',
            'role': 'investigator',
            'phone_number': '',
            'badge_number': '',
            'department': '',
        })
        # Should redirect to login after registration
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_logout(self):
        """Test that logout works correctly."""
        self.client.login(username='testinv', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))


class DashboardTest(TestCase):
    """Tests for the dashboard."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='inv2', password='pass123')
        UserProfile.objects.create(user=self.user, role='investigator')
        self.client.login(username='inv2', password='pass123')

    def test_dashboard_loads(self):
        """Test that the dashboard loads and shows statistics."""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Cases')

    def test_dashboard_stats_correct(self):
        """Test that dashboard statistics reflect actual database values."""
        # Create a case
        Case.objects.create(
            case_number='TEST-001',
            title='Test Case',
            description='Test description',
            created_by=self.user
        )
        response = self.client.get(reverse('dashboard:home'))
        self.assertContains(response, '1')  # Should show 1 case


class CasesTest(TestCase):
    """Tests for case management CRUD."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='inv3', password='pass123')
        UserProfile.objects.create(user=self.user, role='investigator')
        self.client.login(username='inv3', password='pass123')

        self.case = Case.objects.create(
            case_number='CL-TEST-001',
            title='Test Investigation Case',
            description='A test case for unit testing.',
            status='open',
            priority='medium',
            created_by=self.user
        )

    def test_case_list_loads(self):
        response = self.client.get(reverse('cases:case_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CL-TEST-001')

    def test_case_detail_loads(self):
        response = self.client.get(reverse('cases:case_detail', args=[self.case.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.case.title)

    def test_case_create(self):
        response = self.client.post(reverse('cases:case_create'), {
            'case_number': 'CL-TEST-002',
            'title': 'New Test Case',
            'description': 'Created via test.',
            'case_type': 'fraud',
            'location': 'Test City',
            'status': 'open',
            'priority': 'low',
        })
        self.assertTrue(Case.objects.filter(case_number='CL-TEST-002').exists())

    def test_case_search(self):
        response = self.client.get(reverse('cases:case_list') + '?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CL-TEST-001')

    def test_case_filter_by_status(self):
        response = self.client.get(reverse('cases:case_list') + '?status=open')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CL-TEST-001')

    def test_case_delete(self):
        response = self.client.post(reverse('cases:case_delete', args=[self.case.pk]))
        self.assertRedirects(response, reverse('cases:case_list'))
        self.assertFalse(Case.objects.filter(pk=self.case.pk).exists())
