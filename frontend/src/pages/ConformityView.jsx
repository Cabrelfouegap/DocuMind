import React, { useEffect, useRef, useState } from 'react';
import {
  fetchDocuments as getDocuments,
  uploadDocument as sendFiles,
  updateDocument as updateDoc,
  analyzeDocument as runIA
} from '../api/documents.js';
import StatusBadge from '../components/StatusBadge.jsx';
import StatCard from '../components/StatCard.jsx';
import FilterBar from '../components/FilterBar.jsx';

const ConformityView = () => {
  const [listeDocs, setListeDocs] = useState([]);
  const [estEnTrainDeCharger, setEstEnTrainDeCharger] = useState(true);
  const [enTrainDUploader, setEnTrainDUploader] = useState(false);
  const [estAuDessus, setEstAuDessus] = useState(false);

  const [texteRecherche, setTexteRecherche] = useState('');
  const [ongletActif, setOngletActif] = useState('Tous');

  const [idsEnCoursDAnalyse, setIdsEnCoursDAnalyse] = useState([]);

  const inputFichierRef = useRef(null);


  const chargerDocs = () => {
    getDocuments()
      .then((reponse) => {
        setListeDocs(reponse.data);
        setEstEnTrainDeCharger(false);
      })
      .catch((err) => {
        console.error("Erreur:", err);
        setEstEnTrainDeCharger(false);
      });
  };

  useEffect(() => {
    chargerDocs();
  }, []);


  const envoyerFichiers = async (fichiers) => {
    if (!fichiers || fichiers.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < fichiers.length; i++) {
      formData.append('files', fichiers[i]);
    }

    setEnTrainDUploader(true);
    try {
      await sendFiles(formData);
      await chargerDocs();
    } catch (e) {
      console.error("Upload raté", e);
    } finally {
      setEnTrainDUploader(false);
    }
  };

  const quandOnDepose = (e) => {
    e.preventDefault();
    setEstAuDessus(false);
    const fichiersDocuments = e.dataTransfer.files;
    if (fichiersDocuments.length > 0) {
      envoyerFichiers(fichiersDocuments);
    }
  };


  const lancerIA = async (document) => {
    const idsCopiés = [...idsEnCoursDAnalyse, document._id];
    setIdsEnCoursDAnalyse(idsCopiés);

    try {
      const reponseIA = await runIA(document._id);
      const docsAnalysés = reponseIA.data;

      const listeMiseAJour = listeDocs.map((item) => {
        if (item._id === document._id) {
          return { ...item, ...docsAnalysés };
        }
        return item;
      });
      setListeDocs(listeMiseAJour);
    } catch (erreur) {
      console.error("IA Erreur", erreur);
    } finally {
      const listeSansLId = idsEnCoursDAnalyse.filter((id) => id !== document._id);
      setIdsEnCoursDAnalyse(listeSansLId);
      chargerDocs();
    }
  };


  // RawDocument : processingStatus au lieu de status
  const total = listeDocs.length;
  const attente = listeDocs.filter((d) => d.processingStatus === 'PENDING').length;
  const processing = listeDocs.filter((d) => d.processingStatus === 'PROCESSING').length;
  const completed = listeDocs.filter((d) => d.processingStatus === 'OCR_COMPLETED').length;
  const failed = listeDocs.filter((d) => d.processingStatus === 'FAILED').length;

  const lesComptages = {
    total,
    'PENDING': attente,
    'PROCESSING': processing,
    'OCR_COMPLETED': completed,
    'FAILED': failed
  };


  const documentsAffiches = listeDocs.filter((doc) => {
    const okStatus = (ongletActif === 'Tous' || doc.processingStatus === ongletActif);
    const s = texteRecherche.toLowerCase();
    // RawDocument utilise originalFileName
    const n = (doc.originalFileName || '').toLowerCase();
    const okRecherche = n.includes(s);
    return okStatus && okRecherche;
  });

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <div>
            <span className="font-semibold text-slate-800 text-lg">DocuMind</span>
            <span className="ml-2 text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-medium">
              Outil de Conformité
            </span>
          </div>
        </div>
        <a href="/" className="text-xs text-slate-500 hover:text-indigo-600 transition-colors">
          ← CRM
        </a>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Validation & Conformité</h1>
            <p className="text-[10px] text-slate-500">Vérification OCR et détection d'incohérences (SIRET/TVA).</p>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4 items-stretch">
          <div className="col-span-12 lg:col-span-7 grid grid-cols-4 gap-3">
            <StatCard label="Total" value={total} accent="text-slate-800" />
            <StatCard label="En attente" value={attente} accent="text-amber-600" />
            <StatCard label="En cours" value={processing} accent="text-blue-600" />
            <StatCard label="Terminés" value={completed} accent="text-emerald-600" />
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setEstAuDessus(true); }}
            onDragLeave={() => { setEstAuDessus(false); }}
            onDrop={quandOnDepose}
            onClick={() => { inputFichierRef.current.click(); }}
            className={'col-span-12 lg:col-span-5 border-2 border-dashed rounded-2xl px-4 py-3 text-center cursor-pointer transition-all flex items-center justify-center gap-3 ' + (estAuDessus ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 bg-white hover:border-indigo-300 hover:bg-slate-50')}
          >
            <input
              ref={inputFichierRef}
              type="file"
              className="hidden"
              accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
              multiple
              onChange={(e) => { envoyerFichiers(e.target.files); }}
            />
            <div className="text-xl">📂</div>
            {enTrainDUploader ? (
              <p className="text-xs text-indigo-600 font-medium">Envoi...</p>
            ) : (
              <div className="text-left">
                <p className="text-[11px] font-medium text-slate-700 leading-tight">
                  Glisser ou cliquer pour uploader
                </p>
                <p className="text-[9px] text-slate-400 mt-0.5">PDF, Word, Images</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-2 border-b border-slate-100 flex items-center justify-between gap-4">
            <h2 className="text-xs font-semibold text-slate-700 whitespace-nowrap">Documents ({total})</h2>
            <div className="flex-1">
              <FilterBar
                search={texteRecherche}
                onSearch={setTexteRecherche}
                status={ongletActif}
                onStatus={setOngletActif}
                counts={lesComptages}
              />
            </div>
          </div>

          {estEnTrainDeCharger ? (
            <div className="text-center py-8 text-slate-400 text-xs">Chargement...</div>
          ) : listeDocs.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">Aucun document.</div>
          ) : documentsAffiches.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">Aucun résultat.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[11px] text-left table-fixed">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="px-4 py-2 w-[25%]">Fichier</th>
                    <th className="px-4 py-2 w-[12%]">Type</th>
                    <th className="px-4 py-2 w-[10%] text-center">Date</th>
                    <th className="px-4 py-2 w-[15%] text-center">Statut</th>
                    <th className="px-4 py-2 w-[15%] text-right">Données Extraites</th>
                    <th className="px-4 py-2 w-[15%] text-center">Détail/Motif</th>
                    <th className="px-4 py-2 w-[6%] text-center">Aperçu</th>
                    <th className="px-4 py-2 w-[17%] text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {documentsAffiches.map((doc) => {
                    const estEnCoursDAnalyse = idsEnCoursDAnalyse.includes(doc._id);

                    return (
                      <tr key={doc._id} className="hover:bg-slate-50 transition-colors">

                        {/* Nom du fichier — RawDocument: originalFileName */}
                        <td className="px-4 py-1.5 font-medium text-slate-800 truncate">
                          {doc.originalFileName || '—'}
                        </td>

                        {/* Type — sera rempli par OCR via typeSuggere */}
                        <td className="px-4 py-1.5 text-slate-500 truncate">
                          {doc.typeSuggere || '—'}
                        </td>

                        {/* Date */}
                        <td className="px-4 py-1.5 text-slate-500 text-center">
                          {new Date(doc.createdAt).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}
                        </td>

                        {/* Statut OCR — processingStatus */}
                        <td className="px-4 py-1.5 text-center">
                          <span className={
                            'text-[10px] font-semibold px-2 py-0.5 rounded-full ' +
                            (doc.processingStatus === 'PENDING' ? 'bg-amber-100 text-amber-700' :
                            doc.processingStatus === 'PROCESSING' ? 'bg-blue-100 text-blue-700' :
                            doc.processingStatus === 'OCR_COMPLETED' ? 'bg-emerald-100 text-emerald-700' :
                            'bg-red-100 text-red-700')
                          }>
                            {doc.processingStatus}
                          </span>
                        </td>

                        {/* Données extraites — viendront de CleanDocument via OCR */}
                        <td className="px-4 py-1.5 text-right font-medium text-slate-400 text-[10px]">
                          {doc.processingStatus === 'OCR_COMPLETED' ? 'Disponibles' : '—'}
                        </td>
                        {/* Détails/Motifs (WIP) */}
                        <td className="px-4 py-1.5 text-right font-medium text-slate-400 text-[10px]">
                          {}
                        </td>
                        {/* Aperçu */}
                        <td className="px-4 py-1.5 text-center">
                          <a
                            href={'/api/documents/file/' + doc.storedFilePath}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center justify-center p-1 rounded-md bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 transition-colors"
                          >
                            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </a>
                        </td>

                        {/* Action */}
                        <td className="px-4 py-1.5">
                          <div className="flex items-center justify-end gap-1.5">
                            {doc.processingStatus === 'PENDING' && (
                              <button
                                onClick={() => lancerIA(doc)}
                                disabled={estEnCoursDAnalyse}
                                className="px-2 py-1 rounded bg-violet-50 text-violet-700 text-[10px] font-semibold hover:bg-violet-100 disabled:opacity-60 transition-colors whitespace-nowrap"
                              >
                                {estEnCoursDAnalyse ? '...' : 'IA'}
                              </button>
                            )}
                            {doc.processingStatus === 'PROCESSING' && (
                              <span className="text-[10px] text-blue-500">En cours...</span>
                            )}
                            {doc.processingStatus === 'OCR_COMPLETED' && (
                              <span className="text-[10px] text-emerald-600 font-semibold">✓ Traité</span>
                            )}
                            {doc.processingStatus === 'FAILED' && (
                              <span className="text-[10px] text-red-500">✗ Échec</span>
                            )}
                          </div>
                        </td>

                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ConformityView;