"""
Data Management - Views
-----------------------
Handles file uploads, PDF/TXT text extraction, and CSV preview & validation with Pandas.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UploadedFileForm
from .models import UploadedFile, CallRecord, FinancialTransaction
from .services.csv_processor import validate_and_preview_csv, import_csv_records
from .services.pdf_extractor import extract_text_from_pdf


@login_required
def index(request):
    """Landing page for Data Management."""
    total_files     = UploadedFile.objects.count()
    completed_files = UploadedFile.objects.filter(status='completed').count()
    call_records    = CallRecord.objects.count()
    financial_txns  = FinancialTransaction.objects.count()
    recent_files    = UploadedFile.objects.order_by('-uploaded_at')[:6]

    context = {
        'total_files':     total_files,
        'completed_files': completed_files,
        'call_records':    call_records,
        'financial_txns':  financial_txns,
        'recent_files':    recent_files,
    }
    return render(request, 'data_management/index.html', context)


@login_required
def upload_file(request):
    """Handle document or dataset upload."""
    if request.method == 'POST':
        form = UploadedFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.save(commit=False)
            uploaded.filename = request.FILES['file'].name
            ext = uploaded.filename.split('.')[-1].lower()

            uploaded.uploaded_by = request.user

            if ext == 'pdf':
                uploaded.file_type = 'pdf'
                uploaded.status = 'processing'
                uploaded.save()
                try:
                    text = extract_text_from_pdf(uploaded.file.path)
                    uploaded.processing_summary = f'Extracted {len(text)} characters from PDF.'
                    uploaded.status = 'completed'
                    messages.success(request, f"PDF '{uploaded.filename}' uploaded and processed successfully.")
                except Exception as e:
                    uploaded.status = 'error'
                    uploaded.processing_summary = str(e)
                    messages.error(request, f"Error reading PDF: {e}")
                uploaded.save()
                return redirect('data_management:file_list')

            elif ext == 'txt':
                uploaded.file_type = 'txt'
                uploaded.status = 'processing'
                uploaded.save()
                try:
                    with open(uploaded.file.path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    uploaded.processing_summary = f'Read {len(text)} characters from TXT file.'
                    uploaded.status = 'completed'
                    messages.success(request, f"TXT '{uploaded.filename}' uploaded successfully.")
                except Exception as e:
                    uploaded.status = 'error'
                    uploaded.processing_summary = str(e)
                    messages.error(request, f"Error reading TXT: {e}")
                uploaded.save()
                return redirect('data_management:file_list')

            elif ext == 'csv':
                uploaded.file_type = 'csv_calls'  # will be finalized upon validation
                uploaded.status = 'pending_review'
                uploaded.save()
                # Redirect to CSV validation & preview workflow
                return redirect('data_management:preview_csv', file_id=uploaded.pk)

    else:
        form = UploadedFileForm()

    return render(request, 'data_management/upload.html', {'form': form})


@login_required
def preview_csv(request, file_id):
    """
    Pandas-based CSV preview and validation page.
    Displays column integrity, row counts, valid/invalid records, and a data preview.
    """
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    validation = validate_and_preview_csv(uploaded_file.file.path)

    if validation['valid']:
        uploaded_file.file_type = validation['detected_type']
        uploaded_file.save()

    context = {
        'uploaded_file': uploaded_file,
        'validation':    validation,
    }
    return render(request, 'data_management/preview_csv.html', context)


@login_required
def confirm_import_csv(request, file_id):
    """Confirm and import the validated CSV records into the SQLite database."""
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)

    if request.method == 'POST':
        try:
            result = import_csv_records(uploaded_file.file.path, uploaded_file=uploaded_file)
            uploaded_file.file_type = result['detected_type']
            uploaded_file.processing_summary = result['summary']
            uploaded_file.status = 'completed'
            uploaded_file.save()
            messages.success(request, result['summary'])
        except Exception as e:
            uploaded_file.status = 'error'
            uploaded_file.processing_summary = str(e)
            uploaded_file.save()
            messages.error(request, f"Import error: {e}")

        return redirect('data_management:file_list')

    return redirect('data_management:preview_csv', file_id=file_id)


@login_required
def file_list(request):
    """List uploaded files for the investigator."""
    files = UploadedFile.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    return render(request, 'data_management/file_list.html', {'files': files})


@login_required
def delete_file(request, file_id):
    """Delete an uploaded file and all data associated with it."""
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)

    # Permission check: owner or superuser
    if uploaded_file.uploaded_by != request.user and not request.user.is_superuser:
        messages.error(request, "You do not have permission to delete this file.")
        return redirect('data_management:file_list')

    filename = uploaded_file.filename

    # Delete all associated records across apps
    from ai_analysis.models import ExtractedEntity
    ExtractedEntity.objects.filter(uploaded_file=uploaded_file).delete()
    CallRecord.objects.filter(uploaded_file=uploaded_file).delete()
    FinancialTransaction.objects.filter(uploaded_file=uploaded_file).delete()

    # Remove physical file from disk if present
    try:
        if uploaded_file.file:
            uploaded_file.file.delete(save=False)
    except Exception:
        pass

    uploaded_file.delete()
    messages.success(request, f"File '{filename}' and all its extracted entities and records have been deleted.")
    return redirect('data_management:file_list')
