"""
AI Analysis - Views
-------------------
All heavy AI logic lives in ai_analysis/services/.
Views are kept thin: they receive a request, call the service, and render a template.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from data_management.models import UploadedFile, CallRecord, FinancialTransaction
from .models import ExtractedEntity, EntityRelationship, AnalysisAlert
from .services.entity_extractor import extract_entities
from .services.anomaly_detector import detect_call_anomalies, detect_transaction_anomalies


# ─────────────────────────────────────────────
# AI Analysis Dashboard
# ─────────────────────────────────────────────
@login_required
def home(request):
    """Main AI Analysis dashboard — all statistics come from the DB."""
    total_docs      = UploadedFile.objects.count()
    total_entities  = ExtractedEntity.objects.count()
    pending_review  = ExtractedEntity.objects.filter(review_status='pending').count()
    approved_rel    = EntityRelationship.objects.filter(review_status='verified').count()
    total_alerts    = AnalysisAlert.objects.count()
    pending_alerts  = AnalysisAlert.objects.filter(review_status='pending').count()

    recent_docs     = UploadedFile.objects.order_by('-uploaded_at')[:5]
    recent_entities = ExtractedEntity.objects.select_related('uploaded_file').order_by('-created_at')[:10]
    recent_alerts   = AnalysisAlert.objects.filter(review_status='pending').order_by('-created_at')[:5]
    recent_rels     = EntityRelationship.objects.filter(review_status='verified').order_by('-created_at')[:5]

    # Data for Chart.js — entity type distribution
    entity_types = {}
    for e in ExtractedEntity.objects.values_list('entity_type', flat=True):
        entity_types[e] = entity_types.get(e, 0) + 1
    chart_labels = list(entity_types.keys())
    chart_values = list(entity_types.values())

    context = {
        'total_docs':     total_docs,
        'total_entities': total_entities,
        'pending_review': pending_review,
        'approved_rel':   approved_rel,
        'total_alerts':   total_alerts,
        'pending_alerts': pending_alerts,
        'recent_docs':    recent_docs,
        'recent_entities':recent_entities,
        'recent_alerts':  recent_alerts,
        'recent_rels':    recent_rels,
        'chart_labels':   chart_labels,
        'chart_values':   chart_values,
    }
    return render(request, 'ai_analysis/home.html', context)


# ─────────────────────────────────────────────
# Entity Extraction
# ─────────────────────────────────────────────
@login_required
def extract_from_file(request, file_id):
    """
    Run spaCy + regex extraction on an uploaded text/pdf file.
    Preserves any already-approved entities so approval status is never wiped out.
    """
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)

    if uploaded_file.file_type not in ('pdf', 'txt'):
        messages.error(request, 'Entity extraction is only available for PDF and TXT files.')
        return redirect('ai_analysis:entity_list', file_id=file_id)

    try:
        if uploaded_file.file_type == 'pdf':
            from data_management.services.pdf_extractor import extract_text_from_pdf
            text = extract_text_from_pdf(uploaded_file.file.path)
        else:
            with open(uploaded_file.file.path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

        raw_entities = extract_entities(text)

        # Map existing entities to prevent overwriting approved/rejected states
        existing_map = {
            (e.entity_text.strip().lower(), e.entity_type): e
            for e in ExtractedEntity.objects.filter(uploaded_file=uploaded_file)
        }

        new_count = 0
        for ent in raw_entities:
            key = (ent['text'].strip().lower(), ent['type'])
            if key not in existing_map:
                ExtractedEntity.objects.create(
                    uploaded_file=uploaded_file,
                    entity_text=ent['text'][:255],
                    entity_type=ent['type'],
                    extraction_method=ent['method'],
                    confidence=ent.get('confidence', 1.0),
                    review_status='pending',
                )
                new_count += 1

        total_count = ExtractedEntity.objects.filter(uploaded_file=uploaded_file).count()
        messages.success(request, f"Entity extraction completed: {total_count} unique entities available ({new_count} newly identified).")
    except Exception as e:
        messages.error(request, f"Extraction failed: {e}")

    return redirect('ai_analysis:entity_list', file_id=file_id)


@login_required
def entity_list(request, file_id):
    """List all extracted entities for a given uploaded file."""
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    entities = ExtractedEntity.objects.filter(uploaded_file=uploaded_file).order_by('entity_type', 'entity_text')
    context = {
        'uploaded_file': uploaded_file,
        'entities':      entities,
        'pending_count': entities.filter(review_status='pending').count(),
        'approved_count': entities.filter(review_status='approved').count(),
    }
    return render(request, 'ai_analysis/entity_list.html', context)


@login_required
def review_entity(request, entity_id, action):
    """
    Approve or reject a single extracted entity.
    Approving an entity automatically creates/syncs it into the Level 1 entities database.
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
    """
    Saves an approved ExtractedEntity directly into the Level 1 entities database
    (Person, Vehicle, Organization, Location) so it immediately reflects across
    the entire system and relationship dropdowns.
    """
    from entities.models import Person, Vehicle, Organization, Location
    text = entity.entity_text.strip()
    etype = entity.entity_type
    doc_name = entity.uploaded_file.filename if entity.uploaded_file else 'FIR Document'

    if etype == 'PERSON':
        person, created = Person.objects.get_or_create(
            full_name=text,
            defaults={
                'gender': 'unknown',
                'description': f"Extracted and approved from document '{doc_name}'."
            }
        )
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
        return "Saved to Vehicles database." if created else "Updated in Vehicles database."

    elif etype == 'ORG':
        org, created = Organization.objects.get_or_create(
            name=text,
            defaults={
                'organization_type': 'company',
                'description': f"Extracted and approved from document '{doc_name}'."
            }
        )
        return "Saved to Organizations database." if created else "Updated in Organizations database."

    elif etype in ('GPE', 'LOC', 'FAC'):
        loc, created = Location.objects.get_or_create(
            location_name=text,
            defaults={
                'city': text,
                'address': f"Mentioned in document '{doc_name}'."
            }
        )
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
        rel_type   = request.POST.get('relationship_type', '').strip()
        evidence   = request.POST.get('evidence_reference', '').strip()
        confidence = request.POST.get('confidence_score', '1.0').strip()

        # Handle dropdown format "type:id" or fallback to separate inputs
        if source_raw and ':' in source_raw:
            src_type, src_id = source_raw.split(':', 1)
        else:
            src_type = request.POST.get('source_entity_type', '').strip()
            src_id   = request.POST.get('source_entity_id', '0').strip()

        if target_raw and ':' in target_raw:
            tgt_type, tgt_id = target_raw.split(':', 1)
        else:
            tgt_type = request.POST.get('target_entity_type', '').strip()
            tgt_id   = request.POST.get('target_entity_id', '0').strip()

        if src_type and src_id and tgt_type and tgt_id and rel_type:
            EntityRelationship.objects.create(
                source_entity_type=src_type,
                source_entity_id=int(src_id),
                target_entity_type=tgt_type,
                target_entity_id=int(tgt_id),
                relationship_type=rel_type,
                evidence_reference=evidence,
                confidence_score=float(confidence),
            )
            messages.success(request, 'Relationship added and marked as Pending Review.')
            return redirect('ai_analysis:relationship_list')
        else:
            messages.error(request, 'Please select both Source and Target entities, and a Relationship Type.')

    context = {
        'persons':       Person.objects.order_by('full_name'),
        'vehicles':      Vehicle.objects.order_by('registration_number'),
        'organizations': Organization.objects.order_by('name'),
        'locations':     Location.objects.order_by('location_name'),
        'cases':         Case.objects.order_by('-date_created'),
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
    txn_alerts  = detect_transaction_anomalies()
    total = len(call_alerts) + len(txn_alerts)
    messages.success(request, f"Anomaly detection complete. {total} alert(s) generated.")
    return redirect('ai_analysis:alert_list')


@login_required
def alert_list(request):
    """List all analysis alerts."""
    alerts = AnalysisAlert.objects.order_by('-created_at')
    context = {
        'alerts':        alerts,
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
