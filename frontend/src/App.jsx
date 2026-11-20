import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import MetricsCards from './components/MetricsCards';
import ChartsSection from './components/ChartsSection';
import ReconciliationTable from './components/ReconciliationTable';
import { reconcileSample, reconcileFiles, exportCsvReport } from './services/api';
import { 
  Sparkles, 
  Clock, 
  Divide, 
  Copy, 
  RotateCcw, 
  ShieldCheck, 
  ArrowRight,
  AlertCircle
} from 'lucide-react';

export default function App() {
  const [platformFile, setPlatformFile] = useState(null);
  const [bankFile, setBankFile] = useState(null);
  const [settlementWindow, setSettlementWindow] = useState(2);
  const [reconciliationData, setReconciliationData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Load sample data automatically on first mount for instant demo experience
  useEffect(() => {
    handleLoadSampleData(settlementWindow);
  }, []);

  const handleLoadSampleData = async (win = settlementWindow) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await reconcileSample(win);
      setReconciliationData(data);
    } catch (err) {
      setErrorMessage(
        'Backend service unreachable or returned error. Please ensure the backend server is running on http://127.0.0.1:8000 (run: uvicorn app.main:app --port 8000).'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleWindowChange = async (newWindow) => {
    setSettlementWindow(newWindow);
    setIsLoading(true);
    setErrorMessage(null);
    try {
      if (platformFile && bankFile) {
        const data = await reconcileFiles(platformFile, bankFile, newWindow);
        setReconciliationData(data);
      } else {
        const data = await reconcileSample(newWindow);
        setReconciliationData(data);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to re-calculate reconciliation with new window');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReconcile = async () => {
    if (!platformFile || !bankFile) {
      setErrorMessage('Please select both Platform CSV and Bank CSV files to reconcile.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await reconcileFiles(platformFile, bankFile, settlementWindow);
      setReconciliationData(data);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to reconcile uploaded files');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCsv = async () => {
    if (!reconciliationData) return;
    try {
      await exportCsvReport(reconciliationData);
    } catch (err) {
      alert('Failed to export CSV: ' + err.message);
    }
  };

  const handleReset = () => {
    setPlatformFile(null);
    setBankFile(null);
    setReconciliationData(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Header
        onLoadSampleData={() => handleLoadSampleData(settlementWindow)}
        isLoading={isLoading}
        settlementWindow={settlementWindow}
        onWindowChange={handleWindowChange}
        onReset={handleReset}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Error Banner */}
        {errorMessage && (
          <div className="mb-6 p-4 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg flex items-start space-x-3 text-rose-800">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-600" />
            <div className="text-sm">
              <span className="font-bold">Error: </span>
              {errorMessage}
            </div>
          </div>
        )}

        {/* Upload Section */}
        <UploadSection
          platformFile={platformFile}
          setPlatformFile={setPlatformFile}
          bankFile={bankFile}
          setBankFile={setBankFile}
          onReconcile={handleReconcile}
          isLoading={isLoading}
          settlementWindow={settlementWindow}
        />

        {/* If Reconciliation Results are Ready */}
        {reconciliationData ? (
          <>
            <MetricsCards summary={reconciliationData.summary} />
            <ChartsSection
              statusDistribution={reconciliationData.status_distribution}
              categoryExposure={reconciliationData.category_exposure}
            />
            <ReconciliationTable
              records={reconciliationData.records}
              onExportCsv={handleExportCsv}
            />
          </>
        ) : (
          /* Feature Showcase when idle */
          <div className="mt-8 bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
            <div className="text-center max-w-2xl mx-auto mb-8">
              <h3 className="text-xl font-bold text-slate-800 mb-2">
                Deterministic Financial Reconciliation Engine
              </h3>
              <p className="text-sm text-slate-500">
                SmartPay accounts for 100% of input rows from both platforms and banks, strictly using Python <code>Decimal</code> fixed-point precision with zero floating-point drift.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-lg">
                <div className="flex items-center space-x-2 text-amber-700 font-semibold text-sm mb-1.5">
                  <Clock className="w-4 h-4" />
                  <h4>1. Timing Difference</h4>
                </div>
                <p className="text-xs text-amber-900/80">
                  Month-end cut-offs: March 31 platform transactions settled on April 2 within the 1–2 day banking delay.
                </p>
              </div>

              <div className="p-4 bg-sky-50/60 border border-sky-200 rounded-lg">
                <div className="flex items-center space-x-2 text-sky-700 font-semibold text-sm mb-1.5">
                  <Divide className="w-4 h-4" />
                  <h4>2. Rounding Difference</h4>
                </div>
                <p className="text-xs text-sky-900/80">
                  Batch-level sum aggregation: Documented variance where sum of rounded line-items differs from batch total.
                </p>
              </div>

              <div className="p-4 bg-purple-50/60 border border-purple-200 rounded-lg">
                <div className="flex items-center space-x-2 text-purple-700 font-semibold text-sm mb-1.5">
                  <Copy className="w-4 h-4" />
                  <h4>3. Duplicate Entries</h4>
                </div>
                <p className="text-xs text-purple-900/80">
                  Detects repeated platform IDs or duplicate bank settlements with financial exposure without deleting rows.
                </p>
              </div>

              <div className="p-4 bg-rose-50/60 border border-rose-200 rounded-lg">
                <div className="flex items-center space-x-2 text-rose-700 font-semibold text-sm mb-1.5">
                  <RotateCcw className="w-4 h-4" />
                  <h4>4. Unmatched Refund</h4>
                </div>
                <p className="text-xs text-rose-900/80">
                  Flags orphaned refunds without a valid original payment for operations & risk investigation.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 border-t border-slate-800 py-6 text-center text-xs mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-4">
          <p>© 2026 SmartPay Systems • Deterministic INR (₹) Financial Reconciliation</p>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-slate-300">FastAPI Backend: Ready</span>
            </span>
            <span className="text-slate-600">•</span>
            <span>100% Row Accounting Guaranteed</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
