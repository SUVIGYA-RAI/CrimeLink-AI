"""
Management command to populate the database with synthetic sample data.
Run with: python manage.py load_sample_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from cases.models import Case
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord
import datetime


class Command(BaseCommand):
    help = 'Load synthetic sample data for CrimeLink AI demonstration'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')

        # Create admin user
        admin_user, created = User.objects.get_or_create(username='admin')
        if created:
            admin_user.set_password('admin123')
            admin_user.first_name = 'Admin'
            admin_user.last_name = 'User'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            UserProfile.objects.create(
                user=admin_user, role='admin',
                department='Administration', badge_number='A-001'
            )
            self.stdout.write(self.style.SUCCESS('  Admin user created (username: admin, password: admin123)'))

        # Create investigator user
        inv_user, created = User.objects.get_or_create(username='investigator1')
        if created:
            inv_user.set_password('inv123')
            inv_user.first_name = 'Raj'
            inv_user.last_name = 'Kumar'
            inv_user.save()
            UserProfile.objects.create(
                user=inv_user, role='investigator',
                department='Cybercrime Division', badge_number='CCD-042'
            )
            self.stdout.write(self.style.SUCCESS('  Investigator user created (username: investigator1, password: inv123)'))

        # Create sample cases
        cases_data = [
            {
                'case_number': 'CL-2024-001',
                'title': 'Cyber Fraud Ring Investigation',
                'description': (
                    'Investigation into a suspected cyber fraud ring operating across multiple states. '
                    'Victims reported unauthorized transactions totaling over ₹50 lakhs. '
                    'Digital forensics team identified suspicious IP clusters.'
                ),
                'case_type': 'cyber_crime',
                'location': 'Mumbai, Maharashtra',
                'status': 'under_investigation',
                'priority': 'high',
                'created_by': admin_user,
            },
            {
                'case_number': 'CL-2024-002',
                'title': 'Vehicle Theft Network - Sector 7',
                'description': (
                    'A series of luxury vehicle thefts reported in the Sector 7 area. '
                    'Stolen vehicles appear to be exported via the northern border. '
                    'Three suspects identified through CCTV analysis.'
                ),
                'case_type': 'theft',
                'location': 'Delhi NCR',
                'status': 'open',
                'priority': 'medium',
                'created_by': inv_user,
            },
            {
                'case_number': 'CL-2024-003',
                'title': 'Hawala Money Laundering',
                'description': (
                    'Suspected hawala operations discovered through banking transaction analysis. '
                    'Multiple shell companies identified. Network spans 4 cities.'
                ),
                'case_type': 'money_laundering',
                'location': 'Bengaluru, Karnataka',
                'status': 'under_investigation',
                'priority': 'high',
                'created_by': admin_user,
            },
            {
                'case_number': 'CL-2023-089',
                'title': 'Drug Supply Chain - Port Area',
                'description': (
                    'Investigation into suspected drug trafficking through the port area. '
                    'Contraband reportedly concealed in shipping containers.'
                ),
                'case_type': 'drug_trafficking',
                'location': 'Chennai, Tamil Nadu',
                'status': 'closed',
                'priority': 'high',
                'created_by': admin_user,
            },
            {
                'case_number': 'CL-2024-004',
                'title': 'Phone Phishing Campaign',
                'description': (
                    'Coordinated phishing campaign targeting senior citizens. '
                    'Callers impersonate bank officials to obtain OTPs.'
                ),
                'case_type': 'fraud',
                'location': 'Hyderabad, Telangana',
                'status': 'open',
                'priority': 'medium',
                'created_by': inv_user,
            },
        ]

        created_cases = []
        for case_data in cases_data:
            case, created = Case.objects.get_or_create(
                case_number=case_data['case_number'],
                defaults=case_data
            )
            created_cases.append(case)
            if created:
                self.stdout.write(f'  Case: {case.case_number}')

        # Create sample persons
        persons_data = [
            {
                'full_name': 'Vikram Sharma',
                'age': 34,
                'gender': 'male',
                'phone_number': '9876543210',
                'address': '45, Gandhi Nagar, Mumbai - 400001',
                'description': 'Primary suspect in CL-2024-001. Known for creating shell companies.',
            },
            {
                'full_name': 'Priya Mehta',
                'age': 28,
                'gender': 'female',
                'phone_number': '9765432109',
                'address': '12, MG Road, Bengaluru - 560001',
                'description': 'Financial controller in suspected money laundering network.',
            },
            {
                'full_name': 'Arjun Singh',
                'age': 41,
                'gender': 'male',
                'phone_number': '9654321098',
                'address': '78, Jahangirpuri, Delhi - 110033',
                'description': 'Known vehicle theft coordinator. Has priors in similar cases.',
            },
            {
                'full_name': 'Rekha Das',
                'age': 52,
                'gender': 'female',
                'phone_number': '9543210987',
                'address': '23, Anna Nagar, Chennai - 600040',
                'description': 'Port customs officer under investigation for facilitating contraband passage.',
            },
            {
                'full_name': 'Mohammad Farouk',
                'age': 38,
                'gender': 'male',
                'phone_number': '9432109876',
                'address': 'Banjara Hills, Hyderabad - 500034',
                'description': 'Linked to phishing operation. Role: call center manager.',
            },
        ]

        created_persons = []
        for i, pd in enumerate(persons_data):
            person, created = Person.objects.get_or_create(
                full_name=pd['full_name'], defaults=pd
            )
            created_persons.append(person)
            if created:
                # Link person to a case
                if i < len(created_cases):
                    person.related_cases.add(created_cases[i])
                self.stdout.write(f'  Person: {person.full_name}')

        # Create sample vehicles
        vehicles_data = [
            {'registration_number': 'MH02AB1234', 'vehicle_type': 'car', 'model_name': 'Honda City', 'color': 'Silver', 'owner': created_persons[0], 'related_case': created_cases[0]},
            {'registration_number': 'DL1A2345', 'vehicle_type': 'car', 'model_name': 'Toyota Fortuner', 'color': 'Black', 'owner': created_persons[2], 'related_case': created_cases[1]},
            {'registration_number': 'KA03CD6789', 'vehicle_type': 'motorcycle', 'model_name': 'Royal Enfield Bullet', 'color': 'Dark Blue', 'owner': created_persons[1], 'related_case': created_cases[2]},
            {'registration_number': 'TN09EF0001', 'vehicle_type': 'truck', 'model_name': 'Tata Ace', 'color': 'White', 'owner': created_persons[3], 'related_case': created_cases[3]},
        ]

        for vd in vehicles_data:
            vehicle, created = Vehicle.objects.get_or_create(
                registration_number=vd['registration_number'], defaults=vd
            )
            if created:
                self.stdout.write(f'  Vehicle: {vehicle.registration_number}')

        # Create sample organizations
        orgs_data = [
            {'name': 'TechPay Solutions Pvt Ltd', 'organization_type': 'company', 'address': 'Andheri East, Mumbai', 'description': 'Shell company suspected to be front for cyber fraud proceeds.'},
            {'name': 'QuickWheels Auto Trading', 'organization_type': 'company', 'address': 'Karol Bagh, New Delhi', 'description': 'Used vehicle dealer possibly facilitating stolen vehicle sales.'},
            {'name': 'Urban Hawala Network', 'organization_type': 'criminal_network', 'address': 'Shivajinagar, Bengaluru', 'description': 'Identified informal money transfer network.'},
        ]

        created_orgs = []
        for i, od in enumerate(orgs_data):
            org, created = Organization.objects.get_or_create(
                name=od['name'], defaults=od
            )
            created_orgs.append(org)
            if created:
                if i < len(created_cases):
                    org.related_cases.add(created_cases[i])
                self.stdout.write(f'  Org: {org.name}')

        # Create sample locations
        locs_data = [
            {'location_name': 'Cyber Café Omega', 'address': '15A, Dharavi Road, Mumbai', 'city': 'Mumbai', 'state': 'Maharashtra'},
            {'location_name': 'Delhi Vehicle Warehouse', 'address': 'Plot 44, Industrial Area, Rohtak Road', 'city': 'Delhi', 'state': 'Delhi'},
            {'location_name': 'Bengaluru Office Hub', 'address': '2nd Floor, Koramangala 5th Block', 'city': 'Bengaluru', 'state': 'Karnataka'},
        ]

        created_locs = []
        for i, ld in enumerate(locs_data):
            loc, created = Location.objects.get_or_create(
                location_name=ld['location_name'], defaults=ld
            )
            created_locs.append(loc)
            if created:
                if i < len(created_cases):
                    loc.related_cases.add(created_cases[i])
                self.stdout.write(f'  Location: {loc.location_name}')

        # Create sample phone records
        phone_data = [
            {'caller_number': '9876543210', 'receiver_number': '9111222333', 'call_date': datetime.date(2024, 10, 5), 'call_time': datetime.time(11, 23), 'duration': 342, 'related_case': created_cases[0]},
            {'caller_number': '9765432109', 'receiver_number': '9876543210', 'call_date': datetime.date(2024, 10, 6), 'call_time': datetime.time(14, 5), 'duration': 180, 'related_case': created_cases[0]},
            {'caller_number': '9654321098', 'receiver_number': '9000111222', 'call_date': datetime.date(2024, 10, 8), 'call_time': datetime.time(9, 15), 'duration': 95, 'related_case': created_cases[1]},
            {'caller_number': '9432109876', 'receiver_number': '8001002003', 'call_date': datetime.date(2024, 10, 12), 'call_time': datetime.time(16, 45), 'duration': 510, 'related_case': created_cases[4]},
            {'caller_number': '9543210987', 'receiver_number': '7500600700', 'call_date': datetime.date(2023, 11, 22), 'call_time': datetime.time(7, 30), 'duration': 228, 'related_case': created_cases[3]},
        ]

        for pd in phone_data:
            record, created = PhoneRecord.objects.get_or_create(
                caller_number=pd['caller_number'],
                call_date=pd['call_date'],
                call_time=pd['call_time'],
                defaults=pd
            )
            if created:
                self.stdout.write(f'  Phone record: {record.caller_number} → {record.receiver_number}')

        self.stdout.write(self.style.SUCCESS('\n✓ Sample data loaded successfully!'))
        self.stdout.write('\nDemo Login Credentials:')
        self.stdout.write('  Admin    → username: admin        | password: admin123')
        self.stdout.write('  Investigator → username: investigator1 | password: inv123')
