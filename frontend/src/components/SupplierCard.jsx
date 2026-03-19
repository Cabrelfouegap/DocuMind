import React from 'react';

const SupplierCard = (props) => {
  const leFournisseur = props.supplier;
  const lesDocuments = props.documents || [];
  const fonctionVoir = props.onView;
  const fonctionTelecharger = props.onDownload;
  const anomalyCount = props.anomalyCount ?? 0;
  const supplierStatus = props.supplierStatus ?? 'UNKNOWN';
  const onShowAnomalies = props.onShowAnomalies;
  const documentsCount = props.documentsCount ?? lesDocuments.length;

  const anomalyStatusStyle = (() => {
    const s = String(supplierStatus || '').toUpperCase();
    if (s === 'VALID') return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    if (s === 'WARNING') return 'bg-orange-100 text-orange-700 border-orange-200';
    if (s === 'SUSPICIOUS') return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-slate-100 text-slate-700 border-slate-200';
  })();

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:border-indigo-300 transition-all">
      <div className="px-6 py-4 border-b border-slate-50 bg-slate-50/50 flex justify-between items-center">
        <div>
          <h3 className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
            {leFournisseur.name}
          </h3>
          <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">
            SIRET: {leFournisseur.siret}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-slate-400 uppercase font-medium">Cumul HT Validé</p>
          <p className="text-sm font-bold text-indigo-600">
            {Number(leFournisseur.totalAmount || 0).toFixed(2)}€
          </p>
          <div className="mt-2 flex items-center justify-end gap-2">
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-xl border text-[10px] font-semibold ${anomalyStatusStyle}`}>
              <span>Anomalies</span>
              <span className="tabular-nums">{anomalyCount}</span>
            </span>
            <button
              onClick={() => onShowAnomalies?.(leFournisseur.siret)}
              disabled={!onShowAnomalies || anomalyCount === 0}
              className="text-[10px] font-semibold px-3 py-1 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Voir les anomalies et la preuve"
            >
              Détails
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-2">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-2">Documents rattachés ({documentsCount})</p>
        <div className="space-y-1 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
          {lesDocuments.length === 0 ? (
            <div className="text-[10px] text-slate-400 px-2 py-2">
              Les documents apparaissent dans les détails.
            </div>
          ) : (
            lesDocuments.map((doc) => {
            let couleurPoint = 'bg-slate-300';
            if (doc.status === 'Conforme') {
              couleurPoint = 'bg-emerald-400';
            } else if (doc.status === 'Warning') {
              couleurPoint = 'bg-orange-400';
            } else if (doc.status === 'Non conforme') {
              couleurPoint = 'bg-red-400';
            }

            return (
              <div key={doc._id} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 group border border-transparent hover:border-slate-100 transition-all">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${couleurPoint}`} />
                  <div className="min-w-0">
                    <p className="text-[11px] font-medium text-slate-700 truncate" title={doc.originalName}>
                      {doc.originalName}
                    </p>
                    <p className="text-[9px] text-slate-400">
                      {doc.type || 'Inconnu'} • {new Date(doc.createdAt).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => fonctionVoir(doc)}
                    className="p-1 hover:text-indigo-600 text-slate-400 transition-colors"
                    title="Voir"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => fonctionTelecharger(doc)}
                    className="p-1 hover:text-indigo-600 text-slate-400 transition-colors"
                    title="Télécharger"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                </div>
              </div>
            );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default SupplierCard;
