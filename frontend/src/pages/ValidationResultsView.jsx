import React, { useEffect, useMemo, useState } from 'react';
import { fetchValidationResults } from '../api/validation.js';

const badge = (status) => {
  if (status === 'SUSPICIOUS') return 'bg-red-50 text-red-700 border-red-200';
  if (status === 'WARNING') return 'bg-amber-50 text-amber-700 border-amber-200';
  if (status === 'VALID') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  return 'bg-slate-50 text-slate-700 border-slate-200';
};

const ValidationResultsView = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');

  useEffect(() => {
    fetchValidationResults()
      .then((res) => {
        setResults(res.data || []);
        setLoading(false);
      })
      .catch((e) => {
        console.error('Erreur chargement validation results:', e);
        setLoading(false);
      });
  }, []);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return results;
    return results.filter((r) => (r.vendorId || '').toLowerCase().includes(query));
  }, [results, q]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-200">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <div>
            <span className="font-semibold text-slate-800 text-lg">DocuMind</span>
            <span className="ml-2 text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
              Résultats Validation
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="/conformity"
            className="text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors bg-slate-100 hover:bg-indigo-50 px-4 py-2 rounded-xl"
          >
            Conformité →
          </a>
          <a
            href="/"
            className="text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors bg-slate-100 hover:bg-indigo-50 px-4 py-2 rounded-xl"
          >
            CRM →
          </a>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-10 space-y-6">
        <div className="flex items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Anomalies détectées</h1>
            <p className="text-sm text-slate-500 mt-2 font-medium">
              Agrégé par fournisseur (format aligné avec `anomaly_results.json`).
            </p>
          </div>
          <div className="w-full max-w-sm">
            <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Rechercher vendorId
            </label>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white text-sm outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300"
              placeholder="Ex: V03"
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-slate-400 font-medium">Chargement des résultats...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300">
            <p className="text-slate-500 font-medium">Aucun résultat.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => {
              const v = item.validation || {};
              const anomalies = v.anomaliesDetected || [];
              return (
                <details
                  key={item.vendorId}
                  className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden"
                >
                  <summary className="cursor-pointer select-none px-6 py-4 flex items-center justify-between gap-6">
                    <div className="min-w-0">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-extrabold text-slate-900">{item.vendorId}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badge(v.status)}`}>
                          {v.status || 'UNKNOWN'}
                        </span>
                        <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                          décision: {v.decision || '—'}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">
                        score final: <span className="font-semibold text-slate-700">{v.finalScore ?? '—'}</span> • anomalies:{' '}
                        <span className="font-semibold text-slate-700">{v.anomalyCount ?? anomalies.length}</span>
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-400 whitespace-nowrap">
                      {v.lastCheckedAt ? new Date(v.lastCheckedAt).toLocaleString('fr-FR') : '—'}
                    </div>
                  </summary>

                  <div className="px-6 pb-5 pt-0">
                    {anomalies.length === 0 ? (
                      <div className="text-xs text-slate-500">Aucune anomalie détaillée.</div>
                    ) : (
                      <div className="space-y-2">
                        {anomalies.map((a, idx) => (
                          <div key={idx} className="p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                            <div className="flex items-center justify-between gap-3">
                              <div className="min-w-0">
                                <div className="text-[11px] font-bold text-slate-800 truncate">
                                  {a.anomalyCode || 'ANOMALY'}
                                </div>
                                <div className="text-[11px] text-slate-600 mt-0.5">{a.message || '—'}</div>
                              </div>
                              <div className="text-right shrink-0">
                                <div className="text-[10px] text-slate-500 font-semibold uppercase">
                                  {a.severity || '—'}
                                </div>
                                <div className="text-[10px] text-slate-400">score: {a.score ?? '—'}</div>
                              </div>
                            </div>

                            {a.details ? (
                              <pre className="mt-2 text-[10px] leading-4 bg-white border border-slate-200 rounded-lg p-2 overflow-auto text-slate-700">
                                {JSON.stringify(a.details, null, 2)}
                              </pre>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </details>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};

export default ValidationResultsView;

