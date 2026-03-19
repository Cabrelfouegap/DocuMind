import React, { useEffect, useState } from 'react';
import {
  fetchDocuments as getDocs,
  fetchAnomaliesSuppliersSummary,
  fetchAnomaliesSupplierDetails,
} from '../api/documents.js';
import StatCard from '../components/StatCard.jsx';
import FilterBar from '../components/FilterBar.jsx';
import SupplierCard from '../components/SupplierCard.jsx';

const CRMView = () => {
  const [tousLesDocs, setTousLesDocs] = useState([]);
  const [enChargement, setEnChargement] = useState(true);
  const [recherche, setRecherche] = useState('');
  const [anomaliesSuppliers, setAnomaliesSuppliers] = useState([]);

  const [anomaliesModalOpen, setAnomaliesModalOpen] = useState(false);
  const [selectedSupplierSiret, setSelectedSupplierSiret] = useState('');
  const [selectedSupplierDetails, setSelectedSupplierDetails] = useState(null);
  const [supplierDetailsLoading, setSupplierDetailsLoading] = useState(false);

  useEffect(() => {
    const charger = async () => {
      try {
        const [docsRes, anomaliesRes] = await Promise.allSettled([
          getDocs(),
          fetchAnomaliesSuppliersSummary(),
        ]);

        if (docsRes.status === 'fulfilled') {
          setTousLesDocs(docsRes.value.data);
        }

        if (anomaliesRes.status === 'fulfilled') {
          setAnomaliesSuppliers(anomaliesRes.value.data || []);
        }
      } catch (err) {
        console.error('Erreur chargement CRM + anomalies:', err);
      } finally {
        setEnChargement(false);
      }
    };

    charger();
  }, []);

  const normaliserMontant = (valeurBrute) => {
    if (valeurBrute === null || valeurBrute === undefined) return 0;
    if (typeof valeurBrute === 'number') return valeurBrute;

    const texte = String(valeurBrute)
      .replace(/[^\d,.\-]/g, '')
      .replace(',', '.');

    const n = parseFloat(texte);
    return Number.isNaN(n) ? 0 : n;
  };

  const creerListeFournisseurs = () => {
    const dictionnaire = {};
    const anomaliesMap = new Map(
      (anomaliesSuppliers || []).map((a) => [String(a.siret), a])
    );

    for (let i = 0; i < tousLesDocs.length; i++) {
      const doc = tousLesDocs[i];
      const siret = doc.extractedData?.siret || 'Sans SIRET';

      const nomFichierMinuscule = doc.originalName.toLowerCase();
      const nomSansExtension = doc.originalName.split('.')[0];

      const nomCompagnieOCR = doc.extractedData?.companyName || doc.extractedData?.company_name || '';

      let nomFournisseur = nomCompagnieOCR || 'Fournisseur Inconnu';

      if (!nomCompagnieOCR && siret === 'Sans SIRET') {
        nomFournisseur = 'A vérifier';
      } else if (!nomCompagnieOCR) {
        if (nomFichierMinuscule.includes('contrat')) {
          nomFournisseur = 'Service Prestation Plus';
        } else if (nomSansExtension) {
          nomFournisseur = nomSansExtension.replace(/[_-]+/g, ' ');
        }
      }

      if (!dictionnaire[siret]) {
        const anomaly = anomaliesMap.get(String(siret)) || null;
        dictionnaire[siret] = {
          siret: siret,
          name: nomFournisseur,
          totalAmount: 0,
          documents: [],
          anomalyCount: anomaly?.anomalyCount ?? 0,
          supplierStatus: anomaly?.status ?? 'UNKNOWN',
        };
      }

      dictionnaire[siret].documents.push(doc);

      if (doc.status === 'Conforme') {
        const montant = normaliserMontant(doc.extractedData?.amountTTC);
        dictionnaire[siret].totalAmount = dictionnaire[siret].totalAmount + montant;
      }
    }

    return Object.values(dictionnaire);
  };

  const laListeComplete = creerListeFournisseurs();
  const fournisseursDepuisAnomalies = (anomaliesSuppliers || []).map((a) => ({
    siret: a.siret,
    name: a.companyName || 'Fournisseur',
    totalAmount: 0,
    documents: [],
    anomalyCount: a.anomalyCount ?? 0,
    supplierStatus: a.status ?? 'UNKNOWN',
    documentsCount: a.docCount ?? 0,
  }));

  // Si la collection "Document" est vide (cas fréquent après rebuild), on affiche au moins les fournisseurs depuis "Curated".
  const fournisseursSource = laListeComplete.length > 0 ? laListeComplete : fournisseursDepuisAnomalies;

  const fournisseursFiltrés = fournisseursSource.filter((f) => {
    const texteRecherche = recherche.toLowerCase();
    const nomOk = f.name.toLowerCase().includes(texteRecherche);
    const siretOk = f.siret.includes(recherche);

    return nomOk || siretOk;
  });

  const voirDoc = (doc) => {
    window.open('/uploads/' + doc.filename, '_blank');
  };

  const telechargerDoc = (doc) => {
    const lien = document.createElement('a');
    lien.href = '/uploads/' + doc.filename;
    lien.download = doc.originalName;
    lien.click();
  };

  const ouvrirModalAnomalies = async (siret) => {
    if (!siret) return;
    setSelectedSupplierSiret(String(siret));
    setSelectedSupplierDetails(null);
    setAnomaliesModalOpen(true);
    setSupplierDetailsLoading(true);
    try {
      const reponse = await fetchAnomaliesSupplierDetails(String(siret));
      setSelectedSupplierDetails(reponse.data || null);
    } catch (err) {
      console.error('Erreur chargement détails anomalies:', err);
    } finally {
      setSupplierDetailsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-200">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <div>
            <span className="font-semibold text-slate-800 text-lg">DocuMind</span>
            <span className="ml-2 text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
              CRM Fournisseurs
            </span>
          </div>
        </div>
        <a href="/conformity" className="text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors bg-slate-100 hover:bg-indigo-50 px-4 py-2 rounded-xl">
          Outil Conformité →
        </a>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-10 space-y-8">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Répertoire Fournisseurs</h1>
            <p className="text-sm text-slate-500 mt-2 font-medium">Consultez les données structurées de l'entreprise et l'historique de conformité.</p>
          </div>
          <div className="flex gap-4">
            <StatCard label="Fournisseurs" value={laListeComplete.length} accent="text-slate-800" />
            <StatCard label="Docs Validés" value={tousLesDocs.filter(d => d.status === 'Conforme').length} accent="text-emerald-600" />
          </div>
        </div>

        <FilterBar
          search={recherche}
          onSearch={setRecherche}
          hideStatus={true}
          placeholder="Rechercher un fournisseur ou SIRET..."
        />

        {enChargement ? (
          <div className="text-center py-20">
            <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-slate-400 font-medium">Synchronisation des données CRM...</p>
          </div>
        ) : fournisseursFiltrés.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300">
            <span className="text-4xl mb-4 block">🔍</span>
            <p className="text-slate-500 font-medium">Aucun fournisseur ne correspond à votre recherche.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {fournisseursFiltrés.map((f) => (
              <SupplierCard
                key={f.siret}
                supplier={f}
                documents={f.documents}
                onView={voirDoc}
                onDownload={telechargerDoc}
                anomalyCount={f.anomalyCount}
                supplierStatus={f.supplierStatus}
                documentsCount={f.documentsCount}
                onShowAnomalies={ouvrirModalAnomalies}
              />
            ))}
          </div>
        )}
      </main>

      {anomaliesModalOpen && (
        <div className="fixed inset-0 z-50">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setAnomaliesModalOpen(false)}
          />
          <div className="relative mx-auto mt-16 mb-8 max-w-5xl bg-white rounded-2xl shadow-xl overflow-hidden max-h-[calc(100vh-8rem)] flex flex-col">
            <div className="p-5 border-b flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">
                  Anomalies fournisseur
                </h2>
                <p className="text-sm text-slate-600 font-mono">
                  SIRET: {selectedSupplierSiret || '—'}
                </p>
                {selectedSupplierDetails?.companyName && (
                  <p className="text-sm text-slate-600">
                    Société: <span className="font-semibold">{selectedSupplierDetails.companyName}</span>
                  </p>
                )}
              </div>
              <button
                className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold"
                onClick={() => setAnomaliesModalOpen(false)}
              >
                Fermer
              </button>
            </div>

            <div className="p-5 space-y-4 overflow-y-auto">
              {supplierDetailsLoading ? (
                <div className="text-center py-10 text-slate-500 font-medium">
                  Chargement des détails...
                </div>
              ) : !selectedSupplierDetails ? (
                <div className="text-center py-10 text-slate-500 font-medium">
                  Aucun détail disponible pour ce fournisseur.
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="px-3 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-sm font-semibold">
                      Statut: {selectedSupplierDetails.status}
                    </span>
                    <span className="px-3 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-sm font-semibold">
                      Score: {Number(selectedSupplierDetails.finalScore || 0)}
                    </span>
                    <span className="px-3 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-sm font-semibold">
                      Anomalies: {Number(selectedSupplierDetails.anomalyCount || 0)}
                    </span>
                  </div>

                  {(() => {
                    const allDocs = selectedSupplierDetails.documents || [];
                    const flattened = allDocs.flatMap((d) => d.validation?.anomaliesDetected || []);
                    const dedupMap = new Map();
                    for (const a of flattened) {
                      const key = `${a.anomalyCode}|${a.severity}|${a.message}|${JSON.stringify(a.details || {})}`;
                      if (!dedupMap.has(key)) dedupMap.set(key, a);
                    }
                    const deduped = Array.from(dedupMap.values());

                    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, LOW: 3, MEDIUM: 2, HIGH: 1 };
                    deduped.sort((a, b) => {
                      const sa = String(a.severity || '').toLowerCase();
                      const sb = String(b.severity || '').toLowerCase();
                      return (severityOrder[sa] ?? 99) - (severityOrder[sb] ?? 99);
                    });

                    const renderDetails = (details) => {
                      const d = details && typeof details === 'object' ? details : null;
                      if (!d) return <div className="text-sm text-slate-600">—</div>;

                      const docKeys = ['quote', 'invoice', 'urssaf', 'kbis', 'rib'];
                      const keys = Object.keys(d);

                      // Cas: mapping docType -> valeur (SIRET mismatch / COMPANY name mismatch)
                      const looksLikeDocTypeMapping = keys.length > 0 && keys.every((k) => docKeys.includes(k));
                      if (looksLikeDocTypeMapping) {
                        return (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm border border-slate-200 rounded-xl overflow-hidden">
                              <thead className="bg-slate-50">
                                <tr>
                                  <th className="p-2 text-left text-slate-600 font-semibold text-xs">Document</th>
                                  <th className="p-2 text-left text-slate-600 font-semibold text-xs">Valeur</th>
                                </tr>
                              </thead>
                              <tbody>
                                {docKeys
                                  .filter((k) => d[k] !== undefined)
                                  .map((k) => (
                                    <tr key={k} className="border-t border-slate-100">
                                      <td className="p-2 text-slate-700 font-medium text-xs">{k}</td>
                                      <td className="p-2 text-slate-700 text-xs font-mono">{String(d[k] || '')}</td>
                                    </tr>
                                  ))}
                              </tbody>
                            </table>
                          </div>
                        );
                      }

                      const tableRows = [];
                      const pushRow = (label, value, force = false) => {
                        const v = value === undefined || value === null ? '' : value;
                        if (!force && (Array.isArray(v) ? v.length === 0 : String(v).trim() === '')) return;
                        tableRows.push(
                          <tr key={label} className="border-t border-slate-100">
                            <td className="p-2 text-slate-600 font-semibold text-xs">{label}</td>
                            <td className="p-2 text-slate-700 text-xs font-mono">{Array.isArray(v) ? v.join(', ') : String(v)}</td>
                          </tr>
                        );
                      };

                      pushRow('documentId', d.documentId);
                      pushRow('documentType', d.documentType);
                      pushRow('ocrConfidence', d.ocrConfidence);
                      pushRow('missingFields', d.missingFields, true);
                      pushRow('missingDocumentTypes', d.missingDocumentTypes, true);
                      pushRow('siret', d.siret);
                      pushRow('companyName', d.companyName);
                      pushRow('accountHolder', d.accountHolder);
                      pushRow('iban', d.iban);
                      pushRow('expirationDate', d.expirationDate);
                      pushRow('checkedAt', d.checkedAt);
                      pushRow('amountHt', d.amountHt);
                      pushRow('vatRate', d.vatRate);
                      pushRow('expectedTotalTtc', d.expectedTotalTtc);
                      pushRow('detectedTotalTtc', d.detectedTotalTtc);
                      pushRow('quoteTotalTtc', d.quoteTotalTtc);
                      pushRow('invoiceTotalTtc', d.invoiceTotalTtc);
                      pushRow('difference', d.difference);
                      pushRow('triggeredHighRiskRules', d.triggeredHighRiskRules);

                      if (tableRows.length > 0) {
                        return (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm border border-slate-200 rounded-xl overflow-hidden">
                              <tbody>{tableRows}</tbody>
                            </table>
                          </div>
                        );
                      }

                      return (
                        <pre className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-700 overflow-auto">
                          {JSON.stringify(d, null, 2)}
                        </pre>
                      );
                    };

                    const severityToColors = (sev) => {
                      const s = String(sev || '').toLowerCase();
                      if (s === 'high' || s === 'critical') return { bg: 'bg-red-50', bd: 'border-red-200', tx: 'text-red-700' };
                      if (s === 'medium') return { bg: 'bg-orange-50', bd: 'border-orange-200', tx: 'text-orange-700' };
                      if (s === 'low') return { bg: 'bg-slate-50', bd: 'border-slate-200', tx: 'text-slate-700' };
                      return { bg: 'bg-slate-50', bd: 'border-slate-200', tx: 'text-slate-700' };
                    };

                    return (
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-sm font-extrabold text-slate-900">Anomalies (preuves)</h3>
                          {deduped.length === 0 ? (
                            <div className="text-sm text-slate-600 mt-2">Aucune anomalie détectée.</div>
                          ) : (
                            <div className="mt-3 space-y-3">
                              {deduped.map((a, idx) => {
                                const c = severityToColors(a.severity);
                                return (
                                  <div key={idx} className="border border-slate-200 rounded-2xl overflow-hidden">
                                    <div className="p-4 bg-slate-50 flex items-start justify-between gap-4">
                                      <div className="min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                          <span className={`px-2.5 py-1 rounded-xl border text-[10px] font-semibold ${c.bg} ${c.bd} ${c.tx}`}>
                                            {String(a.severity || '').toUpperCase()}
                                          </span>
                                          <span className="text-xs font-mono text-slate-700 font-semibold">
                                            {a.anomalyCode}
                                          </span>
                                        </div>
                                        <p className="mt-2 text-sm text-slate-700 font-medium">
                                          {a.message}
                                        </p>
                                      </div>
                                      <div className="text-right">
                                        <div className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold">
                                          Score
                                        </div>
                                        <div className="text-sm font-bold text-indigo-700 tabular-nums">{a.score ?? 0}</div>
                                      </div>
                                    </div>
                                    <div className="p-4 border-t border-slate-200">
                                      {renderDetails(a.details)}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>

                        <div>
                          <h3 className="text-sm font-extrabold text-slate-900">Documents utilisés</h3>
                          <div className="mt-3 space-y-3">
                            {(selectedSupplierDetails.documents || []).map((doc, idx) => (
                              <div key={`${doc.documentType || 'doc'}_${idx}`} className="border border-slate-200 rounded-2xl p-4">
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <div className="text-xs font-mono text-slate-600 font-semibold">
                                      Type: {doc.documentType}
                                    </div>
                                    <div className="text-sm font-bold text-slate-900">
                                      {doc.extractedData?.company_name || doc.extractedData?.companyName || '—'}
                                    </div>
                                    <div className="text-xs text-slate-500 font-mono mt-1">
                                      SIRET: {doc.extractedData?.siret || '—'}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold">
                                      Statut document
                                    </div>
                                    <div className="text-sm font-bold text-indigo-700">{doc.validation?.status || 'UNKNOWN'}</div>
                                  </div>
                                </div>

                                <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2">
                                  {doc.extractedData?.total_ttc !== undefined && (
                                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-2">
                                      <div className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold">Total TTC</div>
                                      <div className="text-xs font-mono text-slate-700 font-semibold">{doc.extractedData?.total_ttc}€</div>
                                    </div>
                                  )}
                                  {doc.extractedData?.expiration_date && (
                                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-2">
                                      <div className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold">Expiration</div>
                                      <div className="text-xs font-mono text-slate-700 font-semibold">{doc.extractedData.expiration_date}</div>
                                    </div>
                                  )}
                                  {doc.extractedData?.iban && (
                                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-2">
                                      <div className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold">IBAN</div>
                                      <div className="text-xs font-mono text-slate-700 font-semibold break-all">{doc.extractedData.iban}</div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CRMView;
