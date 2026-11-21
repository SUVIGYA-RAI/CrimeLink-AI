"""
Anomaly Detector Service
------------------------
Implements simple, explainable pattern detection.

DISCLAIMER: An anomaly alert is an investigative lead only.
            It does NOT imply guilt or criminal involvement.
"""
from data_management.models import CallRecord, FinancialTransaction
from ai_analysis.models import AnalysisAlert


# ─── Thresholds ────────────────────────────────────────────────────────────────
CALL_FREQ_THRESHOLD    = 5    # more than N calls between same pair  → flag
TXN_AMOUNT_MULTIPLIER  = 3.0  # amount > 3× mean                     → flag
TXN_FREQ_THRESHOLD     = 4    # more than N transactions between same pair → flag


def detect_call_anomalies():
    """
    Detect unusual call patterns:
      1. Same caller–receiver pair with more than CALL_FREQ_THRESHOLD calls.

    Returns list of AnalysisAlert objects created.
    """
    created_alerts = []

    records = CallRecord.objects.values_list('caller_number', 'receiver_number')
    if not records:
        return created_alerts

    # Count call frequency per pair
    pair_count = {}
    for caller, receiver in records:
        key = (caller, receiver)
        pair_count[key] = pair_count.get(key, 0) + 1

    for (caller, receiver), count in pair_count.items():
        if count > CALL_FREQ_THRESHOLD:
            # Only create alert if one doesn't already exist for this pair
            exists = AnalysisAlert.objects.filter(
                alert_type='Unusual Call Frequency',
                related_record=f"{caller} → {receiver}",
            ).exists()
            if not exists:
                alert = AnalysisAlert.objects.create(
                    alert_type='Unusual Call Frequency',
                    description=(
                        f"Pattern Detected: {count} calls recorded between {caller} and {receiver}. "
                        f"This exceeds the threshold of {CALL_FREQ_THRESHOLD} calls. "
                        f"This is an investigative lead and does NOT imply wrongdoing."
                    ),
                    related_record=f"{caller} → {receiver}",
                    severity='medium',
                )
                created_alerts.append(alert)

    return created_alerts


def detect_transaction_anomalies():
    """
    Detect unusual financial transaction patterns:
      1. Transaction amount > TXN_AMOUNT_MULTIPLIER × dataset mean.
      2. Same sender–receiver pair with more than TXN_FREQ_THRESHOLD transactions.

    Returns list of AnalysisAlert objects created.
    """
    created_alerts = []

    all_txns = list(FinancialTransaction.objects.all())
    if not all_txns:
        return created_alerts

    # Calculate mean transaction amount for the dataset
    amounts = [float(t.amount) for t in all_txns]
    mean_amount = sum(amounts) / len(amounts) if amounts else 0
    threshold_amount = mean_amount * TXN_AMOUNT_MULTIPLIER

    # 1. Large transaction amount
    for txn in all_txns:
        if float(txn.amount) > threshold_amount:
            exists = AnalysisAlert.objects.filter(
                alert_type='Unusually Large Transaction',
                related_record=f"Transaction #{txn.pk}",
            ).exists()
            if not exists:
                alert = AnalysisAlert.objects.create(
                    alert_type='Unusually Large Transaction',
                    description=(
                        f"Pattern Detected: Transaction #{txn.pk} of amount ₹{txn.amount} "
                        f"from {txn.sender_id} to {txn.receiver_id} on {txn.transaction_date} "
                        f"is {TXN_AMOUNT_MULTIPLIER}× above the dataset mean (₹{mean_amount:.2f}). "
                        f"Requires Review – this is only an investigative lead."
                    ),
                    related_record=f"Transaction #{txn.pk}",
                    severity='high',
                )
                created_alerts.append(alert)

    # 2. High frequency between same pair
    pair_count = {}
    for txn in all_txns:
        key = (txn.sender_id, txn.receiver_id)
        pair_count[key] = pair_count.get(key, 0) + 1

    for (sender, receiver), count in pair_count.items():
        if count > TXN_FREQ_THRESHOLD:
            exists = AnalysisAlert.objects.filter(
                alert_type='Repeated Transaction Pattern',
                related_record=f"{sender} → {receiver}",
            ).exists()
            if not exists:
                alert = AnalysisAlert.objects.create(
                    alert_type='Repeated Transaction Pattern',
                    description=(
                        f"Pattern Detected: {count} transactions found between {sender} and {receiver}. "
                        f"This exceeds the frequency threshold of {TXN_FREQ_THRESHOLD}. "
                        f"This is an investigative lead and does NOT imply wrongdoing."
                    ),
                    related_record=f"{sender} → {receiver}",
                    severity='medium',
                )
                created_alerts.append(alert)

    return created_alerts
