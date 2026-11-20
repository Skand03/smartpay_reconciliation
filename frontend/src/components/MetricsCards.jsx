import React from 'react';
import { 
  CreditCard, 
  Building2, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Divide, 
  Copy, 
  RotateCcw,
  TrendingDown
} from 'lucide-react';

export default function MetricsCards({ summary }) {
  if (!summary) return null;

  const totalMatchedCount = 
    (summary.matched_exact_count || 0) + 
    (summary.matched_partial_count || 0) + 
    (summary.matched_refund_count || 0);

  const totalDiscrepantCount = 
    (summary.timing_difference_count || 0) + 
    (summary.rounding_difference_count || 0) + 
    (summary.duplicate_platform_count || 0) + 
    (summary.duplicate_bank_count || 0) + 
    (summary.unmatched_refund_count || 0) + 
    (summary.unmatched_platform_count || 0) + 
    (summary.unmatched_bank_count || 0) + 
    (summary.manual_review_count || 0);

  return (
    <div className="space-y-4 mb-8">
      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Platform */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Platform Volume</p>
            <h3 className="text-2xl font-bold text-slate-900">₹{summary.total_platform_amount}</h3>
            <p className="text-xs text-slate-500 mt-1">
              <span className="font-semibold text-slate-700">{summary.total_platform_count}</span> recorded transactions
            </p>
          </div>
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
            <CreditCard className="w-5 h-5" />
          </div>
        </div>

        {/* Total Bank Gross */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Bank Settlements</p>
            <h3 className="text-2xl font-bold text-slate-900">₹{summary.total_bank_gross_amount}</h3>
            <p className="text-xs text-slate-500 mt-1">
              Net: ₹{summary.total_bank_net_amount} • Fees: ₹{summary.total_bank_fees}
            </p>
          </div>
          <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
            <Building2 className="w-5 h-5" />
          </div>
        </div>

        {/* Matched Records */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Reconciled Matches</p>
            <h3 className="text-2xl font-bold text-emerald-600">{totalMatchedCount}</h3>
            <p className="text-xs text-slate-500 mt-1">
              {summary.matched_exact_count} exact, {summary.matched_partial_count} partial, {summary.matched_refund_count} refund
            </p>
          </div>
          <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>

        {/* Total Discrepancy Amount */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Discrepancy Exposure</p>
            <h3 className="text-2xl font-bold text-rose-600">₹{summary.total_discrepancy_amount}</h3>
            <p className="text-xs text-slate-500 mt-1">
              <span className="font-semibold text-slate-700">{totalDiscrepantCount}</span> items flagged for review
            </p>
          </div>
          <div className="p-2.5 bg-rose-50 text-rose-600 rounded-lg">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Discrepancy Scenarios Breakdown Sub-grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Timing Difference */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-amber-600 mb-1">
            <Clock className="w-4 h-4" />
            <span className="text-xs font-semibold">1. Timing Difference</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-bold text-slate-800">{summary.timing_difference_count}</span>
            <span className="text-xs font-medium text-slate-600">₹{summary.timing_difference_volume} vol</span>
          </div>
        </div>

        {/* Rounding Difference */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-blue-600 mb-1">
            <Divide className="w-4 h-4" />
            <span className="text-xs font-semibold">2. Rounding Difference</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-bold text-slate-800">{summary.rounding_difference_count}</span>
            <span className="text-xs font-medium text-slate-600">₹{summary.rounding_difference_net} delta</span>
          </div>
        </div>

        {/* Duplicate Entries */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-purple-600 mb-1">
            <Copy className="w-4 h-4" />
            <span className="text-xs font-semibold">3. Duplicate Entries</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-bold text-slate-800">
              {(summary.duplicate_platform_count || 0) + (summary.duplicate_bank_count || 0)}
            </span>
            <span className="text-xs font-medium text-slate-600">
              ₹{(parseFloat(summary.duplicate_platform_exposure || 0) + parseFloat(summary.duplicate_bank_exposure || 0)).toFixed(2)} exp
            </span>
          </div>
        </div>

        {/* Unmatched Refund */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-rose-600 mb-1">
            <RotateCcw className="w-4 h-4" />
            <span className="text-xs font-semibold">4. Unmatched Refund</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-bold text-slate-800">{summary.unmatched_refund_count}</span>
            <span className="text-xs font-medium text-slate-600">₹{summary.unmatched_refund_exposure} risk</span>
          </div>
        </div>
      </div>
    </div>
  );
}

