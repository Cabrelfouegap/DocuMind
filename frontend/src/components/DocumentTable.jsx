import React from 'react';
import StatusBadge from './StatusBadge.jsx';

const DocumentTable = (props) => {
  const laListe = props.documents;
  const leClicVoir = props.onView;
  const leClicTelecharger = props.onDownload;

  if (laListe.length === 0) {
    return (
      <div className="text-center py-16 text-slate-400 text-sm">
        Aucun document disponible.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 shadow-sm">
      <table className="w-full text-sm text-left">
        <thead className="bg-slate-50 text-slate-500 uppercase text-xs tracking-wide">
          <tr>
            <th className="px-5 py-3">Nom du fichier</th>
            <th className="px-5 py-3">Date</th>
            <th className="px-5 py-3">Type</th>
            <th className="px-5 py-3">Statut</th>
            <th className="px-5 py-3">Motif</th>
            <th className="px-5 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {laListe.map((docFichier) => {
            return (
              <tr key={docFichier._id} className="hover:bg-slate-50 transition-colors">
                <td className="px-5 py-3 font-medium text-slate-800 max-w-xs truncate">
                  {docFichier.originalName}
                </td>
                <td className="px-5 py-3 text-slate-500">
                  {new Date(docFichier.createdAt).toLocaleDateString('fr-FR')}
                </td>
                <td className="px-5 py-3 text-slate-500">
                  {docFichier.type || '—'}
                </td>
                <td className="px-5 py-3">
                  <StatusBadge status={docFichier.status} />
                </td>
                <td 
                  className="px-5 py-3 text-slate-500 max-w-xs truncate cursor-help"
                  title={docFichier.reason || ''}
                >
                  {docFichier.reason ? docFichier.reason : '—'}
                </td>
                <td className="px-5 py-3 text-right space-x-2">
                  <button
                    onClick={() => { leClicVoir(docFichier); }}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 text-xs font-medium hover:bg-slate-200 transition-colors"
                  >
                    Voir
                  </button>
                  <button
                    onClick={() => { leClicTelecharger(docFichier); }}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 transition-colors"
                  >
                    Télécharger
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default DocumentTable;
