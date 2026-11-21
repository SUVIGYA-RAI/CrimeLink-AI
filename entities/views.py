"""
Entities app views.
Full CRUD functionality for Person, Vehicle, Organization, Location, PhoneRecord.
Supports case-centric association workflows when launched from a Case page.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import transaction

from .models import Person, Vehicle, Organization, Location, PhoneRecord
from .forms import PersonForm, VehicleForm, OrganizationForm, LocationForm, PhoneRecordForm
from cases.models import Case
from ai_analysis.models import EntityRelationship


# ============= PERSON VIEWS =============

@login_required
def person_list(request):
    """List all persons with search and gender filtering."""
    persons = Person.objects.prefetch_related('related_cases').all()
    search_query = request.GET.get('search', '')
    if search_query:
        persons = persons.filter(
            Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query)
        )
    gender_filter = request.GET.get('gender', '')
    if gender_filter:
        persons = persons.filter(gender=gender_filter)

    context = {
        'persons': persons,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'gender_choices': Person.GENDER_CHOICES,
        'total_count': persons.count(),
    }
    return render(request, 'entities/person_list.html', context)


@login_required
def person_detail(request, pk):
    """Show details of a single person."""
    person = get_object_or_404(Person, pk=pk)
    vehicles = person.vehicles.all()
    return render(request, 'entities/person_detail.html', {'person': person, 'vehicles': vehicles})


@login_required
def person_create(request):
    """
    Add a new person.
    If 'case_id' is provided, the person is automatically associated with that case
    and the user is redirected back to the case detail page.
    """
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    case = Case.objects.filter(pk=case_id).first() if case_id else None

    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                person = form.save()
                if case:
                    person.related_cases.add(case)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='person',
                        target_entity_id=person.pk,
                        defaults={
                            'relationship_type': 'involved_in',
                            'related_case': case,
                            'evidence_reference': f"Created and linked from Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
            if case:
                messages.success(request, f"Person '{person.full_name}' added and linked to Case {case.case_number}.")
                return redirect('cases:case_detail', pk=case.pk)
            messages.success(request, f"{person.full_name} added successfully.")
            return redirect('entities:person_detail', pk=person.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        initial = {'related_cases': [case]} if case else {}
        form = PersonForm(initial=initial)

    return render(request, 'entities/person_form.html', {
        'form': form,
        'title': 'Add Person',
        'action': 'Add',
        'case': case,
    })


@login_required
def person_edit(request, pk):
    """Edit an existing person."""
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, f'{person.full_name} updated successfully.')
            return redirect('entities:person_detail', pk=person.pk)
    else:
        form = PersonForm(instance=person)
    return render(request, 'entities/person_form.html', {
        'form': form,
        'obj': person,
        'title': 'Edit Person',
        'action': 'Update'
    })


@login_required
def person_delete(request, pk):
    """Delete a person with confirmation."""
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        name = person.full_name
        person.delete()
        messages.success(request, f'{name} has been deleted.')
        return redirect('entities:person_list')
    return render(request, 'entities/confirm_delete.html', {
        'obj': person,
        'type': 'Person',
        'back_url': 'entities:person_list'
    })


# ============= VEHICLE VIEWS =============

@login_required
def vehicle_list(request):
    """List all vehicles with search."""
    vehicles = Vehicle.objects.select_related('owner').prefetch_related('related_cases').all()
    search_query = request.GET.get('search', '')
    if search_query:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search_query) | Q(model_name__icontains=search_query)
        )
    type_filter = request.GET.get('vehicle_type', '')
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)

    context = {
        'vehicles': vehicles,
        'search_query': search_query,
        'type_filter': type_filter,
        'type_choices': Vehicle.VEHICLE_TYPE_CHOICES,
        'total_count': vehicles.count(),
    }
    return render(request, 'entities/vehicle_list.html', context)


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'entities/vehicle_detail.html', {'vehicle': vehicle})


@login_required
def vehicle_create(request):
    """
    Add a new vehicle.
    If 'case_id' is provided, automatically link to that case and redirect to case detail.
    """
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    case = Case.objects.filter(pk=case_id).first() if case_id else None

    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                vehicle = form.save()
                if case:
                    vehicle.related_cases.add(case)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='vehicle',
                        target_entity_id=vehicle.pk,
                        defaults={
                            'relationship_type': 'associated_vehicle',
                            'related_case': case,
                            'evidence_reference': f"Created and linked from Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
            if case:
                messages.success(request, f"Vehicle '{vehicle.registration_number}' added and linked to Case {case.case_number}.")
                return redirect('cases:case_detail', pk=case.pk)
            messages.success(request, f"Vehicle {vehicle.registration_number} added.")
            return redirect('entities:vehicle_detail', pk=vehicle.pk)
    else:
        initial = {'related_cases': [case]} if case else {}
        form = VehicleForm(initial=initial)

    return render(request, 'entities/vehicle_form.html', {
        'form': form,
        'title': 'Add Vehicle',
        'action': 'Add',
        'case': case,
    })


@login_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehicle {vehicle.registration_number} updated.')
            return redirect('entities:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'entities/vehicle_form.html', {
        'form': form,
        'obj': vehicle,
        'title': 'Edit Vehicle',
        'action': 'Update'
    })


@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        reg = vehicle.registration_number
        vehicle.delete()
        messages.success(request, f'Vehicle {reg} deleted.')
        return redirect('entities:vehicle_list')
    return render(request, 'entities/confirm_delete.html', {
        'obj': vehicle,
        'type': 'Vehicle',
        'back_url': 'entities:vehicle_list'
    })


# ============= ORGANIZATION VIEWS =============

@login_required
def organization_list(request):
    organizations = Organization.objects.prefetch_related('related_cases').all()
    search_query = request.GET.get('search', '')
    if search_query:
        organizations = organizations.filter(name__icontains=search_query)
    type_filter = request.GET.get('org_type', '')
    if type_filter:
        organizations = organizations.filter(organization_type=type_filter)

    context = {
        'organizations': organizations,
        'search_query': search_query,
        'type_filter': type_filter,
        'type_choices': Organization.ORG_TYPE_CHOICES,
        'total_count': organizations.count(),
    }
    return render(request, 'entities/organization_list.html', context)


@login_required
def organization_detail(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    return render(request, 'entities/organization_detail.html', {'org': org})


@login_required
def organization_create(request):
    """
    Add a new organization.
    If 'case_id' is provided, automatically link to that case and redirect to case detail.
    """
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    case = Case.objects.filter(pk=case_id).first() if case_id else None

    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                org = form.save()
                if case:
                    org.related_cases.add(case)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='organization',
                        target_entity_id=org.pk,
                        defaults={
                            'relationship_type': 'connected_organization',
                            'related_case': case,
                            'evidence_reference': f"Created and linked from Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
            if case:
                messages.success(request, f"Organization '{org.name}' added and linked to Case {case.case_number}.")
                return redirect('cases:case_detail', pk=case.pk)
            messages.success(request, f'{org.name} added successfully.')
            return redirect('entities:organization_detail', pk=org.pk)
    else:
        initial = {'related_cases': [case]} if case else {}
        form = OrganizationForm(initial=initial)

    return render(request, 'entities/organization_form.html', {
        'form': form,
        'title': 'Add Organization',
        'action': 'Add',
        'case': case,
    })


@login_required
def organization_edit(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, f'{org.name} updated.')
            return redirect('entities:organization_detail', pk=org.pk)
    else:
        form = OrganizationForm(instance=org)
    return render(request, 'entities/organization_form.html', {
        'form': form,
        'obj': org,
        'title': 'Edit Organization',
        'action': 'Update'
    })


@login_required
def organization_delete(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        name = org.name
        org.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('entities:organization_list')
    return render(request, 'entities/confirm_delete.html', {
        'obj': org,
        'type': 'Organization',
        'back_url': 'entities:organization_list'
    })


# ============= LOCATION VIEWS =============

@login_required
def location_list(request):
    locations = Location.objects.prefetch_related('related_cases').all()
    search_query = request.GET.get('search', '')
    if search_query:
        locations = locations.filter(
            Q(location_name__icontains=search_query) | Q(city__icontains=search_query)
        )

    context = {
        'locations': locations,
        'search_query': search_query,
        'total_count': locations.count(),
    }
    return render(request, 'entities/location_list.html', context)


@login_required
def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, 'entities/location_detail.html', {'location': location})


@login_required
def location_create(request):
    """
    Add a new location.
    If 'case_id' is provided, automatically link to that case and redirect to case detail.
    """
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    case = Case.objects.filter(pk=case_id).first() if case_id else None

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                location = form.save()
                if case:
                    location.related_cases.add(case)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='location',
                        target_entity_id=location.pk,
                        defaults={
                            'relationship_type': 'incident_location',
                            'related_case': case,
                            'evidence_reference': f"Created and linked from Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
            if case:
                messages.success(request, f"Location '{location.location_name}' added and linked to Case {case.case_number}.")
                return redirect('cases:case_detail', pk=case.pk)
            messages.success(request, f'{location.location_name} added.')
            return redirect('entities:location_detail', pk=location.pk)
    else:
        initial = {'related_cases': [case]} if case else {}
        form = LocationForm(initial=initial)

    return render(request, 'entities/location_form.html', {
        'form': form,
        'title': 'Add Location',
        'action': 'Add',
        'case': case,
    })


@login_required
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'{location.location_name} updated.')
            return redirect('entities:location_detail', pk=location.pk)
    else:
        form = LocationForm(instance=location)
    return render(request, 'entities/location_form.html', {
        'form': form,
        'obj': location,
        'title': 'Edit Location',
        'action': 'Update'
    })


@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        name = location.location_name
        location.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('entities:location_list')
    return render(request, 'entities/confirm_delete.html', {
        'obj': location,
        'type': 'Location',
        'back_url': 'entities:location_list'
    })


# ============= PHONE RECORD VIEWS =============

@login_required
def phone_record_list(request):
    phone_records = PhoneRecord.objects.select_related('related_case').all()
    search_query = request.GET.get('search', '')
    if search_query:
        phone_records = phone_records.filter(
            Q(caller_number__icontains=search_query) | Q(receiver_number__icontains=search_query)
        )
    case_filter = request.GET.get('case', '')
    if case_filter:
        phone_records = phone_records.filter(related_case__id=case_filter)

    all_cases = Case.objects.all()

    context = {
        'phone_records': phone_records,
        'search_query': search_query,
        'case_filter': case_filter,
        'all_cases': all_cases,
        'total_count': phone_records.count(),
    }
    return render(request, 'entities/phone_record_list.html', context)


@login_required
def phone_record_detail(request, pk):
    record = get_object_or_404(PhoneRecord, pk=pk)
    return render(request, 'entities/phone_record_detail.html', {'record': record})


@login_required
def phone_record_create(request):
    """
    Add a new phone call record.
    If 'case_id' is provided, pre-assign it to that case and redirect to case detail.
    """
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    case = Case.objects.filter(pk=case_id).first() if case_id else None

    if request.method == 'POST':
        form = PhoneRecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                if case:
                    record.related_case = case
                record.save()
            if case:
                messages.success(request, f"Phone record added and linked to Case {case.case_number}.")
                return redirect('cases:case_detail', pk=case.pk)
            messages.success(request, 'Phone record added successfully.')
            return redirect('entities:phone_record_detail', pk=record.pk)
    else:
        initial = {'related_case': case} if case else {}
        form = PhoneRecordForm(initial=initial)

    return render(request, 'entities/phone_record_form.html', {
        'form': form,
        'title': 'Add Phone Record',
        'action': 'Add',
        'case': case,
    })


@login_required
def phone_record_edit(request, pk):
    record = get_object_or_404(PhoneRecord, pk=pk)
    if request.method == 'POST':
        form = PhoneRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Phone record updated.')
            return redirect('entities:phone_record_detail', pk=record.pk)
    else:
        form = PhoneRecordForm(instance=record)
    return render(request, 'entities/phone_record_form.html', {
        'form': form,
        'obj': record,
        'title': 'Edit Phone Record',
        'action': 'Update'
    })


@login_required
def phone_record_delete(request, pk):
    record = get_object_or_404(PhoneRecord, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Phone record deleted.')
        return redirect('entities:phone_record_list')
    return render(request, 'entities/confirm_delete.html', {
        'obj': record,
        'type': 'Phone Record',
        'back_url': 'entities:phone_record_list'
    })
