import React, { useRef } from 'react';
import { Upload, FileText, CheckCircle2, Download, ArrowRight, AlertTriangle } from 'lucide-react';
import { downloadSampleFile } from '../services/api';

export default function UploadSection({
  platformFile,
  setPlatformFile,
  bankFile,
  setBankFile,
  onReconcile,
  isLoading,
  settlementWindow
}) {
  const platformInputRef = useRef(null);
  const bankInputRef = useRef(null);

  const handleFileChange = (e, setFile) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
      <div className="flex flex-wrap items-center justify-between pb-4 mb-6 border-b border-slate-100 gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">CSV Ledger Ingestion</h2>
          <p className="text-sm text-slate-500">
            Upload your platform transaction log and acquiring bank settlement statement (INR ₹)
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400 font-medium">Download Templates:</span>
          <button
            onClick={() => downloadSampleFile('platform')}
            className="flex items-center space-x-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition border border-slate-200"
          >
            <Download className="w-3 h-3 text-slate-500" />
            <span>Platform CSV</span>
          </button>
          <button
            onClick={() => downloadSampleFile('bank')}
            className="flex items-center space-x-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition border border-slate-200"
          >
            <Download className="w-3 h-3 text-slate-500" />
            <span>Bank CSV</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Platform CSV Upload Box */}
        <div
          onClick={() => platformInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
            platformFile
              ? 'border-blue-500 bg-blue-50/40'
              : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
          }`}
        >
          <input
            type="file"
            ref={platformInputRef}
            onChange={(e) => handleFileChange(e, setPlatformFile)}
            accept=".csv"
            className="hidden"
          />
          <div className="flex flex-col items-center">
            {platformFile ? (
              <>
                <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-3">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">{platformFile.name}</h3>
                <p className="text-xs text-slate-500 mb-2">{(platformFile.size / 1024).toFixed(1)} KB • CSV Document</p>
                <span className="text-xs text-blue-600 hover:underline">Click to change file</span>
              </>
            ) : (
              <>
                <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">1. Platform Transactions CSV</h3>
                <p className="text-xs text-slate-500 mb-2">
                  Drop CSV file here or click to browse
                </p>
                <span className="text-[11px] text-slate-400">
                  Headers: transaction_id, order_id, amount, currency, timestamp...
                </span>
              </>
            )}
          </div>
        </div>

        {/* Bank CSV Upload Box */}
        <div
          onClick={() => bankInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
            bankFile
              ? 'border-indigo-500 bg-indigo-50/40'
              : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'
          }`}
        >
          <input
            type="file"
            ref={bankInputRef}
            onChange={(e) => handleFileChange(e, setBankFile)}
            accept=".csv"
            className="hidden"
          />
          <div className="flex flex-col items-center">
            {bankFile ? (
              <>
                <div className="w-12 h-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-3">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">{bankFile.name}</h3>
                <p className="text-xs text-slate-500 mb-2">{(bankFile.size / 1024).toFixed(1)} KB • CSV Document</p>
                <span className="text-xs text-indigo-600 hover:underline">Click to change file</span>
              </>
            ) : (
              <>
                <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">2. Bank Settlements CSV</h3>
                <p className="text-xs text-slate-500 mb-2">
                  Drop CSV file here or click to browse
                </p>
                <span className="text-[11px] text-slate-400">
                  Headers: settlement_id, platform_trx_id, gross_amount, fee_amount, net_amount...
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="mt-6 flex flex-wrap items-center justify-between pt-4 border-t border-slate-100 gap-4">
        <div className="text-xs text-slate-500 flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span>Validates headers, ISO timestamps, decimal precision and checks: net = gross - fee</span>
          </div>
          {settlementWindow && (
            <span className="bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded border border-blue-200 text-[11px]">
              Active Rule: T+{settlementWindow} Days Clearing Lag
            </span>
          )}
        </div>
        <button
          onClick={onReconcile}
          disabled={!platformFile || !bankFile || isLoading}
          className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold px-6 py-2.5 rounded-lg text-sm shadow transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <span>{isLoading ? 'Reconciling Ledger...' : 'Run Deterministic Reconciliation'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

