"""API Integration Tests for SmartPay."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.sample_generator import generate_sample_datasets

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_sample_data_endpoint():
    res = client.get("/api/sample-data")
    assert res.status_code == 200
    data = res.json()
    assert "platform_csv" in data
    assert "bank_csv" in data
    assert "TRX-IN-1001" in data["platform_csv"]
    assert "STL-IN-7001" in data["bank_csv"]

def test_reconcile_sample_endpoint():
    res = client.post("/api/reconcile-sample")
    assert res.status_code == 200
    data = res.json()
    summary = data["summary"]
    assert summary["currency"] == "INR"
    assert summary["total_platform_count"] > 0
    assert summary["total_bank_count"] > 0
    assert summary["matched_exact_count"] > 0
    assert summary["timing_difference_count"] > 0
    assert summary["rounding_difference_count"] > 0
    assert summary["duplicate_platform_count"] > 0
    assert summary["duplicate_bank_count"] > 0
    assert summary["unmatched_refund_count"] > 0
    assert len(data["records"]) == summary["total_platform_count"] + summary["total_bank_count"]

def test_reconcile_uploaded_files():
    plt_csv, bnk_csv = generate_sample_datasets()
    files = {
        "platform_file": ("platform.csv", plt_csv, "text/csv"),
        "bank_file": ("bank.csv", bnk_csv, "text/csv")
    }
    data = {"settlement_window": 2}
    res = client.post("/api/reconcile", files=files, data=data)
    assert res.status_code == 200
    payload = res.json()
    assert payload["summary"]["matched_exact_count"] > 0

def test_export_csv_endpoint():
    res_recon = client.post("/api/reconcile-sample")
    recon_json = res_recon.json()
    
    res_export = client.post("/api/export-csv", json=recon_json)
    assert res_export.status_code == 200
    assert "text/csv" in res_export.headers["content-type"]
    assert "Source Ledger,Record ID,Order ID" in res_export.text

