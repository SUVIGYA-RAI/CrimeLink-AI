"""
AI Analysis - Views
-------------------
Provides Case-Centric AI extraction, review & approval workflows,
entity relationship tracking, and anomaly detection.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from data_management.models import UploadedFile, CallRecord, FinancialTransaction
from cases.models import Case
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord
from .models import ExtractedCase, ExtractedEntity, EntityRelationship, AnalysisAlert
from .services.entity_extractor import extract_case_centric_data
from .services.anomaly_detector import detect_call_anomalies, detect_transaction_anomalies


# ─────────────────────────────────────────────
# AI Analysis Dashboard
# ─────────────────────────────────────────────
@login_required
def home(request):
    """Main AI Analysis dashboard showing case extraction and alert statistics."""
    total_docs = UploadedFile.objects.count()
    total_extracted_cases = ExtractedCase.objects.count()
    pending_extracted_cases = ExtractedCase.objects.filter(review_status='pending').count()

    total_entities = ExtractedEntity.objects.count()
    pending_review = ExtractedEntity.objects.filter(review_status='pending').count()
    approved_rel = EntityRelationship.objects.filter(review_status='verified').count()
    total_alerts = AnalysisAlert.objects.count()
    pending_alerts = AnalysisAlert.objects.filter(review_status='pending').count()

    recent_cases = ExtractedCase.objects.select_related('uploaded_file').order_by('-created_at')[:5]
    recent_docs = UploadedFile.objects.order_by('-uploaded_at')[:5]
    recent_alerts = AnalysisAlert.objects.filter(review_status='pending').order_by('-created_at')[:5]
    recent_rels = EntityRelationship.objects.filter(review_status='verified').order_by('-created_at')[:5]

    # Data for Chart.js — entity type distribution
    entity_types = {}
    for e in ExtractedEntity.objects.values_list('entity_type', flat=True):
        entity_types[e] = entity_types.get(e, 0) + 1
    chart_labels = list(entity_types.keys())
    chart_values = list(entity_types.values())

    context = {
        'total_docs': total_docs,
        'total_extracted_cases': total_extracted_cases,
        'pending_extracted_cases': pending_extracted_cases,
        'total_entities': total_entities,
        'pending_review': pending_review,
        'approved_rel': approved_rel,
        'total_alerts': total_alerts,
        'pending_alerts': pending_alerts,
        'recent_cases': recent_cases,
        'recent_docs': recent_docs,
        'recent_alerts': recent_alerts,
        'recent_rels': recent_rels,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }
    return render(request, 'ai_analysis/home.html', context)


# ─────────────────────────────────────────────
# Case-Centric Entity Extraction
# ─────────────────────────────────────────────
@login_required
def extract_from_file(request, file_id):
    """
    Run Case-Centric AI Extraction on an uploaded document (PDF or TXT).
    Structures all extracted information under an ExtractedCase staging record.
    Deduplicates and preserves previous review states if rerun on the same document.
    """
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)

    if uploaded_file.file_type not in ('pdf', 'txt'):
        messages.error(request, 'Entity extraction is only available for PDF and TXT documents.')
        return redirect('data_management:file_list')

    try:
        if uploaded_file.file_type == 'pdf':
            from data_management.services.pdf_extractor import extract_text_from_pdf
            text = extract_text_from_pdf(uploaded_file.file.path)
        else:
            with open(uploaded_file.file.path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

        payload = extract_case_centric_data(text, filename=uploaded_file.filename)
        cases_list = payload.get('cases', [])

        if not cases_list:
            messages.warning(request, "No investigation case structure could be extracted from this document.")
            return redirect('data_management:file_list')

        first_case_data = cases_list[0]

        # Check if an ExtractedCase already exists for this uploaded file
        extracted_case = ExtractedCase.objects.filter(
            uploaded_file=uploaded_file,
            review_status='pending'
        ).first()

        if not extracted_case:
            extracted_case = ExtractedCase.objects.create(
                uploaded_file=uploaded_file,
                case_number=first_case_data.get('case_number', ''),
                title=first_case_data.get('title', 'Extracted Investigation Case'),
                description=first_case_data.get('description', ''),
                case_type=first_case_data.get('case_type', 'other'),
                incident_location=first_case_data.get('location', ''),
                extracted_data=first_case_data,
                review_status='pending',
            )
        else:
            # Update existing pending staged extraction
            extracted_case.case_number = first_case_data.get('case_number', '') or extracted_case.case_number
            extracted_case.title = first_case_data.get('title', extracted_case.title)
            extracted_case.description = first_case_data.get('description', extracted_case.description)
            extracted_case.case_type = first_case_data.get('case_type', extracted_case.case_type)
            extracted_case.incident_location = first_case_data.get('location', extracted_case.incident_location)
            extracted_case.extracted_data = first_case_data
            extracted_case.save()

        # Sync individual ExtractedEntity records for backward compatibility & review tables
        _sync_extracted_entities(uploaded_file, extracted_case, first_case_data)

        messages.success(
            request,
            f"Case extraction complete. Identified: {len(first_case_data.get('persons', []))} persons, "
            f"{len(first_case_data.get('vehicles', []))} vehicles, "
            f"{len(first_case_data.get('organizations', []))} organizations, and "
            f"{len(first_case_data.get('locations', []))} locations."
        )
        return redirect('ai_analysis:review_extracted_case', case_id=extracted_case.pk)

    except Exception as e:
        messages.error(request, f"Extraction failed: {e}")
        return redirect('data_management:file_list')


def _sync_extracted_entities(uploaded_file, extracted_case, case_data):
    """Save normalized ExtractedEntity rows grouped under the ExtractedCase."""
    existing_map = {
        (e.entity_text.strip().lower(), e.entity_type): e
        for e in ExtractedEntity.objects.filter(uploaded_file=uploaded_file)
    }

    # Persons
    for p in case_data.get('persons', []):
        key = (p['full_name'].strip().lower(), 'PERSON')
        if key not in existing_map:
            ExtractedEntity.objects.create(
                uploaded_file=uploaded_file,
                extracted_case=extracted_case,
                entity_text=p['full_name'][:255],
                entity_type='PERSON',
                role=p.get('role', 'Person of Interest'),
                extraction_method='spacy',
                confidence=0.95,
                review_status='pending',
            )

    # Vehicles
    for v in case_data.get('vehicles', []):
        key = (v['registration_number'].strip().lower(), 'VEHICLE_NUMBER')
        if key not in existing_map:
            ExtractedEntity.objects.create(
                uploaded_file=uploaded_file,
                extracted_case=extracted_case,
                entity_text=v['registration_number'][:255],
                entity_type='VEHICLE_NUMBER',
                role=f"{v.get('model_name', '')} ({v.get('color', '')})",
                extraction_method='regex',
                confidence=1.0,
                review_status='pending',
            )

    # Organizations
    for o in case_data.get('organizations', []):
        key = (o['name'].strip().lower(), 'ORG')
        if key not in existing_map:
            ExtractedEntity.objects.create(
                uploaded_file=uploaded_file,
                extracted_case=extracted_case,
                entity_text=o['name'][:255],
                entity_type='ORG',
                role=o.get('organization_type', 'company'),
                extraction_method='spacy',
                confidence=0.90,
                review_status='pending',
            )

    # Locations
    for l in case_data.get('locations', []):
        key = (l['location_name'].strip().lower(), 'GPE')
        if key not in existing_map:
            ExtractedEntity.objects.create(
                uploaded_file=uploaded_file,
                extracted_case=extracted_case,
                entity_text=l['location_name'][:255],
                entity_type='GPE',
                role=l.get('city', ''),
                extraction_method='spacy',
                confidence=0.90,
                review_status='pending',
            )


@login_required
def review_extracted_case(request, case_id):
    """
    Case-Centric Review Interface.
    Displays all extracted case attributes and nested entities for investigator approval.
    """
    extracted_case = get_object_or_404(ExtractedCase, pk=case_id)
    all_cases = Case.objects.order_by('-date_created')

    data = extracted_case.extracted_data or {}
    persons = data.get('persons', [])
    vehicles = data.get('vehicles', [])
    organizations = data.get('organizations', [])
    locations = data.get('locations', [])
    phone_records = data.get('phone_records', [])
    relationships = data.get('relationships', [])

    context = {
        'extracted_case': extracted_case,
        'data': data,
        'persons': persons,
        'vehicles': vehicles,
        'organizations': organizations,
        'locations': locations,
        'phone_records': phone_records,
        'relationships': relationships,
        'all_cases': all_cases,
        'case_type_choices': Case.CASE_TYPE_CHOICES,
    }
    return render(request, 'ai_analysis/case_review.html', context)


@login_required
def review_extracted_case_action(request, case_id, action):
    """
    Handles Approval or Rejection of an ExtractedCase in an atomic transaction.
    Guarantees no orphan records: every approved entity is committed and linked
    to its parent case.
    """
    extracted_case = get_object_or_404(ExtractedCase, pk=case_id)

    if action == 'reject':
        extracted_case.review_status = 'rejected'
        extracted_case.reviewed_by = request.user
        extracted_case.reviewed_at = timezone.now()
        extracted_case.save()
        extracted_case.entities.update(review_status='rejected')
        messages.info(request, "Extracted case and entities rejected. No records were committed to the database.")
        return redirect('ai_analysis:home')

    elif action == 'approve':
        # Retrieve form edits from the review submission
        target_case_id = request.POST.get('target_case_id', '').strip()
        case_number = request.POST.get('case_number', '').strip().upper()
        title = request.POST.get('title', '').strip()
        case_type = request.POST.get('case_type', 'other').strip()
        incident_location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()

        try:
            with transaction.atomic():
                # 1. Resolve or Create the permanent Case record
                if target_case_id and target_case_id.isdigit():
                    case = get_object_or_404(Case, pk=int(target_case_id))
                    # Update description if empty
                    if not case.description and description:
                        case.description = description
                        case.save()
                else:
                    if not case_number:
                        # Auto-generate a clean case number if none extracted
                        case_number = f"CL-AI-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                    case, created = Case.objects.get_or_create(
                        case_number=case_number,
                        defaults={
                            'title': title or f"Investigation Case {case_number}",
                            'description': description or "Extracted and approved via AI analysis.",
                            'case_type': case_type or 'other',
                            'location': incident_location,
                            'status': 'under_investigation',
                            'priority': 'medium',
                            'created_by': request.user,
                        }
                    )

                data = extracted_case.extracted_data or {}
                committed_persons = {}

                # 2. Commit & Deduplicate Persons
                for p in data.get('persons', []):
                    full_name = p['full_name'].strip()
                    phone = p.get('phone_number', '').strip()
                    role = p.get('role', 'Person of Interest')

                    person = Person.objects.filter(full_name__iexact=full_name).first()
                    if not person and phone:
                        person = Person.objects.filter(phone_number=phone).first()

                    if not person:
                        person = Person.objects.create(
                            full_name=full_name,
                            gender=p.get('gender', 'unknown'),
                            phone_number=phone,
                            description=f"Identified as {role} from document '{extracted_case.uploaded_file.filename}'."
                        )

                    person.related_cases.add(case)
                    committed_persons[full_name.lower()] = person

                # 3. Commit & Deduplicate Vehicles
                for v in data.get('vehicles', []):
                    plate = v['registration_number'].strip().upper()
                    vehicle = Vehicle.objects.filter(registration_number=plate).first()
                    if not vehicle:
                        vehicle = Vehicle.objects.create(
                            registration_number=plate,
                            model_name=v.get('model_name', 'Unknown Model'),
                            vehicle_type=v.get('vehicle_type', 'car'),
                            color=v.get('color', 'Unknown'),
                        )
                    vehicle.related_cases.add(case)

                    # Link owner if matched
                    owner_name = v.get('owner_name', '').strip().lower()
                    if owner_name and owner_name in committed_persons:
                        vehicle.owner = committed_persons[owner_name]
                        vehicle.save()

                # 4. Commit & Deduplicate Organizations
                for o in data.get('organizations', []):
                    name = o['name'].strip()
                    org = Organization.objects.filter(name__iexact=name).first()
                    if not org:
                        org = Organization.objects.create(
                            name=name,
                            organization_type=o.get('organization_type', 'company'),
                            address=o.get('address', ''),
                            description=f"Identified from document '{extracted_case.uploaded_file.filename}'."
                        )
                    org.related_cases.add(case)

                # 5. Commit & Deduplicate Locations
                for l in data.get('locations', []):
                    loc_name = l['location_name'].strip()
                    location = Location.objects.filter(location_name__iexact=loc_name).first()
                    if not location:
                        location = Location.objects.create(
                            location_name=loc_name,
                            city=l.get('city', loc_name),
                            state=l.get('state', ''),
                            address=l.get('address', ''),
                        )
                    location.related_cases.add(case)

                # 6. Commit Phone Records
                for pr in data.get('phone_records', []):
                    PhoneRecord.objects.get_or_create(
                        caller_number=pr['caller_number'],
                        receiver_number=pr['receiver_number'],
                        call_date=pr.get('call_date', timezone.now().date()),
                        call_time=pr.get('call_time', '12:00:00'),
                        duration=pr.get('duration', 180),
                        related_case=case,
                    )

                # 7. Sync all Case-Entity relationships for Network Analysis
                from cases.views import _sync_case_relationships
                _sync_case_relationships(case)

                # 8. Commit explicit Entity-to-Entity Relationships
                for r in data.get('relationships', []):
                    s_type = r.get('source_type', '').lower()
                    s_name = r.get('source_name', '').lower()
                    t_type = r.get('target_type', '').lower()
                    t_name = r.get('target_name', '').lower()

                    s_obj = None
                    t_obj = None

                    if s_type == 'person' and s_name in committed_persons:
                        s_obj = committed_persons[s_name]
                    if t_type == 'vehicle':
                        t_obj = Vehicle.objects.filter(registration_number__iexact=r.get('target_name')).first()
                    elif t_type == 'organization':
                        t_obj = Organization.objects.filter(name__iexact=r.get('target_name')).first()

                    if s_obj and t_obj:
                        EntityRelationship.objects.get_or_create(
                            source_entity_type=s_type,
                            source_entity_id=s_obj.pk,
                            target_entity_type=t_type,
                            target_entity_id=t_obj.pk,
                            defaults={
                                'relationship_type': r.get('relationship_type', 'associated_with'),
                                'related_case': case,
                                'evidence_reference': r.get('evidence', f"Extracted from document '{extracted_case.uploaded_file.filename}'"),
                                'review_status': 'verified',
                            }
                        )

                # 9. Mark staging records as approved
                extracted_case.review_status = 'approved'
                extracted_case.committed_case = case
                extracted_case.reviewed_by = request.user
                extracted_case.reviewed_at = timezone.now()
                extracted_case.save()

                extracted_case.entities.update(review_status='approved', related_case=case)

            messages.success(request, f"Case '{case.case_number}' and all associated entities successfully committed to the database.")
            return redirect('cases:case_detail', pk=case.pk)

        except Exception as e:
            messages.error(request, f"Failed to commit case: {e}")
            return redirect('ai_analysis:review_extracted_case', case_id=extracted_case.pk)

    return redirect('ai_analysis:home')


@login_required
def entity_list(request, file_id):
    """List all extracted entities for a given uploaded file."""
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    entities = ExtractedEntity.objects.filter(uploaded_file=uploaded_file).order_by('entity_type', 'entity_text')
    extracted_case = ExtractedCase.objects.filter(uploaded_file=uploaded_file).first()

    context = {
        'uploaded_file': uploaded_file,
        'extracted_case': extracted_case,
        'entities': entities,
        'pending_count': entities.filter(review_status='pending').count(),
        'approved_count': entities.filter(review_status='approved').count(),
    }
    return render(request, 'ai_analysis/entity_list.html', context)


@login_required
def review_entity(request, entity_id, action):
    """
    Approve or reject a single extracted entity.
    If the entity is linked to a case, automatically associates it with that case.
    """
    entity = get_object_or_404(ExtractedEntity, pk=entity_id)
    if action == 'approve':
        entity.review_status = 'approved'
        entity.save()
        sync_note = _sync_approved_entity_to_level1(entity)
        messages.success(request, f"Approved '{entity.entity_text}'. {sync_note}")
    elif action == 'reject':
        entity.review_status = 'rejected'
        entity.save()
        messages.info(request, f"Entity '{entity.entity_text}' marked as Rejected.")
    else:
        messages.error(request, 'Invalid action.')

    return redirect('ai_analysis:entity_list', file_id=entity.uploaded_file_id)


def _sync_approved_entity_to_level1(entity):
    """Saves an approved ExtractedEntity into the main entities database."""
    text = entity.entity_text.strip()
    etype = entity.entity_type
    doc_name = entity.uploaded_file.filename if entity.uploaded_file else 'FIR Document'
    target_case = entity.related_case or (entity.extracted_case and entity.extracted_case.committed_case)

    if etype == 'PERSON':
        person, created = Person.objects.get_or_create(
            full_name=text,
            defaults={
                'gender': 'unknown',
                'description': f"Extracted and approved from document '{doc_name}'."
            }
        )
        if target_case:
            person.related_cases.add(target_case)
        return "Saved to Persons database." if created else "Updated in Persons database."

    elif etype == 'VEHICLE_NUMBER':
        vehicle, created = Vehicle.objects.get_or_create(
            registration_number=text,
            defaults={
                'model_name': 'Unknown',
                'color': 'Unknown',
                'vehicle_type': 'car'
            }
        )
        if target_case:
            vehicle.related_cases.add(target_case)
        return "Saved to Vehicles database." if created else "Updated in Vehicles database."

    elif etype == 'ORG':
        org, created = Organization.objects.get_or_create(
            name=text,
            defaults={
                'organization_type': 'company',
                'description': f"Extracted and approved from document '{doc_name}'."
            }
        )
        if target_case:
            org.related_cases.add(target_case)
        return "Saved to Organizations database." if created else "Updated in Organizations database."

    elif etype in ('GPE', 'LOC', 'FAC'):
        loc, created = Location.objects.get_or_create(
            location_name=text,
            defaults={
                'city': text,
                'address': f"Mentioned in document '{doc_name}'."
            }
        )
        if target_case:
            loc.related_cases.add(target_case)
        return "Saved to Locations database." if created else "Updated in Locations database."

    return "Status updated to Approved."


# ─────────────────────────────────────────────
# Relationships
# ─────────────────────────────────────────────
@login_required
def relationship_list(request):
    """List all entity relationships."""
    relationships = EntityRelationship.objects.order_by('-created_at')
    context = {
        'relationships': relationships,
        'pending_count': relationships.filter(review_status='pending').count(),
    }
    return render(request, 'ai_analysis/relationship_list.html', context)


@login_required
def add_relationship(request):
    """Manually add a new relationship between two entities."""
    from entities.models import Person, Vehicle, Organization, Location
    from cases.models import Case

    if request.method == 'POST':
        source_raw = request.POST.get('source_entity', '').strip()
        target_raw = request.POST.get('target_entity', '').strip()
        rel_type = request.POST.get('relationship_type', '').strip()
        evidence = request.POST.get('evidence_reference', '').strip()
        confidence = request.POST.get('confidence_score', '1.0').strip()
        case_id = request.POST.get('related_case', '').strip()

        # Handle dropdown format "type:id" or fallback to separate inputs
        if source_raw and ':' in source_raw:
            src_type, src_id = source_raw.split(':', 1)
        else:
            src_type = request.POST.get('source_entity_type', '').strip()
            src_id = request.POST.get('source_entity_id', '0').strip()

        if target_raw and ':' in target_raw:
            tgt_type, tgt_id = target_raw.split(':', 1)
        else:
            tgt_type = request.POST.get('target_entity_type', '').strip()
            tgt_id = request.POST.get('target_entity_id', '0').strip()

        case = Case.objects.filter(pk=case_id).first() if case_id and case_id.isdigit() else None

        if src_type and src_id and tgt_type and tgt_id and rel_type:
            EntityRelationship.objects.create(
                source_entity_type=src_type,
                source_entity_id=int(src_id),
                target_entity_type=tgt_type,
                target_entity_id=int(tgt_id),
                relationship_type=rel_type,
                related_case=case,
                evidence_reference=evidence,
                confidence_score=float(confidence) if confidence else 1.0,
            )
            messages.success(request, 'Relationship added and marked as Pending Review.')
            return redirect('ai_analysis:relationship_list')
        else:
            messages.error(request, 'Please select both Source and Target entities, and a Relationship Type.')

    context = {
        'persons': Person.objects.order_by('full_name'),
        'vehicles': Vehicle.objects.order_by('registration_number'),
        'organizations': Organization.objects.order_by('name'),
        'locations': Location.objects.order_by('location_name'),
        'cases': Case.objects.order_by('-date_created'),
    }
    return render(request, 'ai_analysis/add_relationship.html', context)


@login_required
def review_relationship(request, rel_id, action):
    """Verify or reject a relationship."""
    rel = get_object_or_404(EntityRelationship, pk=rel_id)
    if action == 'verify':
        rel.review_status = 'verified'
        messages.success(request, 'Relationship verified.')
    elif action == 'reject':
        rel.review_status = 'rejected'
        messages.info(request, 'Relationship rejected.')
    rel.save()
    return redirect('ai_analysis:relationship_list')


# ─────────────────────────────────────────────
# Anomaly Detection
# ─────────────────────────────────────────────
@login_required
def run_anomaly_detection(request):
    """
    Run statistical anomaly detection on call records and financial transactions.
    Saves AnalysisAlert rows for anything unusual.
    """
    call_alerts = detect_call_anomalies()
    txn_alerts = detect_transaction_anomalies()
    total = len(call_alerts) + len(txn_alerts)
    messages.success(request, f"Anomaly detection complete. {total} alert(s) generated.")
    return redirect('ai_analysis:alert_list')


@login_required
def alert_list(request):
    """List all analysis alerts."""
    alerts = AnalysisAlert.objects.order_by('-created_at')
    context = {
        'alerts': alerts,
        'pending_count': alerts.filter(review_status='pending').count(),
    }
    return render(request, 'ai_analysis/alert_list.html', context)


@login_required
def review_alert(request, alert_id, action):
    """Mark an alert as reviewed or dismissed."""
    alert = get_object_or_404(AnalysisAlert, pk=alert_id)
    if action == 'reviewed':
        alert.review_status = 'reviewed'
        messages.success(request, 'Alert marked as reviewed.')
    elif action == 'dismiss':
        alert.review_status = 'dismissed'
        messages.info(request, 'Alert dismissed.')
    alert.save()
    return redirect('ai_analysis:alert_list')
