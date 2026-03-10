import { useState, useEffect, useCallback } from "react";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend, LineChart, Line, ReferenceLine
} from "recharts";

// ── Styles ──────────────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0c10;
    --surface: #111318;
    --surface2: #181c23;
    --border: #1e2330;
    --accent: #e8c840;
    --accent2: #3de8b0;
    --accent3: #e8503d;
    --text: #e2e8f0;
    --muted: #64748b;
    --font-display: 'Syne', sans-serif;
    --font-mono: 'DM Mono', monospace;
  }

  body { background: var(--bg); color: var(--text); font-family: var(--font-display); }

  .app {
    min-height: 100vh;
    background: var(--bg);
    background-image:
      radial-gradient(ellipse 80% 50% at 20% 10%, rgba(232,200,64,0.06) 0%, transparent 60%),
      radial-gradient(ellipse 60% 40% at 80% 80%, rgba(61,232,176,0.04) 0%, transparent 60%);
  }

  /* Header */
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 24px 40px;
    border-bottom: 1px solid var(--border);
    background: rgba(17,19,24,0.8);
    backdrop-filter: blur(12px);
    position: sticky; top: 0; z-index: 100;
  }
  .header-left { display: flex; align-items: center; gap: 14px; }
  .logo-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 12px var(--accent);
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
  .header-title { font-size: 18px; font-weight: 800; letter-spacing: -0.5px; }
  .header-title span { color: var(--accent); }
  .header-badge {
    font-family: var(--font-mono); font-size: 11px;
    background: rgba(232,200,64,0.12); color: var(--accent);
    border: 1px solid rgba(232,200,64,0.25);
    padding: 4px 10px; border-radius: 4px;
  }
  .price-pill {
    font-family: var(--font-mono); font-size: 13px; font-weight: 500;
    padding: 8px 16px; border-radius: 6px;
    background: rgba(61,232,176,0.08); color: var(--accent2);
    border: 1px solid rgba(61,232,176,0.2);
    display: flex; align-items: center; gap: 8px;
  }
  .price-pill .dot { width:6px;height:6px;border-radius:50%;background:var(--accent2); }

  /* Layout */
  .main { padding: 32px 40px; max-width: 1400px; margin: 0 auto; }

  /* Form Panel */
  .form-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 32px;
  }
  .form-panel-title {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: var(--muted);
    margin-bottom: 20px;
  }
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr auto;
    gap: 16px; align-items: end;
  }
  .field { display: flex; flex-direction: column; gap: 8px; }
  .field label {
    font-size: 11px; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; color: var(--muted);
  }
  .field input, .field select {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    width: 100%;
  }
  .field input:focus, .field select:focus {
    border-color: rgba(232,200,64,0.5);
    box-shadow: 0 0 0 3px rgba(232,200,64,0.08);
  }
  .field input::placeholder { color: var(--muted); }
  .field input[type="password"] { letter-spacing: 2px; }

  .btn {
    padding: 10px 24px; border-radius: 8px;
    font-family: var(--font-display); font-size: 13px; font-weight: 700;
    letter-spacing: 0.5px; cursor: pointer; border: none;
    transition: all 0.2s; white-space: nowrap;
  }
  .btn-primary {
    background: var(--accent); color: #0a0c10;
  }
  .btn-primary:hover { background: #f5d840; transform: translateY(-1px); box-shadow: 0 4px 20px rgba(232,200,64,0.3); }
  .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

  /* KPI Cards */
  .kpi-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 16px; margin-bottom: 32px;
  }
  .kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative; overflow: hidden;
  }
  .kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  }
  .kpi-card.yellow::before { background: var(--accent); }
  .kpi-card.green::before { background: var(--accent2); }
  .kpi-card.red::before { background: var(--accent3); }
  .kpi-card.blue::before { background: #5b8dee; }
  .kpi-label { font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
  .kpi-value { font-family: var(--font-mono); font-size: 28px; font-weight: 500; letter-spacing: -1px; }
  .kpi-value.yellow { color: var(--accent); }
  .kpi-value.green { color: var(--accent2); }
  .kpi-value.red { color: var(--accent3); }
  .kpi-value.blue { color: #5b8dee; }
  .kpi-sub { font-size: 11px; color: var(--muted); margin-top: 6px; font-family: var(--font-mono); }

  /* Chart Grid */
  .chart-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }
  .chart-grid-3 {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }
  .chart-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
  }
  .chart-title {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: var(--muted);
    margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .chart-title-tag {
    font-size: 10px; padding: 2px 8px; border-radius: 3px;
    background: rgba(232,200,64,0.1); color: var(--accent);
  }

  /* Table */
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead tr { border-bottom: 1px solid var(--border); }
  th {
    text-align: left; padding: 10px 14px;
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--muted);
  }
  td { padding: 12px 14px; font-family: var(--font-mono); font-size: 12px; border-bottom: 1px solid rgba(30,35,48,0.6); }
  tr:hover td { background: rgba(255,255,255,0.02); }
  .risk-bar-wrap { display: flex; align-items: center; gap: 10px; }
  .risk-bar-bg { flex: 1; height: 5px; background: rgba(255,255,255,0.06); border-radius: 3px; }
  .risk-bar-fill { height: 100%; border-radius: 3px; }

  /* Tooltip */
  .custom-tooltip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    font-family: var(--font-mono);
    font-size: 12px;
  }
  .custom-tooltip .tt-label { color: var(--accent); font-weight: 600; margin-bottom: 6px; }
  .custom-tooltip .tt-row { color: var(--muted); }
  .custom-tooltip .tt-row span { color: var(--text); }

  /* Status */
  .status-bar {
    display: flex; align-items: center; gap: 8px;
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
    margin-top: 8px;
  }
  .status-dot { width:6px;height:6px;border-radius:50%; }
  .status-dot.live { background:var(--accent2); box-shadow:0 0 6px var(--accent2); }
  .status-dot.fallback { background:var(--accent); }

  /* Responsive */
  @media (max-width: 900px) {
    .form-grid { grid-template-columns: 1fr 1fr; }
    .kpi-grid { grid-template-columns: 1fr 1fr; }
    .chart-grid, .chart-grid-3 { grid-template-columns: 1fr; }
    .main { padding: 20px; }
    .header { padding: 16px 20px; }
  }
`;

// ── Data ─────────────────────────────────────────────────────────────────────
const BASE_MARKET_DATA = [
  { country: "Congo (DRC)", share: 72.0, political: 0.92, ethical: 0.88, regulatory: 0.80 },
  { country: "Indonesia",   share: 14.5, political: 0.55, ethical: 0.40, regulatory: 0.35 },
  { country: "China",       share:  1.2, political: 0.65, ethical: 0.50, regulatory: 0.75 },
  { country: "Russia",      share:  2.8, political: 0.98, ethical: 0.45, regulatory: 0.90 },
  { country: "Australia",   share:  2.5, political: 0.15, ethical: 0.05, regulatory: 0.20 },
  { country: "Mexico",      share:  0.5, political: 0.40, ethical: 0.30, regulatory: 0.25 },
  { country: "Canada",      share:  1.5, political: 0.10, ethical: 0.05, regulatory: 0.15 },
  { country: "Philippines", share:  1.8, political: 0.50, ethical: 0.35, regulatory: 0.30 },
  { country: "Cuba",        share:  1.2, political: 0.88, ethical: 0.55, regulatory: 0.85 },
];

const PRICE_HISTORY = [
  { month: "Sep '25", price: 48200 },
  { month: "Oct '25", price: 50100 },
  { month: "Nov '25", price: 51800 },
  { month: "Dec '25", price: 54200 },
  { month: "Jan '26", price: 55100 },
  { month: "Feb '26", price: 55900 },
  { month: "Mar '26", price: 56290 },
];

const RISK_COLORS = { low: "#3de8b0", medium: "#e8c840", high: "#e8803d", critical: "#e8503d" };

function getRiskLevel(score) {
  if (score < 0.3) return "low";
  if (score < 0.55) return "medium";
  if (score < 0.75) return "high";
  return "critical";
}

function computeData(rawData, cobaltPrice, weights) {
  return rawData.map(d => {
    const risk = weights.political * d.political + weights.ethical * d.ethical + weights.regulatory * d.regulatory;
    const exposure = (d.share / 100) * cobaltPrice;
    return { ...d, risk: +risk.toFixed(3), exposure: +exposure.toFixed(0), riskLevel: getRiskLevel(risk) };
  });
}

// ── Custom Tooltip ────────────────────────────────────────────────────────────
const ScatterTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="custom-tooltip">
      <div className="tt-label">{d.country}</div>
      <div className="tt-row">Share: <span>{d.share}%</span></div>
      <div className="tt-row">Risk: <span>{d.risk}</span></div>
      <div className="tt-row">Exposure: <span>${d.exposure.toLocaleString()}/Ton</span></div>
    </div>
  );
};

const BarTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div className="tt-label">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="tt-row">{p.name}: <span>{typeof p.value === 'number' && p.value > 10 ? p.value.toFixed(3) : p.value}</span></div>
      ))}
    </div>
  );
};

// ── Main App ──────────────────────────────────────────────────────────────────
export default function CobaltDashboard() {
  const [apiKey, setApiKey] = useState("");
  const [cobaltPrice, setCobaltPrice] = useState(56290);
  const [priceSource, setPriceSource] = useState("benchmark");
  const [loading, setLoading] = useState(false);
  const [exposure, setExposure] = useState(10);
  const [weights, setWeights] = useState({ political: 0.4, ethical: 0.3, regulatory: 0.3 });
  const [data, setData] = useState(() => computeData(BASE_MARKET_DATA, 56290, { political: 0.4, ethical: 0.3, regulatory: 0.3 }));

  useEffect(() => {
    setData(computeData(BASE_MARKET_DATA, cobaltPrice, weights));
  }, [cobaltPrice, weights]);

  const fetchPrice = useCallback(async () => {
    if (!apiKey.trim()) return;
    setLoading(true);
    try {
      // Try Metals-API
      const res = await fetch(`https://metals-api.com/api/latest?access_key=${apiKey}&base=USD&symbols=LCO`);
      const json = await res.json();
      if (json.success && json.rates?.LCO) {
        const pricePerTon = (1 / json.rates.LCO) * 1000;
        setCobaltPrice(Math.round(pricePerTon));
        setPriceSource("live");
      } else {
        setPriceSource("fallback");
      }
    } catch {
      setPriceSource("fallback");
    }
    setLoading(false);
  }, [apiKey]);

  const totalRiskIndex = data.reduce((acc, d) => acc + d.risk * d.share, 0).toFixed(2);
  const drcExposure = data.find(d => d.country === "Congo (DRC)");
  const highRiskShare = data.filter(d => d.riskLevel === "critical" || d.riskLevel === "high")
    .reduce((acc, d) => acc + d.share, 0).toFixed(1);
  const portfolioRisk = ((totalRiskIndex / 100) * exposure * cobaltPrice / 1e6).toFixed(2);

  const radarData = [
    { subject: "Political", value: +(data.reduce((a, d) => a + d.political * d.share, 0) / 100).toFixed(2) },
    { subject: "Ethical",   value: +(data.reduce((a, d) => a + d.ethical * d.share, 0) / 100).toFixed(2) },
    { subject: "Regulatory",value: +(data.reduce((a, d) => a + d.regulatory * d.share, 0) / 100).toFixed(2) },
  ];

  return (
    <>
      <style>{css}</style>
      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="header-left">
            <div className="logo-dot" />
            <div className="header-title">COBALT <span>RISK ENGINE</span></div>
            <div className="header-badge">2026 EDITION</div>
          </div>
          <div className="price-pill">
            <span className="dot" />
            ${cobaltPrice.toLocaleString()}/Ton
            <span style={{ color: "var(--muted)", fontSize: 10 }}>
              {priceSource === "live" ? "LIVE" : "BENCHMARK"}
            </span>
          </div>
        </header>

        <main className="main">
          {/* Form Panel */}
          <div className="form-panel">
            <div className="form-panel-title">⚙ Configuration & Market Settings</div>
            <div className="form-grid">
              <div className="field">
                <label>Metals-API Key (Free Tier)</label>
                <input
                  type="password"
                  placeholder="Enter your free API key…"
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Portfolio Exposure (Metric Tons)</label>
                <input
                  type="number"
                  min="1" max="10000" step="1"
                  value={exposure}
                  onChange={e => setExposure(+e.target.value)}
                />
              </div>
              <div className="field">
                <label>Risk Weight: Political / Ethical / Reg.</label>
                <select value={JSON.stringify(weights)} onChange={e => setWeights(JSON.parse(e.target.value))}>
                  <option value={JSON.stringify({ political: 0.4, ethical: 0.3, regulatory: 0.3 })}>Balanced (40/30/30)</option>
                  <option value={JSON.stringify({ political: 0.6, ethical: 0.2, regulatory: 0.2 })}>Political-Heavy (60/20/20)</option>
                  <option value={JSON.stringify({ political: 0.2, ethical: 0.5, regulatory: 0.3 })}>ESG-Focused (20/50/30)</option>
                  <option value={JSON.stringify({ political: 0.2, ethical: 0.2, regulatory: 0.6 })}>Regulatory-Heavy (20/20/60)</option>
                </select>
              </div>
              <button
                className="btn btn-primary"
                onClick={fetchPrice}
                disabled={loading || !apiKey.trim()}
              >
                {loading ? "Fetching…" : "Fetch Live Price"}
              </button>
            </div>
            <div className="status-bar">
              <span className={`status-dot ${priceSource === "live" ? "live" : "fallback"}`} />
              {priceSource === "live"
                ? "Live price loaded from Metals-API"
                : "Using 2026 LME benchmark · Get free key at metals-api.com"}
            </div>
          </div>

          {/* KPI Cards */}
          <div className="kpi-grid">
            <div className="kpi-card yellow">
              <div className="kpi-label">Cobalt Price</div>
              <div className="kpi-value yellow">${(cobaltPrice / 1000).toFixed(2)}K</div>
              <div className="kpi-sub">per metric ton · LME</div>
            </div>
            <div className="kpi-card red">
              <div className="kpi-label">Supply Chain Risk Index</div>
              <div className="kpi-value red">{totalRiskIndex}</div>
              <div className="kpi-sub">weighted by production share</div>
            </div>
            <div className="kpi-card red">
              <div className="kpi-label">High-Risk Supply Share</div>
              <div className="kpi-value red">{highRiskShare}%</div>
              <div className="kpi-sub">critical + high risk countries</div>
            </div>
            <div className="kpi-card green">
              <div className="kpi-label">Portfolio Risk Exposure</div>
              <div className="kpi-value green">${portfolioRisk}M</div>
              <div className="kpi-sub">{exposure}t at current risk index</div>
            </div>
          </div>

          {/* Row 1: Scatter + Bar */}
          <div className="chart-grid">
            <div className="chart-card">
              <div className="chart-title">
                Risk vs. Production Share
                <span className="chart-title-tag">STRATEGIC MAP</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="share" name="Share" unit="%" stroke="#374151" tick={{ fill: "#64748b", fontSize: 11, fontFamily: "DM Mono" }} label={{ value: "Global Share (%)", position: "insideBottom", offset: -10, fill: "#64748b", fontSize: 11 }} />
                  <YAxis dataKey="risk" name="Risk" domain={[0, 1]} stroke="#374151" tick={{ fill: "#64748b", fontSize: 11, fontFamily: "DM Mono" }} label={{ value: "Risk Score", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }} />
                  <Tooltip content={<ScatterTooltip />} />
                  <ReferenceLine y={0.75} stroke="rgba(232,80,61,0.3)" strokeDasharray="4 4" />
                  <ReferenceLine y={0.3} stroke="rgba(61,232,176,0.3)" strokeDasharray="4 4" />
                  <Scatter
                    data={data}
                    fill="#e8c840"
                  >
                    {data.map((d, i) => (
                      <Cell key={i} fill={RISK_COLORS[d.riskLevel]} fillOpacity={0.8} stroke={RISK_COLORS[d.riskLevel]} strokeWidth={1.5} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <div className="chart-title">
                Composite Risk by Country
                <span className="chart-title-tag">RANKED</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={[...data].sort((a, b) => b.risk - a.risk)} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" horizontal={false} />
                  <XAxis type="number" domain={[0, 1]} stroke="#374151" tick={{ fill: "#64748b", fontSize: 10, fontFamily: "DM Mono" }} />
                  <YAxis dataKey="country" type="category" width={90} stroke="#374151" tick={{ fill: "#94a3b8", fontSize: 11, fontFamily: "DM Mono" }} />
                  <Tooltip content={<BarTooltip />} />
                  <Bar dataKey="risk" radius={[0, 3, 3, 0]}>
                    {[...data].sort((a, b) => b.risk - a.risk).map((d, i) => (
                      <Cell key={i} fill={RISK_COLORS[d.riskLevel]} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Row 2: Price History + Radar */}
          <div className="chart-grid-3">
            <div className="chart-card">
              <div className="chart-title">
                Cobalt Price Trend (6-Month)
                <span className="chart-title-tag">LME USD/TON</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={PRICE_HISTORY} margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="month" stroke="#374151" tick={{ fill: "#64748b", fontSize: 11, fontFamily: "DM Mono" }} />
                  <YAxis domain={[45000, 60000]} stroke="#374151" tick={{ fill: "#64748b", fontSize: 10, fontFamily: "DM Mono" }} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                  <Tooltip formatter={(v) => [`$${v.toLocaleString()}`, "Price/Ton"]} contentStyle={{ background: "#111318", border: "1px solid #1e2330", borderRadius: 8, fontFamily: "DM Mono", fontSize: 12 }} />
                  <Line type="monotone" dataKey="price" stroke="var(--accent)" strokeWidth={2} dot={{ fill: "var(--accent)", r: 3 }} activeDot={{ r: 5 }} />
                  <ReferenceLine y={cobaltPrice} stroke="rgba(61,232,176,0.5)" strokeDasharray="4 4" label={{ value: "Current", fill: "#3de8b0", fontSize: 10, fontFamily: "DM Mono" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <div className="chart-title">
                Global Risk Profile
                <span className="chart-title-tag">RADAR</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.06)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 11, fontFamily: "DM Mono" }} />
                  <PolarRadiusAxis angle={30} domain={[0, 1]} tick={{ fill: "#64748b", fontSize: 9 }} />
                  <Radar name="Weighted Risk" dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.15} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Table */}
          <div className="chart-card">
            <div className="chart-title">
              Country Risk Matrix
              <span className="chart-title-tag">FULL DATA</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Country</th>
                    <th>Share %</th>
                    <th>Political</th>
                    <th>Ethical</th>
                    <th>Regulatory</th>
                    <th>Composite Risk</th>
                    <th>Exposure ($/Ton)</th>
                    <th>Rating</th>
                  </tr>
                </thead>
                <tbody>
                  {[...data].sort((a, b) => b.risk - a.risk).map((d, i) => (
                    <tr key={i}>
                      <td style={{ color: "var(--text)", fontWeight: 600 }}>{d.country}</td>
                      <td>{d.share}%</td>
                      <td>
                        <div className="risk-bar-wrap">
                          <div className="risk-bar-bg"><div className="risk-bar-fill" style={{ width: `${d.political * 100}%`, background: RISK_COLORS[getRiskLevel(d.political)] }} /></div>
                          {d.political.toFixed(2)}
                        </div>
                      </td>
                      <td>
                        <div className="risk-bar-wrap">
                          <div className="risk-bar-bg"><div className="risk-bar-fill" style={{ width: `${d.ethical * 100}%`, background: RISK_COLORS[getRiskLevel(d.ethical)] }} /></div>
                          {d.ethical.toFixed(2)}
                        </div>
                      </td>
                      <td>
                        <div className="risk-bar-wrap">
                          <div className="risk-bar-bg"><div className="risk-bar-fill" style={{ width: `${d.regulatory * 100}%`, background: RISK_COLORS[getRiskLevel(d.regulatory)] }} /></div>
                          {d.regulatory.toFixed(2)}
                        </div>
                      </td>
                      <td style={{ color: RISK_COLORS[d.riskLevel], fontWeight: 600 }}>{d.risk}</td>
                      <td>${d.exposure.toLocaleString()}</td>
                      <td>
                        <span style={{ padding: "3px 10px", borderRadius: 4, fontSize: 10, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", background: `${RISK_COLORS[d.riskLevel]}18`, color: RISK_COLORS[d.riskLevel], border: `1px solid ${RISK_COLORS[d.riskLevel]}33` }}>
                          {d.riskLevel}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Footer note */}
          <div style={{ marginTop: 24, padding: "16px 0", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)" }}>
              Free API: <span style={{ color: "var(--accent)" }}>metals-api.com</span> · Fallback: LME 2026 Benchmark $56,290/Ton
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--muted)" }}>
              DRC Quota Risk · Russia Sanctions · Mar 2026
            </span>
          </div>
        </main>
      </div>
    </>
  );
}
