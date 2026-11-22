"""
CSV Processor Service using Pandas
-----------------------------------
Validates synthetic Call Detail Records and Financial Transactions.
Provides preview, data type checking, missing value detection, and ORM insertion.
"""

import pandas as pd
from datetime import datetime
from ..models import CallRecord, FinancialTransaction, UploadedFile

CALL_COLUMNS = {'caller_number', 'receiver_number', 'call_date', 'call_time', 'duration'}
FINANCIAL_COLUMNS = {'sender_id', 'receiver_id', 'amount', 'transaction_date', 'transaction_type'}


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

    if detected_type == 'csv_calls':
        for idx, row in df.iterrows():
            row_num = idx + 1
            row_errs = []
            if pd.isna(row.get('caller_number')) or not str(row.get('caller_number')).strip():
                row_errs.append("Missing caller_number")
            if pd.isna(row.get('receiver_number')) or not str(row.get('receiver_number')).strip():
                row_errs.append("Missing receiver_number")
            try:
                dur = int(row.get('duration', 0))
                if dur < 0:
                    row_errs.append("Negative duration")
            except (ValueError, TypeError):
                row_errs.append("Invalid duration integer")

            if row_errs:
                errors_list.append(f"Row {row_num}: {', '.join(row_errs)}")
            else:
                valid_count += 1

    elif detected_type == 'csv_financial':
        for idx, row in df.iterrows():
            row_num = idx + 1
            row_errs = []
            if pd.isna(row.get('sender_id')) or not str(row.get('sender_id')).strip():
                row_errs.append("Missing sender_id")
            if pd.isna(row.get('receiver_id')) or not str(row.get('receiver_id')).strip():
                row_errs.append("Missing receiver_id")
            try:
                amt = float(row.get('amount', 0))
                if amt <= 0:
                    row_errs.append("Amount must be positive")
            except (ValueError, TypeError):
                row_errs.append("Invalid decimal amount")

            if row_errs:
                errors_list.append(f"Row {row_num}: {', '.join(row_errs)}")
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


def import_csv_records(file_path, uploaded_file=None):
    """
    Parses CSV and creates ORM objects in the database.
    """
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.lower()
    cols = set(df.columns)

    created_count = 0
    if CALL_COLUMNS.issubset(cols):
        for _, row in df.iterrows():
            try:
                CallRecord.objects.create(
                    uploaded_file=uploaded_file,
                    caller_number=str(row['caller_number']).strip(),
                    receiver_number=str(row['receiver_number']).strip(),
                    call_date=str(row['call_date']).strip(),
                    call_time=str(row['call_time']).strip(),
                    duration=int(row['duration']),
                )
                created_count += 1
            except Exception:
                continue
        detected_type = 'csv_calls'
        summary = f"Successfully imported {created_count} call detail record(s)."

    elif FINANCIAL_COLUMNS.issubset(cols):
        for _, row in df.iterrows():
            try:
                FinancialTransaction.objects.create(
                    uploaded_file=uploaded_file,
                    sender_id=str(row['sender_id']).strip(),
                    receiver_id=str(row['receiver_id']).strip(),
                    amount=float(row['amount']),
                    transaction_date=str(row['transaction_date']).strip(),
                    transaction_type=str(row['transaction_type']).strip(),
                )
                created_count += 1
            except Exception:
                continue
        detected_type = 'csv_financial'
        summary = f"Successfully imported {created_count} financial transaction(s)."
    else:
        raise ValueError("CSV schema does not match known formats.")

    return {
        'detected_type': detected_type,
        'created_count': created_count,
        'summary': summary
    }
