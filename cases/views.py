"""
Cases app views.
Full CRUD functionality for investigation cases.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Case
from .forms import CaseForm


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
    """Show full details of a single case."""
    case = get_object_or_404(Case, pk=pk)
    # Get all entities related to this case
    persons = case.persons.all()
    vehicles = case.vehicles.all()
    organizations = case.organizations.all()
    locations = case.locations.all()
    phone_records = case.phone_records.order_by('-call_date')[:10]

    context = {
        'case': case,
        'persons': persons,
        'vehicles': vehicles,
        'organizations': organizations,
        'locations': locations,
        'phone_records': phone_records,
    }
    return render(request, 'cases/case_detail.html', context)


@login_required
def case_create(request):
    """Create a new investigation case."""
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user  # Assign current user as creator
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
    """Edit an existing case."""
    case = get_object_or_404(Case, pk=pk)

    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, f'Case {case.case_number} updated successfully.')
            return redirect('cases:case_detail', pk=case.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CaseForm(instance=case)

    return render(request, 'cases/case_form.html', {'form': form, 'case': case, 'title': 'Edit Case', 'action': 'Update'})


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
