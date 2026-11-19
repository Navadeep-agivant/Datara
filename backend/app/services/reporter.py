import os
from datetime import datetime, timezone
import io
from jinja2 import Environment, FileSystemLoader
import pandas as pd
from app.utils.session import SessionState
from app.utils.formula_guard import sanitize_dataframe_for_export

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def render_html_report(state: SessionState) -> str:
    template = env.get_template("report.html")
    return template.render(
        filename=state.filename,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        score_before=state.quality_score_before,
        score_after=state.quality_score_after,
        findings=state.findings,
        explanations=state.explanations,
        transformation_log=state.applied_cleaning_history
    )

def export_cleaned_csv(state: SessionState) -> bytes:
    sanitized_df = sanitize_dataframe_for_export(state.working_df)
    buf = io.StringIO()
    sanitized_df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
