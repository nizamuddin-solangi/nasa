import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet';
import { Activity, Download, MapPin, Play, Radio, RefreshCw, Scale } from 'lucide-react';
import { Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import 'leaflet/dist/leaflet.css';
import './style.css';

const API = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');
type Query = { latitude: number; longitude: number; variable: string; start_year: number; end_year: number };
type Result = { metadata: any; statistics: any; observations: any[]; trend_line: any[]; interpretation: string };
const presets: (Query & { name: string })[] = [
  { name: 'Urban Heat', latitude: 24.8607, longitude: 67.0011, variable: 'T2M', start_year: 2001, end_year: 2024 },
  { name: 'Precipitation', latitude: 30.3753, longitude: 69.3451, variable: 'PRECTOTCORR', start_year: 2001, end_year: 2024 },
  { name: 'Climate Comparison', latitude: 40.7128, longitude: -74.006, variable: 'T2M', start_year: 2001, end_year: 2024 },
];

function Picker({ query, setQuery }: { query: Query; setQuery: (value: Query) => void }) {
  useMapEvents({ click: (event) => setQuery({ ...query, latitude: +event.latlng.lat.toFixed(4), longitude: +event.latlng.lng.toFixed(4) }) });
  return <Marker position={[query.latitude, query.longitude]} />;
}
function Map({ query, setQuery }: { query: Query; setQuery: (value: Query) => void }) {
  return <MapContainer center={[query.latitude, query.longitude]} zoom={5} className="map"><TileLayer attribution="© OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" /><Picker query={query} setQuery={setQuery} /></MapContainer>;
}
function Metric({ label, value }: { label: string; value: string | number }) { return <div className="metric"><small>{label}</small><strong>{value}</strong></div>; }
function Charts({ result }: { result: Result }) {
  const data = result.observations.map((item, index) => ({ ...item, date: item.date.slice(0, 7), trend: result.trend_line[index]?.value }));
  return <div className="charts">
    <div className="chartcard"><h3>Original NASA POWER observations</h3><ResponsiveContainer width="100%" height={280}><LineChart data={data}><XAxis dataKey="date" minTickGap={40} /><YAxis /><Tooltip /><Line dot={false} stroke="#7ae5ff" dataKey="value" name="Observation" /></LineChart></ResponsiveContainer></div>
    <div className="chartcard"><h3>Deseasonalized anomalies & Sen trend</h3><ResponsiveContainer width="100%" height={280}><LineChart data={data}><XAxis dataKey="date" minTickGap={40} /><YAxis /><Tooltip /><Legend /><Line dot={false} stroke="#8dc5d2" dataKey="anomaly" name="Monthly anomaly" /><Line dot={false} stroke="#ffb86a" dataKey="trend" name="Sen trend" /></LineChart></ResponsiveContainer></div>
  </div>;
}

function App() {
  const [query, setQuery] = useState<Query>(presets[0]); const [result, setResult] = useState<Result>(); const [comparison, setComparison] = useState<any>();
  const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [view, setView] = useState<'lab' | 'compare'>('lab');
  async function request(path: string, body: unknown) { const response = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); if (!response.ok) { const text = await response.text(); let message = 'Request failed'; try { message = JSON.parse(text).detail || message; } catch { if (text) message = text.slice(0, 180); } throw new Error(message); } return response; }
  async function investigate() { setLoading(true); setError(''); try { const response = await request('/investigations', query); setResult((await response.json()).result); setView('lab'); } catch (e: any) { setError(e.message); } finally { setLoading(false); } }
  async function compare() { setLoading(true); setError(''); try { const second = { ...query, latitude: 40.7128, longitude: -74.006 }; const response = await request('/analysis/compare', { first: query, second }); setComparison(await response.json()); setView('compare'); } catch (e: any) { setError(e.message); } finally { setLoading(false); } }
  async function report() { if (!result) return; const response = await request('/reports/generate', { result, title: 'EARTHSCOPE Investigation Report' }); const url = URL.createObjectURL(await response.blob()); const link = document.createElement('a'); link.href = url; link.download = 'earthscope-report.pdf'; link.click(); URL.revokeObjectURL(url); }
  return <main><header><div className="brand"><span className="orb" /> EARTHSCOPE <small>EARTH SYSTEM TREND DETECTIVE</small></div><nav><button onClick={() => setView('lab')}>Investigation Lab</button><button onClick={compare}>Compare</button><span className="live"><Radio size={13} /> NASA POWER LIVE</span></nav></header>
    <section className="hero"><div><p className="eyebrow">NASA SPACE APPS 2026</p><h1>Find the signal.<br /><i>Question the change.</i></h1><p className="sub">A scientific investigation environment for real NASA Earth-system observations. Explore trends, uncertainty and place.</p></div><div className="mission"><Activity /><b>{result ? 'Analysis complete' : 'Ready for investigation'}</b><span>{result ? result.statistics.period : 'Select a location and launch.'}</span></div></section>
    <section className="presets">{presets.map((preset) => <button key={preset.name} onClick={() => { setQuery(preset); setView('lab'); }}><Scale size={16} /><span>{preset.name}<small>{preset.variable} · {preset.start_year}–{preset.end_year}</small></span></button>)}</section>{error && <div className="error">Data unavailable — {error}</div>}
    {view === 'lab' ? <><section className="lab"><aside><p className="eyebrow">01 / DEFINE STUDY</p><h2>Investigation Lab</h2><label>Environmental variable<select value={query.variable} onChange={(event) => setQuery({ ...query, variable: event.target.value })}><option value="T2M">Temperature at 2 meters</option><option value="PRECTOTCORR">Corrected precipitation</option><option value="WS10M">Wind speed at 10 meters</option><option value="ALLSKY_SFC_SW_DWN">Surface solar radiation</option></select></label><div className="grid"><label>Latitude<input type="number" step=".0001" value={query.latitude} onChange={(event) => setQuery({ ...query, latitude: +event.target.value })} /></label><label>Longitude<input type="number" step=".0001" value={query.longitude} onChange={(event) => setQuery({ ...query, longitude: +event.target.value })} /></label><label>Start year<input type="number" value={query.start_year} onChange={(event) => setQuery({ ...query, start_year: +event.target.value })} /></label><label>End year<input type="number" value={query.end_year} onChange={(event) => setQuery({ ...query, end_year: +event.target.value })} /></label></div><button className="launch" disabled={loading} onClick={investigate}>{loading ? <RefreshCw className="spin" /> : <Play />} {loading ? 'Retrieving NASA observations…' : 'Launch investigation'}</button><p className="fine">Click the basemap to place the study marker. Basemap © OpenStreetMap; it is not a NASA imagery layer.</p></aside><Map query={query} setQuery={setQuery} /></section>
      {result && <section className="results"><div className="resulthead"><div><p className="eyebrow">02 / EARTH INTELLIGENCE</p><h2>{result.metadata.label}</h2><span><MapPin size={14} />{result.metadata.latitude.toFixed(4)}, {result.metadata.longitude.toFixed(4)} · {result.metadata.unit}</span></div><button className="download" onClick={report}><Download size={16} /> Download report</button></div><div className="metrics"><Metric label="Classification" value={result.statistics.direction} /><Metric label="Sen’s slope" value={`${result.statistics.slope_per_decade > 0 ? '+' : ''}${result.statistics.slope_per_decade} ${result.metadata.unit}/decade`} /><Metric label="p-value" value={result.statistics.p_value} /><Metric label="95% interval" value={result.statistics.ci95_per_decade.join(' to ')} /></div><Charts result={result} /><article><h3>Scientific finding</h3><p>{result.interpretation}</p><p className="fine"><b>Provenance:</b> {result.metadata.source}. Retrieved {new Date(result.metadata.retrieved_at).toLocaleString()}. Values are model-derived / gridded estimates, not station measurements.</p></article></section>}</>
      : <section className="results">{comparison ? <><p className="eyebrow">COMPARATIVE INTELLIGENCE</p><h2>Two-place comparison</h2><div className="metrics"><Metric label="First trend" value={`${comparison.first.statistics.slope_per_decade} ${comparison.first.metadata.unit}/decade`} /><Metric label="Second trend" value={`${comparison.second.statistics.slope_per_decade} ${comparison.second.metadata.unit}/decade`} /><Metric label="Difference" value={comparison.comparison.slope_difference_per_decade} /><Metric label="Trend-difference p" value={comparison.comparison.comparative_significance.p_value ?? 'N/A'} /></div><article><p>{comparison.comparison.note}</p><p className="fine">{comparison.comparison.comparative_significance.method}. Matched observations: {comparison.comparison.comparative_significance.matched_observations}.</p></article></> : <p>Launching comparison…</p>}</section>}
  </main>;
}
createRoot(document.getElementById('root')!).render(<App />);
