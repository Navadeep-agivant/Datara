import pytest
import pandas as pd
from app.detectors.outliers import OutlierDetector

def test_outlier_detector_iqr_and_mad():
    # Normal distribution with extreme values 1000 and -500
    values = [10.0, 11.0, 12.0, 10.5, 11.5, 10.8, 11.2, 12.1, 1000.0, -500.0]
    df = pd.DataFrame({"quantity": values})
    
    detector = OutlierDetector(iqr_multiplier=1.5)
    findings = detector.detect(df)
    
    assert len(findings) > 0
    f = findings[0]
    assert "quantity" in f.affected_columns
    # Rows 8 and 9 should be flagged
    assert 8 in f.affected_row_indices
    assert 9 in f.affected_row_indices
    assert "IQR" in f.detection_methods or "MAD" in f.detection_methods

def test_outlier_detector_constant_column():
    # Constant column should not generate false outliers
    df = pd.DataFrame({"constant_val": [5.0] * 20})
    detector = OutlierDetector()
    findings = detector.detect(df)
    assert len(findings) == 0
