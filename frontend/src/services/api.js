const API_BASE = '/api';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function reconcileSample(settlementWindow = 2) {
  const res = await fetch(`${API_BASE}/reconcile-sample?settlement_window=${settlementWindow}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail?.message || errorData.detail || 'Reconciliation failed');
  }
  return res.json();
}

export async function reconcileFiles(platformFile, bankFile, settlementWindow = 2) {
  const formData = new FormData();
  formData.append('platform_file', platformFile);
  formData.append('bank_file', bankFile);
  formData.append('settlement_window', settlementWindow.toString());

  const res = await fetch(`${API_BASE}/reconcile`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json();
    const errMsg = typeof errorData.detail === 'object' 
      ? JSON.stringify(errorData.detail) 
      : (errorData.detail || 'Reconciliation request failed');
    throw new Error(errMsg);
  }
  return res.json();
}

export function downloadSampleFile(type) {
  window.open(`${API_BASE}/sample-data/${type}.csv`, '_blank');
}

export async function exportCsvReport(reconciliationResponse) {
  const res = await fetch(`${API_BASE}/export-csv`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(reconciliationResponse),
  });

  if (!res.ok) {
    throw new Error('Failed to generate CSV export');
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `SmartPay_Reconciliation_Report_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}

