"""API routes for SmartPay Payment Reconciliation."""
import csv
import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, StreamingResponse
from typing import Optional

from app.schemas import ReconciliationResponse
from app.services.validator import validate_and_parse_platform_csv, validate_and_parse_bank_csv
from app.services.sample_generator import generate_sample_datasets
from app.services.engine import ReconciliationEngine

router = APIRouter()
engine = ReconciliationEngine(settlement_window_days=2)

@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "SmartPay Reconciliation API", "version": "1.0.0"}

@router.get("/sample-data")
def get_sample_data():
    plt_csv, bnk_csv = generate_sample_datasets()
    return {
        "platform_csv": plt_csv,
        "bank_csv": bnk_csv
    }

@router.get("/sample-data/platform.csv")
def download_sample_platform_csv():
    plt_csv, _ = generate_sample_datasets()
    return Response(
        content=plt_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=platform_transactions_sample.csv"}
    )

@router.get("/sample-data/bank.csv")
def download_sample_bank_csv():
    _, bnk_csv = generate_sample_datasets()
    return Response(
        content=bnk_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bank_settlements_sample.csv"}
    )

@router.post("/reconcile-sample", response_model=ReconciliationResponse)
def reconcile_sample_datasets(settlement_window: int = 2):
    plt_csv, bnk_csv = generate_sample_datasets()
    plt_records, plt_errors = validate_and_parse_platform_csv(plt_csv)
    bnk_records, bnk_errors = validate_and_parse_bank_csv(bnk_csv)
    
    if plt_errors:
        raise HTTPException(status_code=400, detail={"platform_errors": plt_errors})
    if bnk_errors:
        raise HTTPException(status_code=400, detail={"bank_errors": bnk_errors})
        
    recon_engine = ReconciliationEngine(settlement_window_days=settlement_window)
    return recon_engine.reconcile(plt_records, bnk_records)

@router.post("/reconcile", response_model=ReconciliationResponse)
async def reconcile_uploaded_files(
    platform_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
    settlement_window: int = Form(2)
):
    try:
        plt_bytes = await platform_file.read()
        bnk_bytes = await bank_file.read()
        
        plt_content = plt_bytes.decode("utf-8-sig", errors="replace")
        bnk_content = bnk_bytes.decode("utf-8-sig", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV files: {str(e)}")
        
    plt_records, plt_errors = validate_and_parse_platform_csv(plt_content)
    bnk_records, bnk_errors = validate_and_parse_bank_csv(bnk_content)
    
    if plt_errors and len(plt_records) == 0:
        raise HTTPException(status_code=400, detail={"message": "Platform CSV validation failed", "errors": plt_errors})
    if bnk_errors and len(bnk_records) == 0:
        raise HTTPException(status_code=400, detail={"message": "Bank CSV validation failed", "errors": bnk_errors})
        
    recon_engine = ReconciliationEngine(settlement_window_days=settlement_window)
    return recon_engine.reconcile(plt_records, bnk_records)

@router.post("/export-csv")
def export_reconciliation_csv(response_data: ReconciliationResponse):
    """Exports the full 100% accounted reconciliation output rows into an audit-ready CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Source Ledger", "Record ID", "Order ID", "Date / Timestamp",
        "Amount (INR)", "Fee Amount (INR)", "Net Amount (INR)", "Currency",
        "Counterpart Matched ID", "Reconciliation Status", "Category",
        "Variance / Discrepancy Amount", "Batch ID", "Audit Explanation"
    ])
    
    for row in response_data.records:
        writer.writerow([
            row.source,
            row.record_id,
            row.order_id or "",
            row.date,
            row.amount,
            row.fee_amount or "0.00",
            row.net_amount or "",
            row.currency,
            row.matched_record_id or "",
            row.status,
            row.category,
            row.difference_amount,
            row.batch_id or "",
            row.explanation
        ])
        
    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=SmartPay_Reconciliation_Report.csv"}
    )

