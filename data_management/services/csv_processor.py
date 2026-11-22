"""
CSV Processor Service using Pandas
-----------------------------------
Validates synthetic Call Detail Records and Financial Transactions.
Provides preview, data type checking, missing value detection, and ORM insertion.
"""

import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import CallRecord, FinancialTransaction

CALL_COLUMNS = {'caller_number', 'receiver_number', 'call_date', 'call_time', 'duration'}
FINANCIAL_COLUMNS = {'sender_id', 'receiver_id', 'amount', 'transaction_date', 'transaction_type'}


def _validate_csv_row(row, detected_type):
    errors = []

    if detected_type == 'csv_calls':
        for column in ('caller_number', 'receiver_number', 'call_date', 'call_time'):
            value = row.get(column)
            if pd.isna(value) or not str(value).strip():
                errors.append(f"Missing {column}")
            elif column in ('call_date', 'call_time'):
                try:
                    CallRecord._meta.get_field(column).clean(str(value).strip(), None)
                except ValidationError:
                    errors.append(f"Invalid {column}")
        try:
            duration = int(row.get('duration', 0))
            if duration < 0:
                errors.append("Negative duration")
            else:
                CallRecord._meta.get_field('duration').clean(duration, None)
        except (ValueError, TypeError):
            errors.append("Invalid duration integer")
        except ValidationError:
            errors.append("Invalid duration integer")

    elif detected_type == 'csv_financial':
        for column in ('sender_id', 'receiver_id', 'transaction_date', 'transaction_type'):
            value = row.get(column)
            if pd.isna(value) or not str(value).strip():
                errors.append(f"Missing {column}")
            elif column == 'transaction_date':
                try:
                    FinancialTransaction._meta.get_field(column).clean(str(value).strip(), None)
                except ValidationError:
                    errors.append(f"Invalid {column}")
        if pd.isna(row.get('amount')):
            errors.append("Missing amount")
        else:
            try:
                if float(row.get('amount')) <= 0:
                    errors.append("Amount must be positive")
            except (ValueError, TypeError):
                errors.append("Invalid decimal amount")

    return errors


def validate_and_preview_csv(file_path):
    """
    Reads CSV with Pandas, validates columns and data integrity,
    and returns preview records and error statistics.
    """
    df = pd.read_csv(file_path)
    # Normalize column names to lowercase and strip whitespace
    df.columns = df.columns.str.strip().str.lower()
    columns_list = list(df.columns)
    cols = set(df.columns)

    detected_type = None
    if CALL_COLUMNS.issubset(cols):
        detected_type = 'csv_calls'
    elif FINANCIAL_COLUMNS.issubset(cols):
        detected_type = 'csv_financial'
    else:
        return {
            'valid': False,
            'error': f"CSV columns do not match expected schemas. Found: {list(df.columns)}",
            'detected_type': 'unknown',
            'total_rows': len(df),
            'valid_rows': 0,
            'invalid_rows': len(df),
            'preview': [],
            'errors_list': ["Columns do not match required CDR or Financial format."]
        }

    total_rows = len(df)
    errors_list = []
    valid_count = 0

    for idx, row in df.iterrows():
        row_errors = _validate_csv_row(row, detected_type)
        if row_errors:
            errors_list.append(f"Row {idx + 1}: {', '.join(row_errors)}")
        else:
            valid_count += 1

    # Convert first 10 rows to list of lists for simple template rendering
    preview_rows = []
    for _, r in df.head(10).fillna('').iterrows():
        preview_rows.append([str(r[c]) for c in columns_list])

    return {
        'valid': True,
        'detected_type': detected_type,
        'detected_label': 'Call Detail Records' if detected_type == 'csv_calls' else 'Financial Transactions',
        'columns': columns_list,
        'total_rows': total_rows,
        'valid_rows': valid_count,
        'invalid_rows': total_rows - valid_count,
        'preview_rows': preview_rows,
        'errors_list': errors_list[:5],  # top 5 errors if any
    }


def import_csv_records(file_path, uploaded_file, related_case):
    """
    Imports valid CSV rows and links them to the selected case.
    """
    if related_case is None:
        raise ValueError("A case must be selected before importing CSV records.")

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.lower()
    cols = set(df.columns)

    if CALL_COLUMNS.issubset(cols):
        detected_type = 'csv_calls'
    elif FINANCIAL_COLUMNS.issubset(cols):
        detected_type = 'csv_financial'
    else:
        raise ValueError("CSV schema does not match known formats.")

    created_count = 0
    row_errors = []
    with transaction.atomic():
        for idx, row in df.iterrows():
            validation_errors = _validate_csv_row(row, detected_type)
            if validation_errors:
                row_errors.append(f"Row {idx + 1}: {', '.join(validation_errors)}")
                continue

            try:
                if detected_type == 'csv_calls':
                    CallRecord.objects.create(
                        uploaded_file=uploaded_file,
                        related_case=related_case,
                        caller_number=str(row['caller_number']).strip(),
                        receiver_number=str(row['receiver_number']).strip(),
                        call_date=str(row['call_date']).strip(),
                        call_time=str(row['call_time']).strip(),
                        duration=int(row['duration']),
                    )
                else:
                    FinancialTransaction.objects.create(
                        uploaded_file=uploaded_file,
                        related_case=related_case,
                        sender_id=str(row['sender_id']).strip(),
                        receiver_id=str(row['receiver_id']).strip(),
                        amount=float(row['amount']),
                        transaction_date=str(row['transaction_date']).strip(),
                        transaction_type=str(row['transaction_type']).strip(),
                    )
            except (ValidationError, ValueError, TypeError) as error:
                row_errors.append(f"Row {idx + 1}: {error}")
                continue
            created_count += 1

    if not created_count:
        details = '; '.join(row_errors[:5]) or 'The CSV contains no data rows.'
        raise ValueError(f"No valid rows were imported. {details}")

    record_label = 'call detail record(s)' if detected_type == 'csv_calls' else 'financial transaction(s)'
    summary = (
        f"Imported {created_count} {record_label} and linked them to case "
        f"{related_case.case_number}."
    )
    if row_errors:
        summary += f" Skipped {len(row_errors)} invalid row(s): {'; '.join(row_errors[:5])}"

    return {
        'detected_type': detected_type,
        'created_count': created_count,
        'summary': summary
    }
