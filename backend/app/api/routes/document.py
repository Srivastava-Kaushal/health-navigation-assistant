import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.models.document import Document
from app.core.config import settings
from app.models.document import Document, ExtractedResult
from app.services.ocr_service import extract_text
from app.services.parser_service import parse_prescription_text
import json

router = APIRouter()

@router.post("/upload")
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_type = file.filename.split(".")[-1].lower()

    doc = Document(
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "status": doc.status
    }
@router.post("/extract/{document_id}")
def extract_document_text(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    extraction = extract_text(doc.file_path, doc.file_type)
    parsed_data = parse_prescription_text(extraction["raw_text"])

    result = ExtractedResult(
        document_id=doc.id,
        raw_text=extraction["raw_text"],
        structured_json=json.dumps(parsed_data),
        confidence_score=0.3 if extraction["low_confidence"] else 0.9
    )
    db.add(result)

    doc.status = "processed"
    db.commit()
    db.refresh(result)

    return {
        "document_id": doc.id,
        "raw_text": extraction["raw_text"],
        "parsed_data": parsed_data,
        "low_confidence": extraction["low_confidence"],
        "message": extraction["message"]
    }
@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = db.query(ExtractedResult).filter(
        ExtractedResult.document_id == document_id
    ).first()

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "raw_text": result.raw_text if result else None,
        "structured_json": result.structured_json if result else None
    }