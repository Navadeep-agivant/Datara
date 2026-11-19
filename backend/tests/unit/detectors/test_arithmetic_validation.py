import pandas as pd
from app.detectors.validation import ArithmeticValidationDetector

def test_arithmetic_validation_with_currency_tolerance():
    data = {
        "order_id": ["ORD1", "ORD2", "ORD3", "ORD4"],
        "quantity": [2, 3, 10, 5],
        "unit_price": [19.99, 10.00, 5.50, 20.00],
        # ORD1: 2 * 19.99 = 39.98 (exact match)
        # ORD2: 3 * 10.00 = 30.00 (within 0.01 cent rounding: 30.009 -> diff 0.009 <= 0.01)
        # ORD3: 10 * 5.50 = 55.00, but recorded as 75.00 (diff 20.00 > 0.01 -> ANOMALY)
        # ORD4: 5 * 20.00 = 100.00, but recorded as 90.00 (diff 10.00 > 0.01 -> ANOMALY)
        "total_amount": [39.98, 30.009, 75.00, 90.00],
    }
    df = pd.DataFrame(data)

    detector = ArithmeticValidationDetector(tolerance=0.01)
    findings = detector.detect(df)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.issue_family == "arithmetic_conflict"
    assert 2 in finding.affected_row_indices  # ORD3
    assert 3 in finding.affected_row_indices  # ORD4
    assert 0 not in finding.affected_row_indices  # ORD1 valid
    assert 1 not in finding.affected_row_indices  # ORD2 valid within 0.01 tolerance

def test_arithmetic_validation_skips_when_columns_missing():
    df = pd.DataFrame({"product": ["A", "B"], "city": ["Mumbai", "Delhi"]})
    detector = ArithmeticValidationDetector()
    findings = detector.detect(df)
    assert len(findings) == 0
