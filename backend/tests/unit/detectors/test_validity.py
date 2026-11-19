import pandas as pd
import pytest
from app.detectors.validity import ValidityDetector

def test_validity_detector_dates():
    detector = ValidityDetector()
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
        "order_date": ["15/01/2024", "2024-01-16", "2026-02-30", "invalid-date-str"],
    })
    findings = detector.detect(df)
    date_findings = [f for f in findings if "order_date" in f.affected_columns]
    assert len(date_findings) > 0
    date_finding = date_findings[0]
    assert date_finding.issue_family == "invalid"
    # Row 2 (2026-02-30) and Row 3 (invalid-date-str) should be flagged
    assert 2 in date_finding.affected_row_indices
    assert 3 in date_finding.affected_row_indices
    assert 0 not in date_finding.affected_row_indices
    assert 1 not in date_finding.affected_row_indices

def test_validity_detector_phone():
    detector = ValidityDetector()
    df = pd.DataFrame({
        "phone": ["+919876543210", "9876543214", "0000000000", "123", "9999999999"]
    })
    findings = detector.detect(df)
    phone_findings = [f for f in findings if "phone" in f.affected_columns]
    assert len(phone_findings) > 0
    phone_finding = phone_findings[0]
    assert phone_finding.issue_family == "invalid"
    # "0000000000" (dummy repetitive), "123" (too short), "9999999999" (dummy repetitive)
    assert 2 in phone_finding.affected_row_indices  # 0000000000
    assert 3 in phone_finding.affected_row_indices  # 123
    assert 4 in phone_finding.affected_row_indices  # 9999999999
    assert 0 not in phone_finding.affected_row_indices
    assert 1 not in phone_finding.affected_row_indices

def test_validity_detector_email():
    detector = ValidityDetector()
    df = pd.DataFrame({
        "email": ["valid.user@example.com", "bob.wilson@invalid-email", "test@domain.org", "no-at-sign.com", "bad@domain"]
    })
    findings = detector.detect(df)
    email_findings = [f for f in findings if "email" in f.affected_columns]
    assert len(email_findings) > 0
    email_finding = email_findings[0]
    assert email_finding.issue_family == "invalid"
    assert 1 in email_finding.affected_row_indices  # bob.wilson@invalid-email (no valid TLD)
    assert 3 in email_finding.affected_row_indices  # no-at-sign.com
    assert 4 in email_finding.affected_row_indices  # bad@domain (no valid TLD)
    assert 0 not in email_finding.affected_row_indices
    assert 2 not in email_finding.affected_row_indices

def test_validity_detector_rating():
    detector = ValidityDetector()
    df = pd.DataFrame({
        "rating": [5.0, 4.0, 0.0, 6.0, 10.0, 1.0]
    })
    findings = detector.detect(df)
    rating_findings = [f for f in findings if "rating" in f.affected_columns]
    assert len(rating_findings) > 0
    rating_finding = rating_findings[0]
    assert rating_finding.issue_family == "invalid"
    assert 2 in rating_finding.affected_row_indices  # 0.0 (< 1.0)
    assert 3 in rating_finding.affected_row_indices  # 6.0 (> 5.0)
    assert 4 in rating_finding.affected_row_indices  # 10.0 (> 5.0)
    assert 0 not in rating_finding.affected_row_indices
    assert 1 not in rating_finding.affected_row_indices
    assert 5 not in rating_finding.affected_row_indices

def test_validity_detector_delivery_days_and_quantity():
    detector = ValidityDetector()
    df = pd.DataFrame({
        "delivery_days": [3, 0, -3, 45],
        "quantity": [2, 1, -2, 0]
    })
    findings = detector.detect(df)
    
    delivery_findings = [f for f in findings if "delivery_days" in f.affected_columns]
    assert len(delivery_findings) > 0
    assert 2 in delivery_findings[0].affected_row_indices  # -3
    assert 0 not in delivery_findings[0].affected_row_indices
    assert 1 not in delivery_findings[0].affected_row_indices

    qty_findings = [f for f in findings if "quantity" in f.affected_columns]
    assert len(qty_findings) > 0
    assert 2 in qty_findings[0].affected_row_indices  # -2 (<= 0)
    assert 3 in qty_findings[0].affected_row_indices  # 0 (<= 0)
    assert 0 not in qty_findings[0].affected_row_indices
    assert 1 not in qty_findings[0].affected_row_indices
