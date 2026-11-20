import React from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip, 
  Legend, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid 
} from 'recharts';

const STATUS_COLORS = {
  'Matched Exact': '#10b981',        // Emerald
  'Matched Partial': '#059669',      // Dark emerald
  'Matched Refund': '#14b8a6',       // Teal
  'Timing Difference': '#f59e0b',    // Amber
  'Rounding Difference': '#0284c7',  // Sky blue
  'Duplicate Platform': '#a855f7',   // Purple
  'Duplicate Bank': '#9333ea',       // Deep Purple
  'Unmatched Refund': '#ef4444',     // Red
  'Unmatched Platform': '#f97316',   // Orange
  'Unmatched Bank': '#64748b',       // Slate
  'Manual Review': '#eab308'         // Yellow
};

export default function ChartsSection({ statusDistribution, categoryExposure }) {
  if (!statusDistribution) return null;

  // Format data for status distribution pie chart
  const pieData = Object.entries(statusDistribution)
    .filter(([_, count]) => count > 0)
    .map(([status, count]) => ({
      name: status,
      value: count,
      color: STATUS_COLORS[status] || '#94a3b8'
    }));

  // Format data for financial exposure bar chart
  const barData = Object.entries(categoryExposure || {})
    .filter(([_, amount]) => parseFloat(amount) > 0)
    .map(([category, amount]) => ({
      name: category,
      exposure: parseFloat(amount)
    }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {/* Status Distribution Pie/Donut Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h3 className="text-base font-bold text-slate-800 mb-1">Reconciliation Status Breakdown</h3>
        <p className="text-xs text-slate-500 mb-4">Total records mapped by deterministic category</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={3}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value, name) => [`${value} records`, name]}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={36} 
                iconType="circle"
                wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Financial Exposure by Category Bar Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h3 className="text-base font-bold text-slate-800 mb-1">Financial Exposure by Discrepancy Category</h3>
        <p className="text-xs text-slate-500 mb-4">Monetary volume & risk in INR (₹)</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={barData}
              margin={{ top: 10, right: 20, left: 20, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 10, fill: '#64748b' }} 
                interval={0}
                angle={-15}
                textAnchor="end"
              />
              <YAxis 
                tick={{ fontSize: 10, fill: '#64748b' }} 
                tickFormatter={(val) => `₹${val}`}
              />
              <Tooltip 
                formatter={(val) => [`₹${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, 'Financial Impact']}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Bar dataKey="exposure" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

