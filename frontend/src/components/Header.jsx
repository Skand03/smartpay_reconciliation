import React from 'react';
import { ShieldCheck, Sparkles, SlidersHorizontal, RefreshCw } from 'lucide-react';

export default function Header({ 
  onLoadSampleData, 
  isLoading, 
  settlementWindow, 
  onWindowChange,
  onReset
}) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 p-2 rounded-lg text-white shadow-sm">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">SmartPay</h1>
              <span className="text-xs bg-blue-500/20 text-blue-300 font-semibold px-2 py-0.5 rounded-full border border-blue-400/30">
                INR (₹) Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">Deterministic Financial Reconciliation & Audit System</p>
          </div>
        </div>

        {/* Controls & Quick Actions */}
        <div className="flex items-center flex-wrap gap-3">
          {/* Settlement Window Config */}
          <div className="flex items-center space-x-2 bg-slate-800/90 px-3 py-1.5 rounded-lg border border-slate-700 text-xs shadow-inner">
            <SlidersHorizontal className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-300 font-medium">Settlement Lag Window:</span>
            <select
              value={settlementWindow}
              onChange={(e) => onWindowChange(Number(e.target.value))}
              disabled={isLoading}
              className="bg-slate-900 text-white font-semibold px-2.5 py-1 rounded border border-blue-500/50 hover:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer text-xs"
            >
              <option value={1}>1 Day (T+1)</option>
              <option value={2}>2 Days (Default T+2)</option>
              <option value={3}>3 Days (T+3)</option>
              <option value={5}>5 Days (T+5)</option>
            </select>
          </div>

          {/* Reset */}
          <button
            onClick={onReset}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition cursor-pointer"
            title="Reset All"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Load Sample Data Button */}
          <button
            onClick={onLoadSampleData}
            disabled={isLoading}
            className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-yellow-300" />
            <span>{isLoading ? 'Running Engine...' : 'Load Realistic Sample Data'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}

