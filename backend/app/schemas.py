"""Data schemas for SmartPay Reconciliation System."""
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PlatformTransaction(BaseModel):
    transaction_id: str
    order_id: str
    customer_id: str
    amount: Decimal
    currency: str
    timestamp: str
    status: str
    type: str  # PAYMENT or REFUND
    parent_transaction_id: Optional[str] = None
    batch_id: Optional[str] = None
    source_row: int = 0

class BankSettlement(BaseModel):
    settlement_id: str
    platform_trx_id: Optional[str] = None
    order_id: Optional[str] = None
    bank_reference: str
    settlement_date: str
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    currency: str
    settlement_status: str
    type: str  # SETTLEMENT or REFUND
    batch_id: Optional[str] = None
    original_payment_ref: Optional[str] = None
    source_row: int = 0

class ReconciliationRow(BaseModel):
    id: str
    source: str  # PLATFORM or BANK
    record_id: str
    order_id: Optional[str] = None
    date: str
    amount: str
    fee_amount: Optional[str] = "0.00"
    net_amount: Optional[str] = None
    currency: str
    matched_record_id: Optional[str] = None
    status: str
    difference_amount: str
    category: str
    explanation: str
    batch_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ReconciliationSummary(BaseModel):
    total_platform_count: int
    total_bank_count: int
    total_platform_amount: str
    total_bank_gross_amount: str
    total_bank_net_amount: str
    total_bank_fees: str
    currency: str
    
    # Counts
    matched_exact_count: int
    matched_partial_count: int
    matched_refund_count: int
    timing_difference_count: int
    rounding_difference_count: int
    duplicate_platform_count: int
    duplicate_bank_count: int
    unmatched_refund_count: int
    unmatched_platform_count: int
    unmatched_bank_count: int
    manual_review_count: int
    
    # Financial Impact
    total_discrepancy_amount: str
    duplicate_platform_exposure: str
    duplicate_bank_exposure: str
    unmatched_refund_exposure: str
    timing_difference_volume: str
    rounding_difference_net: str
    unsettled_platform_volume: str
    unclaimed_bank_volume: str

class ReconciliationResponse(BaseModel):
    summary: ReconciliationSummary
    records: List[ReconciliationRow]
    status_distribution: Dict[str, int]
    category_exposure: Dict[str, str]

