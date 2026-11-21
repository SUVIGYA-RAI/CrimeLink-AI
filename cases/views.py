"""
Cases app views.
Full CRUD functionality and entity relationship management for investigation cases.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import transaction

from .models import Case
from .forms import CaseForm
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord
from ai_analysis.models import EntityRelationship


@login_required
def case_list(request):
    """
    Display all cases with search and filter functionality.
    Uses GET parameters for searching and filtering.
    """
    cases = Case.objects.select_related('created_by').all()

    # Search by case number or title
    search_query = request.GET.get('search', '')
    if search_query:
        cases = cases.filter(
            Q(case_number__icontains=search_query) | Q(title__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        cases = cases.filter(status=status_filter)

    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        cases = cases.filter(priority=priority_filter)

    context = {
        'cases': cases,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': Case.STATUS_CHOICES,
        'priority_choices': Case.PRIORITY_CHOICES,
        'total_count': cases.count(),
    }
    return render(request, 'cases/case_list.html', context)


@login_required
def case_detail(request, pk):
    """
    Show full details of a single case, including all linked entities
    (Persons, Vehicles, Organizations, Locations, Phone Records) and
    available entities for linking.
    """
    case = get_object_or_404(Case, pk=pk)

    # Get all entities related to this case
    persons = case.persons.all()
    vehicles = case.vehicles.all()
    organizations = case.organizations.all()
    locations = case.locations.all()
    phone_records = case.phone_records.order_by('-call_date', '-call_time')

    # Available entities for the "Link Existing Entity" modal/dropdowns
    available_persons = Person.objects.exclude(related_cases=case).order_by('full_name')
    available_vehicles = Vehicle.objects.exclude(related_cases=case).order_by('registration_number')
    available_organizations = Organization.objects.exclude(related_cases=case).order_by('name')
    available_locations = Location.objects.exclude(related_cases=case).order_by('location_name')
    available_phone_records = PhoneRecord.objects.exclude(related_case=case).order_by('-call_date')[:50]

    context = {
        'case': case,
        'persons': persons,
        'vehicles': vehicles,
        'organizations': organizations,
        'locations': locations,
        'phone_records': phone_records,
        'available_persons': available_persons,
        'available_vehicles': available_vehicles,
        'available_organizations': available_organizations,
        'available_locations': available_locations,
        'available_phone_records': available_phone_records,
    }
    return render(request, 'cases/case_detail.html', context)


@login_required
def case_create(request):
    """Create a new investigation case."""
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            messages.success(request, f'Case {case.case_number} created successfully.')
            return redirect('cases:case_detail', pk=case.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CaseForm()

    return render(request, 'cases/case_form.html', {'form': form, 'title': 'New Case', 'action': 'Create'})


@login_required
def case_edit(request, pk):
    """
    Edit an existing case and manage its associated entities
    (Persons, Vehicles, Organizations, Locations).
    """
    case = get_object_or_404(Case, pk=pk)

    all_persons = Person.objects.order_by('full_name')
    all_vehicles = Vehicle.objects.order_by('registration_number')
    all_organizations = Organization.objects.order_by('name')
    all_locations = Location.objects.order_by('location_name')

    linked_person_ids = set(case.persons.values_list('id', flat=True))
    linked_vehicle_ids = set(case.vehicles.values_list('id', flat=True))
    linked_org_ids = set(case.organizations.values_list('id', flat=True))
    linked_loc_ids = set(case.locations.values_list('id', flat=True))

    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            with transaction.atomic():
                case = form.save()

                # Sync ManyToMany entity associations from submitted checkboxes/selects
                selected_persons = request.POST.getlist('associated_persons')
                selected_vehicles = request.POST.getlist('associated_vehicles')
                selected_orgs = request.POST.getlist('associated_organizations')
                selected_locs = request.POST.getlist('associated_locations')

                case.persons.set(selected_persons)
                case.vehicles.set(selected_vehicles)
                case.organizations.set(selected_orgs)
                case.locations.set(selected_locs)

                # Sync relationships for Network Analysis
                _sync_case_relationships(case)

            messages.success(request, f'Case {case.case_number} and associated entities updated successfully.')
            return redirect('cases:case_detail', pk=case.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CaseForm(instance=case)

    context = {
        'form': form,
        'case': case,
        'title': 'Edit Case',
        'action': 'Update',
        'all_persons': all_persons,
        'all_vehicles': all_vehicles,
        'all_organizations': all_organizations,
        'all_locations': all_locations,
        'linked_person_ids': linked_person_ids,
        'linked_vehicle_ids': linked_vehicle_ids,
        'linked_org_ids': linked_org_ids,
        'linked_loc_ids': linked_loc_ids,
    }
    return render(request, 'cases/case_form.html', context)


@login_required
def case_delete(request, pk):
    """Delete a case with confirmation."""
    case = get_object_or_404(Case, pk=pk)

    if request.method == 'POST':
        case_number = case.case_number
        case.delete()
        messages.success(request, f'Case {case_number} has been deleted.')
        return redirect('cases:case_list')

    return render(request, 'cases/case_confirm_delete.html', {'case': case})


@login_required
def case_link_entity(request, pk):
    """
    Associate an existing entity (Person, Vehicle, Organization, Location, PhoneRecord)
    with the current case.
    """
    case = get_object_or_404(Case, pk=pk)

    if request.method == 'POST':
        entity_type = request.POST.get('entity_type', '').strip().lower()
        entity_id = request.POST.get('entity_id', '').strip()

        if not entity_id or not entity_id.isdigit():
            messages.error(request, 'Please select a valid entity to link.')
            return redirect('cases:case_detail', pk=case.pk)

        entity_id = int(entity_id)

        try:
            with transaction.atomic():
                if entity_type == 'person':
                    person = get_object_or_404(Person, pk=entity_id)
                    case.persons.add(person)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='person',
                        target_entity_id=person.pk,
                        defaults={
                            'relationship_type': 'involved_in',
                            'related_case': case,
                            'evidence_reference': f"Manually associated with Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
                    messages.success(request, f"Person '{person.full_name}' linked to case {case.case_number}.")

                elif entity_type == 'vehicle':
                    vehicle = get_object_or_404(Vehicle, pk=entity_id)
                    case.vehicles.add(vehicle)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='vehicle',
                        target_entity_id=vehicle.pk,
                        defaults={
                            'relationship_type': 'associated_vehicle',
                            'related_case': case,
                            'evidence_reference': f"Manually associated with Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
                    messages.success(request, f"Vehicle '{vehicle.registration_number}' linked to case {case.case_number}.")

                elif entity_type == 'organization':
                    org = get_object_or_404(Organization, pk=entity_id)
                    case.organizations.add(org)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='organization',
                        target_entity_id=org.pk,
                        defaults={
                            'relationship_type': 'connected_organization',
                            'related_case': case,
                            'evidence_reference': f"Manually associated with Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
                    messages.success(request, f"Organization '{org.name}' linked to case {case.case_number}.")

                elif entity_type == 'location':
                    loc = get_object_or_404(Location, pk=entity_id)
                    case.locations.add(loc)
                    EntityRelationship.objects.get_or_create(
                        source_entity_type='case',
                        source_entity_id=case.pk,
                        target_entity_type='location',
                        target_entity_id=loc.pk,
                        defaults={
                            'relationship_type': 'incident_location',
                            'related_case': case,
                            'evidence_reference': f"Manually associated with Case {case.case_number}",
                            'review_status': 'verified',
                        }
                    )
                    messages.success(request, f"Location '{loc.location_name}' linked to case {case.case_number}.")

                elif entity_type in ('phone', 'phonerecord'):
                    rec = get_object_or_404(PhoneRecord, pk=entity_id)
                    rec.related_case = case
                    rec.save()
                    messages.success(request, f"Phone record '{rec.caller_number} → {rec.receiver_number}' linked to case {case.case_number}.")

                else:
                    messages.error(request, 'Unsupported entity type.')
        except Exception as e:
            messages.error(request, f"Failed to link entity: {e}")

    return redirect('cases:case_detail', pk=case.pk)


@login_required
def case_unlink_entity(request, pk, entity_type, entity_id):
    """
    Remove an entity's association with a case without deleting the entity itself.
    """
    case = get_object_or_404(Case, pk=pk)
    entity_type = entity_type.strip().lower()

    try:
        with transaction.atomic():
            if entity_type == 'person':
                person = get_object_or_404(Person, pk=entity_id)
                case.persons.remove(person)
                EntityRelationship.objects.filter(
                    source_entity_type='case',
                    source_entity_id=case.pk,
                    target_entity_type='person',
                    target_entity_id=person.pk,
                ).delete()
                messages.info(request, f"Person '{person.full_name}' was unlinked from case {case.case_number}. The person record was preserved.")

            elif entity_type == 'vehicle':
                vehicle = get_object_or_404(Vehicle, pk=entity_id)
                case.vehicles.remove(vehicle)
                EntityRelationship.objects.filter(
                    source_entity_type='case',
                    source_entity_id=case.pk,
                    target_entity_type='vehicle',
                    target_entity_id=vehicle.pk,
                ).delete()
                messages.info(request, f"Vehicle '{vehicle.registration_number}' was unlinked from case {case.case_number}. The vehicle record was preserved.")

            elif entity_type == 'organization':
                org = get_object_or_404(Organization, pk=entity_id)
                case.organizations.remove(org)
                EntityRelationship.objects.filter(
                    source_entity_type='case',
                    source_entity_id=case.pk,
                    target_entity_type='organization',
                    target_entity_id=org.pk,
                ).delete()
                messages.info(request, f"Organization '{org.name}' was unlinked from case {case.case_number}. The organization record was preserved.")

            elif entity_type == 'location':
                loc = get_object_or_404(Location, pk=entity_id)
                case.locations.remove(loc)
                EntityRelationship.objects.filter(
                    source_entity_type='case',
                    source_entity_id=case.pk,
                    target_entity_type='location',
                    target_entity_id=loc.pk,
                ).delete()
                messages.info(request, f"Location '{loc.location_name}' was unlinked from case {case.case_number}. The location record was preserved.")

            elif entity_type in ('phone', 'phonerecord'):
                rec = get_object_or_404(PhoneRecord, pk=entity_id, related_case=case)
                rec.related_case = None
                rec.save()
                messages.info(request, f"Phone record '{rec.caller_number} → {rec.receiver_number}' was unlinked from case {case.case_number}. The call record was preserved.")

            else:
                messages.error(request, 'Unsupported entity type.')

    except Exception as e:
        messages.error(request, f"Failed to unlink entity: {e}")

    return redirect('cases:case_detail', pk=case.pk)


def _sync_case_relationships(case):
    """
    Ensure EntityRelationship rows exist for all entities directly linked to this case,
    allowing the Network Analysis graph to accurately reflect current case associations.
    """
    for person in case.persons.all():
        EntityRelationship.objects.get_or_create(
            source_entity_type='case',
            source_entity_id=case.pk,
            target_entity_type='person',
            target_entity_id=person.pk,
            defaults={
                'relationship_type': 'involved_in',
                'related_case': case,
                'evidence_reference': f"Linked to Case {case.case_number}",
                'review_status': 'verified',
            }
        )

    for vehicle in case.vehicles.all():
        EntityRelationship.objects.get_or_create(
            source_entity_type='case',
            source_entity_id=case.pk,
            target_entity_type='vehicle',
            target_entity_id=vehicle.pk,
            defaults={
                'relationship_type': 'associated_vehicle',
                'related_case': case,
                'evidence_reference': f"Linked to Case {case.case_number}",
                'review_status': 'verified',
            }
        )
        if vehicle.owner:
            EntityRelationship.objects.get_or_create(
                source_entity_type='person',
                source_entity_id=vehicle.owner.pk,
                target_entity_type='vehicle',
                target_entity_id=vehicle.pk,
                defaults={
                    'relationship_type': 'owns',
                    'related_case': case,
                    'evidence_reference': f"Vehicle owner registered in Case {case.case_number}",
                    'review_status': 'verified',
                }
            )

    for org in case.organizations.all():
        EntityRelationship.objects.get_or_create(
            source_entity_type='case',
            source_entity_id=case.pk,
            target_entity_type='organization',
            target_entity_id=org.pk,
            defaults={
                'relationship_type': 'connected_organization',
                'related_case': case,
                'evidence_reference': f"Linked to Case {case.case_number}",
                'review_status': 'verified',
            }
        )

    for loc in case.locations.all():
        EntityRelationship.objects.get_or_create(
            source_entity_type='case',
            source_entity_id=case.pk,
            target_entity_type='location',
            target_entity_id=loc.pk,
            defaults={
                'relationship_type': 'incident_location',
                'related_case': case,
                'evidence_reference': f"Linked to Case {case.case_number}",
                'review_status': 'verified',
            }
        )
