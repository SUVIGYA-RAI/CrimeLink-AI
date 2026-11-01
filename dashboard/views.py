"""
Dashboard app views.
The main intelligence dashboard showing statistics and recent activity.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from cases.models import Case
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord


@login_required
def dashboard_home(request):
    """
    Main dashboard view.
    Fetches real statistics from the database and passes them to the template.
    """

    # --- Database Statistics (real ORM queries) ---
    total_cases = Case.objects.count()
    total_persons = Person.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_organizations = Organization.objects.count()
    total_locations = Location.objects.count()
    total_phone_records = PhoneRecord.objects.count()

    # Case status breakdown for Chart.js
    open_cases = Case.objects.filter(status='open').count()
    investigating_cases = Case.objects.filter(status='under_investigation').count()
    closed_cases = Case.objects.filter(status='closed').count()

    # High priority open cases
    high_priority_cases = Case.objects.filter(priority='high', status='open').count()

    # Recent 5 cases
    recent_cases = Case.objects.select_related('created_by').order_by('-date_created')[:5]

    # Recently added entities (across all types)
    recent_persons = Person.objects.order_by('-date_added')[:3]
    recent_vehicles = Vehicle.objects.order_by('-date_added')[:3]

    # Total users
    total_users = User.objects.count()

    context = {
        'total_cases': total_cases,
        'total_persons': total_persons,
        'total_vehicles': total_vehicles,
        'total_organizations': total_organizations,
        'total_locations': total_locations,
        'total_phone_records': total_phone_records,
        'open_cases': open_cases,
        'investigating_cases': investigating_cases,
        'closed_cases': closed_cases,
        'high_priority_cases': high_priority_cases,
        'recent_cases': recent_cases,
        'recent_persons': recent_persons,
        'recent_vehicles': recent_vehicles,
        'total_users': total_users,
    }

    return render(request, 'dashboard/home.html', context)
