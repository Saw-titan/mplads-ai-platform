import React, { useEffect, useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  IndianRupee,
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  TrendingUp,
  PieChart as PieIcon,
  BarChart3,
  MapPin,
  Flame,
  Camera,
  GitCompare,
  ClipboardList,
  Eye,
  Copy,
  CalendarClock,
  CheckCircle2,
  Layers,
  Sliders
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area,
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import StatCard from '../components/StatCard';
import { getKPIs, getTop5PercentWorks, getFlaggedAnomalies } from '../services/api';

const SEV_COLORS = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b', LOW: '#10b981' };

const roleLabel = (role) => {
  if (role === 'DISTRICT_OFFICER') return 'District Authority View';
  if (role === 'AUDITOR') return 'Independent Forensic Audit View';
  return 'MoSPI Central Command';
};

const Dashboard = () => {
  const { activeRole, refreshKey } = useOutletContext();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [top5, setTop5] = useState([]);
  const [scatterData, setScatterData] = useState([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const [kpis, queue, anomalies] = await Promise.all([
          getKPIs(),
          getTop5PercentWorks(),
          getFlaggedAnomalies({ limit: 80 })
        ]);
        setData(kpis);
        let queueRows = queue || [];
        if (activeRole === 'DISTRICT_OFFICER') {
          queueRows = queueRows.filter((p) => p.district_name === 'Varanasi');
        }
        setTop5(queueRows.slice(0, 8));
        const scatter = (anomalies || []).slice(0, 60).map((p) => ({
          name: p.project_code,
          payment: Number(p.payment_progress || 0),
          physical: Number(p.physical_progress || 0),
          severity: p.severity,
          fill: SEV_COLORS[p.severity] || '#06b6d4'
        }));
        setScatterData(scatter);
      } catch (err) {
        console.error('Failed to load dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [refreshKey, activeRole]);

  if (loading) {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-400">Loading MPLADS Forensic Analytics...</p>
      </div>
    );
  }

  const formatCurrencyCrores = (val) => `₹${(val / 10000000).toFixed(2)} Cr`;
  const severityDonut = (data.severity_distribution || []).map((s) => ({
    ...s,
    fill: SEV_COLORS[s.severity] || '#64748b'
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-950 text-cyan-400 border border-cyan-800 uppercase tracking-wide">
              {roleLabel(activeRole)}
            </span>
            <span className="text-xs text-slate-500">Updated Real-Time</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white mt-1 tracking-tight">Executive Analytics Dashboard</h2>
          <p className="text-xs text-slate-400">Forensic risk assessment for MPLADS works — anomaly indicators requiring review, not confirmed irregularity findings.</p>
        </div>
      </div>

      <button
        onClick={() => navigate('/audit?top_5_percent=true')}
        className="w-full text-left glass-card p-4 rounded-2xl border border-red-800/70 bg-gradient-to-r from-red-950/50 to-slate-950 flex items-center justify-between gap-4 hover:border-red-600 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-red-950 text-red-400 border border-red-800">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Top 5% Priority Audit Queue</h3>
            <p className="text-[11px] text-slate-400">
              {data.top_5_percent_count} highest-risk works require review ({data.critical_projects_count} CRITICAL, {data.high_risk_projects_count} HIGH).
            </p>
          </div>
        </div>
        <span className="text-xs font-bold text-red-300 px-3 py-1.5 rounded-lg bg-red-950 border border-red-800">Open Queue →</span>
      </button>

      {/* 11 Core Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Projects"
          value={data.total_projects}
          subtext={`Portfolio outlay ${formatCurrencyCrores(data.total_sanctioned_funds)}`}
          icon={Layers}
          color="cyan"
        />
        <StatCard
          title="Critical Projects"
          value={data.critical_projects_count}
          subtext="SIH Composite Score 85–100"
          icon={ShieldAlert}
          color="red"
          isAlert={true}
        />
        <StatCard
          title="High-Risk Projects"
          value={data.high_risk_projects_count}
          subtext="SIH Composite Score 70–84"
          icon={AlertTriangle}
          color="orange"
        />
        <StatCard
          title="Top 5% Priority Projects"
          value={data.top_5_percent_count}
          subtext="Immediate forensic triage queue"
          icon={Flame}
          color="red"
        />
        <StatCard
          title="Payment-Progress Mismatch"
          value={data.payment_mismatch_count}
          subtext="Works with ≥25% progress gap"
          icon={GitCompare}
          color="amber"
        />
        <StatCard
          title="Geospatial Anomalies"
          value={data.geospatial_anomaly_count}
          subtext="Haversine distance > 500m"
          icon={MapPin}
          color="orange"
        />
        <StatCard
          title="Duplicate Evidence"
          value={data.duplicate_evidence_count}
          subtext="Re-used SHA-256 photo hashes"
          icon={Camera}
          color="violet"
        />
        <StatCard
          title="Duplicate Projects"
          value={data.duplicate_project_count}
          subtext="Semantic overlap score ≥ 70%"
          icon={Copy}
          color="violet"
        />
        <StatCard
          title="Timeline Delays"
          value={data.timeline_delay_count}
          subtext="Significant milestone variance"
          icon={CalendarClock}
          color="amber"
        />
        <StatCard
          title="Cases Under Review"
          value={data.cases_under_review_count}
          subtext="Active field / desk clarification"
          icon={ClipboardList}
          color="cyan"
        />
        <StatCard
          title="Cases Resolved"
          value={data.cases_resolved_count}
          subtext="Cleared through HITL workflow"
          icon={CheckCircle2}
          color="emerald"
        />
        <StatCard
          title="Flagged Expenditure Outlay"
          value={formatCurrencyCrores(data.suspended_fraud_value)}
          subtext={`${data.high_risk_ratio}% portfolio requiring review`}
          icon={IndianRupee}
          color="red"
        />
      </div>

      <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-red-950/60 border border-red-800/50 text-red-400">
              <Flame className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Top 5% Priority Audit Queue</h3>
              <p className="text-[11px] text-slate-400">Dynamic highest composite SIH risk scores</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/audit?top_5_percent=true')}
            className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300"
          >
            View all
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2 pr-3">Code</th>
                <th className="py-2 pr-3">Title</th>
                <th className="py-2 pr-3">District</th>
                <th className="py-2 pr-3">Severity</th>
                <th className="py-2 pr-3">Risk</th>
                <th className="py-2 pr-3">Mismatch</th>
                <th className="py-2">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {top5.map((p) => (
                <tr key={p.id} className="hover:bg-slate-900/40">
                  <td className="py-2.5 pr-3 font-mono text-cyan-400">{p.project_code}</td>
                  <td className="py-2.5 pr-3 max-w-xs truncate text-slate-100">{p.title}</td>
                  <td className="py-2.5 pr-3">{p.district_name}</td>
                  <td className="py-2.5 pr-3">
                    <span
                      className="px-2 py-0.5 rounded-full text-[10px] font-bold border"
                      style={{ color: SEV_COLORS[p.severity], borderColor: SEV_COLORS[p.severity] }}
                    >
                      {p.severity}
                    </span>
                  </td>
                  <td className="py-2.5 pr-3 font-bold">{Number(p.risk_score).toFixed(1)}</td>
                  <td className="py-2.5 pr-3">{Number(p.progress_mismatch).toFixed(1)}%</td>
                  <td className="py-2.5">
                    <button
                      onClick={() => navigate(`/audit?id=${p.id}`)}
                      className="inline-flex items-center gap-1 text-cyan-400 font-semibold"
                    >
                      <Eye className="w-3.5 h-3.5" /> Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-red-950/60 border border-red-800/50 text-red-400">
              <PieIcon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Risk Severity Distribution</h3>
              <p className="text-[11px] text-slate-400">LOW 0–39 · MEDIUM 40–69 · HIGH 70–84 · CRITICAL 85–100</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={severityDonut} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={5} dataKey="count" nameKey="severity">
                  {severityDonut.map((entry, index) => (
                    <Cell key={`sev-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Legend formatter={(value) => <span className="text-xs text-slate-300 font-medium">{value}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">SIH Risk Factor Distribution</h3>
              <p className="text-[11px] text-slate-400">Average normalized score by formula component across portfolio</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.risk_factor_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="factor" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="score" name="Avg Factor Score" radius={[4, 4, 0, 0]}>
                  {(data.risk_factor_distribution || []).map((entry, index) => (
                    <Cell key={`fact-${index}`} fill={entry.fill || '#06b6d4'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-800/50 text-amber-400">
              <GitCompare className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Payment vs Physical Progress</h3>
              <p className="text-[11px] text-slate-400">Scatter of disbursement % against verified physical %</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" dataKey="physical" name="Physical %" domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis type="number" dataKey="payment" name="Payment %" domain={[0, 120]} stroke="#64748b" tick={{ fontSize: 10 }} />
                <ZAxis range={[40, 40]} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Scatter name="Works" data={scatterData} fill="#06b6d4">
                  {scatterData.map((entry, index) => (
                    <Cell key={`pt-${index}`} fill={entry.fill} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-800/50 text-amber-400">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">District Anomaly Rankings</h3>
              <p className="text-[11px] text-slate-400">Average composite risk score by district</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={data.district_risk_rankings} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} domain={[0, 100]} />
                <YAxis dataKey="district" type="category" stroke="#64748b" tick={{ fontSize: 11 }} width={90} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="risk_score" name="Avg Risk Score" fill="#f59e0b" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800/50 text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Monthly Fund Flow & Anomaly Trends</h3>
              <p className="text-[11px] text-slate-400">Disbursement (₹ Lakhs) vs flagged incidents</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.monthly_fund_flow} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="disbursement" name="Disbursement (₹ Lakhs)" stroke="#06b6d4" fillOpacity={0.2} fill="#06b6d4" />
                <Area type="monotone" dataKey="anomalies" name="Flagged Anomalies" stroke="#ef4444" fillOpacity={0.2} fill="#ef4444" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800/80 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Sector Cost Variance (₹ Crores)</h3>
              <p className="text-[11px] text-slate-400">Sanctioned budget vs actual expenditure</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.category_variance} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="category" stroke="#64748b" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="sanctioned" name="Sanctioned (₹ Cr)" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expenditure" name="Expenditure (₹ Cr)" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
