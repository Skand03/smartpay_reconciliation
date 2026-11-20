import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Download, 
  Filter, 
  CheckCircle2, 
  Clock, 
  Divide, 
  Copy, 
  RotateCcw, 
  AlertTriangle,
  HelpCircle,
  ArrowUpRight
} from 'lucide-react';

const STATUS_BADGES = {
  'MATCHED_EXACT': { label: 'Exact Match', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  'MATCHED_PARTIAL': { label: 'Partial Match', bg: 'bg-teal-50 text-teal-700 border-teal-200', icon: CheckCircle2 },
  'MATCHED_REFUND': { label: 'Refund Matched', bg: 'bg-cyan-50 text-cyan-700 border-cyan-200', icon: CheckCircle2 },
  'TIMING_DIFFERENCE': { label: 'Timing Lag', bg: 'bg-amber-50 text-amber-700 border-amber-200', icon: Clock },
  'ROUNDING_DIFFERENCE': { label: 'Rounding Diff', bg: 'bg-sky-50 text-sky-700 border-sky-200', icon: Divide },
  'DUPLICATE_PLATFORM': { label: 'Duplicate Plt', bg: 'bg-purple-50 text-purple-700 border-purple-200', icon: Copy },
  'DUPLICATE_BANK': { label: 'Duplicate Bnk', bg: 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200', icon: Copy },
  'UNMATCHED_REFUND': { label: 'Unmatched Refund', bg: 'bg-rose-50 text-rose-700 border-rose-200', icon: RotateCcw },
  'UNMATCHED_PLATFORM': { label: 'Unsettled Plt', bg: 'bg-orange-50 text-orange-700 border-orange-200', icon: AlertTriangle },
  'UNMATCHED_BANK': { label: 'Unclaimed Bnk', bg: 'bg-slate-100 text-slate-700 border-slate-300', icon: AlertTriangle },
  'MANUAL_REVIEW': { label: 'Manual Review', bg: 'bg-yellow-50 text-yellow-700 border-yellow-200', icon: HelpCircle },
  'SUGGESTED_MATCH': { label: 'Suggested Match', bg: 'bg-indigo-50 text-indigo-700 border-indigo-200', icon: ArrowUpRight },
  'CURRENCY_MISMATCH': { label: 'Currency Mismatch', bg: 'bg-red-50 text-red-700 border-red-200', icon: AlertTriangle },
  'AMOUNT_MISMATCH': { label: 'Amount Mismatch', bg: 'bg-red-50 text-red-700 border-red-200', icon: AlertTriangle },
};

export default function ReconciliationTable({ records, onExportCsv }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const rowsPerPage = 15;

  const filteredRecords = useMemo(() => {
    if (!records) return [];

    return records.filter((row) => {
      // Source filter
      if (sourceFilter !== 'ALL' && row.source !== sourceFilter) return false;

      // Status filter
      if (statusFilter !== 'ALL') {
        if (statusFilter === 'MATCHED' && !row.status.startsWith('MATCHED')) return false;
        if (statusFilter === 'DISCREPANCY' && row.status.startsWith('MATCHED')) return false;
        if (statusFilter === 'TIMING' && row.status !== 'TIMING_DIFFERENCE') return false;
        if (statusFilter === 'ROUNDING' && row.status !== 'ROUNDING_DIFFERENCE') return false;
        if (statusFilter === 'DUPLICATE' && !row.status.includes('DUPLICATE')) return false;
        if (statusFilter === 'REFUND' && row.status !== 'UNMATCHED_REFUND' && row.status !== 'MATCHED_REFUND') return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchId = (row.record_id || '').toLowerCase().includes(q);
        const matchOrder = (row.order_id || '').toLowerCase().includes(q);
        const matchCounterpart = (row.matched_record_id || '').toLowerCase().includes(q);
        const matchExpl = (row.explanation || '').toLowerCase().includes(q);
        const matchBatch = (row.batch_id || '').toLowerCase().includes(q);
        if (!matchId && !matchOrder && !matchCounterpart && !matchExpl && !matchBatch) return false;
      }

      return true;
    });
  }, [records, searchQuery, statusFilter, sourceFilter]);

  const totalPages = Math.ceil(filteredRecords.length / rowsPerPage) || 1;
  const paginatedRecords = filteredRecords.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header & Controls */}
      <div className="p-5 border-b border-slate-200 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-800">100% Accounted Reconciliation Ledger</h2>
            <p className="text-xs text-slate-500">
              Showing {filteredRecords.length} of {records?.length || 0} total input ledger rows
            </p>
          </div>
          <button
            onClick={onExportCsv}
            className="flex items-center space-x-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm transition cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export Audit CSV Report</span>
          </button>
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Bar */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by ID, Order, Batch, Counterpart..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Source Filter */}
          <select
            value={sourceFilter}
            onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
            className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Sources</option>
            <option value="PLATFORM">Platform Ledger</option>
            <option value="BANK">Bank Settlements</option>
          </select>

          {/* Status Quick Filter Chips */}
          <div className="flex items-center flex-wrap gap-1.5 text-xs">
            {[
              { id: 'ALL', label: 'All' },
              { id: 'MATCHED', label: 'Matched' },
              { id: 'DISCREPANCY', label: 'Discrepancies' },
              { id: 'TIMING', label: 'Timing' },
              { id: 'ROUNDING', label: 'Rounding' },
              { id: 'DUPLICATE', label: 'Duplicates' },
              { id: 'REFUND', label: 'Refunds' },
            ].map((chip) => (
              <button
                key={chip.id}
                onClick={() => { setStatusFilter(chip.id); setPage(1); }}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition cursor-pointer ${
                  statusFilter === chip.id
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {chip.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <th className="py-3 px-3">Source</th>
              <th className="py-3 px-3">Record ID</th>
              <th className="py-3 px-3">Order / Ref</th>
              <th className="py-3 px-3">Date</th>
              <th className="py-3 px-3 text-right">Amount (₹)</th>
              <th className="py-3 px-3">Counterpart</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Variance (₹)</th>
              <th className="py-3 px-4">Audit Explanation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-normal text-slate-700">
            {paginatedRecords.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-400">
                  No records match the current filter criteria.
                </td>
              </tr>
            ) : (
              paginatedRecords.map((row) => {
                const badge = STATUS_BADGES[row.status] || {
                  label: row.status,
                  bg: 'bg-slate-100 text-slate-700 border-slate-200',
                  icon: HelpCircle
                };
                const IconComponent = badge.icon;

                return (
                  <tr key={row.id} className="hover:bg-slate-50/80 transition">
                    {/* Source */}
                    <td className="py-3 px-3 font-semibold">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        row.source === 'PLATFORM' 
                          ? 'bg-blue-100 text-blue-700' 
                          : 'bg-indigo-100 text-indigo-700'
                      }`}>
                        {row.source}
                      </span>
                    </td>

                    {/* Record ID */}
                    <td className="py-3 px-3 font-mono font-medium text-slate-900">
                      {row.record_id}
                    </td>

                    {/* Order / Ref */}
                    <td className="py-3 px-3 font-mono text-slate-500">
                      {row.order_id || '—'}
                    </td>

                    {/* Date */}
                    <td className="py-3 px-3 text-slate-600 whitespace-nowrap">
                      {row.date ? row.date.split('T')[0] : '—'}
                    </td>

                    {/* Amount */}
                    <td className="py-3 px-3 text-right font-mono font-semibold text-slate-900 whitespace-nowrap">
                      ₹{row.amount}
                      {row.fee_amount && row.fee_amount !== '0.00' && (
                        <span className="block text-[10px] text-slate-400 font-normal">
                          Fee: ₹{row.fee_amount}
                        </span>
                      )}
                    </td>

                    {/* Counterpart */}
                    <td className="py-3 px-3 font-mono text-slate-600 text-[11px]">
                      {row.matched_record_id || '—'}
                    </td>

                    {/* Status Badge */}
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${badge.bg}`}>
                        <IconComponent className="w-3 h-3" />
                        <span>{badge.label}</span>
                      </span>
                    </td>

                    {/* Variance Amount */}
                    <td className={`py-3 px-3 text-right font-mono font-semibold whitespace-nowrap ${
                      row.difference_amount && row.difference_amount !== '0.00' 
                        ? 'text-rose-600' 
                        : 'text-slate-400'
                    }`}>
                      {row.difference_amount && row.difference_amount !== '0.00' ? `₹${row.difference_amount}` : '—'}
                    </td>

                    {/* Explanation */}
                    <td className="py-3 px-4 text-xs text-slate-600 max-w-sm">
                      <p className="line-clamp-2" title={row.explanation}>
                        {row.explanation}
                      </p>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
        <div>
          Page <span className="font-semibold text-slate-700">{page}</span> of <span className="font-semibold text-slate-700">{totalPages}</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-white border border-slate-300 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100"
          >
            Previous
          </button>
          <button
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page === totalPages}
            className="px-3 py-1 bg-white border border-slate-300 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

