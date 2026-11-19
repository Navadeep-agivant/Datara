import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingestion import ingest_csv
from app.utils.session import session_store
from app.models.dataset import UploadResponse, ErrorResponse

router = APIRouter(tags=["Upload"])

@router.post("/upload", response_model=UploadResponse, responses={400: {"model": ErrorResponse}})
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
    try:
        content = file.file.read() if hasattr(file, "file") else await file.read()
        df, encoding, warnings = ingest_csv(content, file.filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected parsing error: {str(e)}")

    session_id = str(uuid.uuid4())
    session_store.create_session(
        session_id=session_id,
        df=df,
        filename=file.filename,
        encoding=encoding,
        warnings=warnings
    )

    return UploadResponse(
        session_id=session_id,
        filename=file.filename,
        row_count=len(df),
        column_count=len(df.columns),
        encoding=encoding,
        parse_warnings=warnings
    )
