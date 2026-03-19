import React, { useEffect, useMemo, useRef, useState } from 'react';
import { FaEye } from 'react-icons/fa';
import {
  fetchDocuments as getDocuments,
  uploadDocument as sendFiles,
  updateDocument as updateDoc,
  analyzeDocument as runIA
} from '../api/documents.js';

export default function ConformityView() {
  const [listeDocs, setListeDocs] = useState([]);
  const [texteRecherche, setTexteRecherche] = useState('');
  const [ongletActif, setOngletActif] = useState('Tous');
  const [estEnTrainDeCharger, setEstEnTrainDeCharger] = useState(true);
  const [enTrainDUploader, setEnTrainDUploader] = useState(false);
  const [estAuDessus, setEstAuDessus] = useState(false);
  const [idsEnCoursDAnalyse, setIdsEnCoursDAnalyse] = useState([]);

  const inputFichierRef = useRef(null);

  const chargerDocs = async () => {
    try {
      const reponse = await getDocuments();
      setListeDocs(reponse.data);
    } catch (err) {
      console.error('Erreur:', err);
    } finally {
      setEstEnTrainDeCharger(false);
    }
  };

  useEffect(() => {
    chargerDocs();
  }, []);

  const documentsAffiches = useMemo(() => {
    return listeDocs.filter((doc) => {
      const okStatus = ongletActif === 'Tous' || doc.status === ongletActif;
      const okRecherche = doc.originalName.toLowerCase().includes(texteRecherche.toLowerCase());
      return okStatus && okRecherche;
    });
  }, [listeDocs, texteRecherche, ongletActif]);

  const total = listeDocs.length;
  const attente = listeDocs.filter((d) => d.status === 'En attente').length;
  const warning = listeDocs.filter((d) => d.status === 'Warning').length;
  const conforme = listeDocs.filter((d) => d.status === 'Conforme').length;
  const nonConforme = listeDocs.filter((d) => d.status === 'Non conforme').length;

  const envoyerFichiers = async (fichiers) => {
    if (!fichiers?.length) return;
    const formData = new FormData();
    Array.from(fichiers).forEach((fichier) => formData.append('files', fichier));
    setEnTrainDUploader(true);
    try {
      await sendFiles(formData);
      await chargerDocs();
    } catch (e) {
      console.error('Upload raté', e);
    } finally {
      setEnTrainDUploader(false);
    }
  };

  const lancerIA = async (document) => {
    setIdsEnCoursDAnalyse((precedent) => [...precedent, document._id]);
    try {
      const reponseIA = await runIA(document._id);
      const docsAnalyses = reponseIA.data;
      setListeDocs((precedent) =>
        precedent.map((item) => (item._id === document._id ? { ...item, ...docsAnalyses } : item))
      );
    } catch (erreur) {
      console.error('IA Erreur', erreur);
    } finally {
      setIdsEnCoursDAnalyse((precedent) => precedent.filter((id) => id !== document._id));
      await chargerDocs();
    }
  };

  const changerLeStatut = async (document, nouveauStatut) => {
    let explication = '';
    if (nouveauStatut === 'Non conforme') {
      explication = window.prompt('Pourquoi refusez-vous ce document ?') || '';
    }

    await updateDoc(document._id, {
      status: nouveauStatut,
      reason: explication,
      aiGenerated: false
    });

    setListeDocs((precedent) =>
      precedent.map((item) =>
        item._id === document._id
          ? { ...item, status: nouveauStatut, reason: explication, aiGenerated: false }
          : item
      )
    );
  };

  return (
    <div style={container}>
      <Header />
      <main style={mainContent}>
        <section style={statsSection}>
          <StatCircle label="Total" value={total} />
          <StatCircle label="En attente" value={attente} />
          <StatCircle label="Warnings" value={warning} />
          <StatCircle label="Conformes" value={conforme} />
          <StatCircle label="Refusés" value={nonConforme} />
        </section>

        <div
          style={{ ...uploadZone, ...(estAuDessus ? uploadDragOver : {}) }}
          onDragOver={(e) => {
            e.preventDefault();
            setEstAuDessus(true);
          }}
          onDragLeave={() => setEstAuDessus(false)}
          onDrop={(e) => {
            e.preventDefault();
            setEstAuDessus(false);
            envoyerFichiers(e.dataTransfer.files);
          }}
          onClick={() => inputFichierRef.current?.click()}
        >
          <input
            ref={inputFichierRef}
            type="file"
            hidden
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
            multiple
            onChange={(e) => envoyerFichiers(e.target.files)}
          />
          {enTrainDUploader ? 'Envoi...' : 'Glisser ou cliquer pour uploader (PDF, Word ou Images)'}
        </div>

        <div style={filterContainer}>
          <input
            type="text"
            placeholder="Rechercher un document..."
            value={texteRecherche}
            onChange={(e) => setTexteRecherche(e.target.value)}
            style={searchInput}
          />
          <select
            value={ongletActif}
            onChange={(e) => setOngletActif(e.target.value)}
            style={statusSelectFilter}
          >
            <option value="Tous">Tous</option>
            <option value="En attente">En attente</option>
            <option value="Warning">Warning</option>
            <option value="Conforme">Conforme</option>
            <option value="Non conforme">Non conforme</option>
          </select>
        </div>

        <div style={tableContainer}>
          {estEnTrainDeCharger ? (
            <div style={loadingStyle}>Chargement...</div>
          ) : listeDocs.length === 0 ? (
            <div style={emptyStyle}>Aucun document.</div>
          ) : documentsAffiches.length === 0 ? (
            <div style={emptyStyle}>Aucun résultat.</div>
          ) : (
            <table style={tableStyle}>
              <thead style={theadStyle}>
                <tr>
                  <th style={{ width: '22%', ...thStyle }}>Fichier</th>
                  <th style={{ width: '10%', ...thStyle }}>Type</th>
                  <th style={{ width: '10%', textAlign: 'center', ...thStyle }}>Date</th>
                  <th style={{ width: '12%', textAlign: 'center', ...thStyle }}>Statut</th>
                  <th style={{ width: '15%', textAlign: 'right', ...thStyle }}>Données Extraites</th>
                  <th style={{ width: '15%', ...thStyle }}>Détails/Motif</th>
                  <th style={{ width: '6%', textAlign: 'center', ...thStyle }}>Aperçu</th>
                  <th style={{ width: '15%', textAlign: 'right', ...thStyle }}>Décision</th>
                </tr>
              </thead>
              <tbody>
                {documentsAffiches.map((doc) => {
                  const estEnCoursDAnalyse = idsEnCoursDAnalyse.includes(doc._id);
                  const details = doc.reason || doc.extractedData?.inconsistencyNote || '—';

                  return (
                    <tr key={doc._id} style={trStyle}>
                      <td style={tdStyle}>{doc.originalName}</td>
                      <td style={tdStyle}>{doc.type || '—'}</td>
                      <td style={{ ...tdStyle, textAlign: 'center' }}>
                        {doc.createdAt
                          ? new Date(doc.createdAt).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                          : '—'}
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'center' }}>
                        <span style={statusTag(doc.status)}>{doc.status}</span>
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        {doc.extractedData?.amountTTC ? `${doc.extractedData.amountTTC}€` : '—'}
                      </td>
                      <td style={tdStyle} title={details}>
                        {doc.reason ? doc.reason : doc.extractedData?.inconsistencyNote ? '⚠️ Incohérence' : '—'}
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'center' }}>
                        <a
                          href={`/uploads/${doc.filename}`}
                          target="_blank"
                          rel="noreferrer"
                          style={viewButton}
                        >
                          <FaEye size={14} />
                        </a>
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        {doc.status === 'En attente' ? (
                          <button
                            style={analysisButton}
                            onClick={() => lancerIA(doc)}
                            disabled={estEnCoursDAnalyse}
                          >
                            {estEnCoursDAnalyse ? '...' : 'IA'}
                          </button>
                        ) : (
                          <div style={decisionWrap}>
                            {doc.aiGenerated && <span style={aiHintDot} title="Suggestion IA" />}
                            <select
                              value={doc.status}
                              onChange={(e) => changerLeStatut(doc, e.target.value)}
                              style={statusSelect}
                            >
                              <option value="Conforme">OK</option>
                              <option value="Warning">Warning</option>
                              <option value="Non conforme">Refus</option>
                              <option value="En attente">?</option>
                            </select>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}

const Header = () => (
  <header style={headerStyle}>
    <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
      <div style={logoBox}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="36"
          height="36"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#fff"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M8 12l3 3 5-5" />
        </svg>
      </div>
      <h1 style={headerTitle}>Documind Conformite</h1>
    </div>
    <a href="/" style={crmLinkStyle}>
      ← CRM
    </a>
  </header>
);

function StatCircle({ label, value }) {
  return (
    <div style={statCircle}>
      <div style={statValue}>{value}</div>
      <div style={statLabel}>{label}</div>
    </div>
  );
}

const container = {
  fontFamily: "'Inter', sans-serif",
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column'
};
const mainContent = {
  marginTop: 72,
  marginLeft: 16,
  flexGrow: 1,
  padding: '2rem 3rem',
  background: '#f9fafb'
};
const headerStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  height: '56px',
  backgroundColor: '#fff',
  display: 'flex',
  alignItems: 'center',
  padding: '0 1rem',
  boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
  zIndex: 1000
};
const logoBox = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '56px',
  height: '56px',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: '#22335E',
  borderRadius: 0,
  zIndex: 1001
};
const headerTitle = {
  fontSize: '1.3rem',
  fontWeight: 400,
  marginLeft: '50px',
  color: '#22335E',
  fontFamily: "'Poppins', sans-serif'"
};
const crmLinkStyle = {
  fontSize: '11px',
  color: '#6b7280',
  textDecoration: 'none',
  padding: '4px 8px',
  borderRadius: 9999,
  border: '1px solid #e5e7eb',
  backgroundColor: '#f9fafb',
  cursor: 'pointer'
};
const statsSection = {
  display: 'flex',
  gap: '2rem',
  justifyContent: 'center',
  marginBottom: '2rem',
  flexWrap: 'wrap'
};
const statCircle = {
  width: 120,
  height: 120,
  borderRadius: '50%',
  background: '#fff',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  boxShadow: '0 4px 10px rgba(0,0,0,0.05)',
  marginBottom: '1rem'
};
const statValue = { fontSize: '2rem', fontWeight: 300, color: '#111827' };
const statLabel = { fontSize: '0.9rem', fontWeight: 500, color: '#6b7280', textAlign: 'center' };
const uploadZone = {
  display: 'flex',
  justifyContent: 'center',
  flexWrap: 'wrap',
  border: '2px dashed #9ca3af',
  padding: '2rem',
  borderRadius: 16,
  textAlign: 'center',
  cursor: 'pointer',
  margin: '1em 8rem 2em 8rem',
  color: '#6b7280'
};
const uploadDragOver = { borderColor: '#2563eb', background: '#eff6ff', color: '#1e3a8a' };
const tableContainer = {
  overflowX: 'auto',
  borderRadius: 12,
  background: '#fff',
  boxShadow: '0 2px 6px rgba(0,0,0,0.05)'
};
const tableStyle = { width: '100%', borderCollapse: 'collapse' };
const theadStyle = {
  backgroundColor: '#f1f5f9',
  color: '#64748b',
  fontSize: '9px',
  textTransform: 'uppercase',
  letterSpacing: '0.5px'
};
const thStyle = { padding: '0.5rem 0.75rem', fontWeight: 500 };
const trStyle = { borderBottom: '1px solid #e5e7eb' };
const tdStyle = {
  padding: '0.5rem 0.75rem',
  fontSize: '13px',
  color: '#111827',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis'
};
const statusTag = (status) => ({
  fontSize: '0.85rem',
  padding: '0.2rem 0.6rem',
  borderRadius: 12,
  color:
    status === 'Conforme'
      ? '#047857'
      : status === 'Non conforme'
        ? '#b91c1c'
        : status === 'Warning'
          ? '#c2410c'
          : '#4b5563',
  background:
    status === 'Conforme'
      ? '#d1fae5'
      : status === 'Non conforme'
        ? '#fee2e2'
        : status === 'Warning'
          ? '#ffedd5'
          : '#e5e7eb',
  display: 'inline-block'
});
const analysisButton = {
  padding: '0.4rem 1rem',
  borderRadius: 12,
  background: '#ede9fe',
  color: '#7c3aed',
  border: 'none',
  cursor: 'pointer',
  fontWeight: 400
};
const decisionWrap = { display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.35rem' };
const aiHintDot = { width: 6, height: 6, borderRadius: 9999, background: '#a78bfa', display: 'inline-block' };
const statusSelect = {
  borderRadius: 8,
  padding: '0.3rem 0.6rem',
  border: '1px solid #d1d5db',
  fontSize: '0.7rem'
};
const viewButton = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '0.2rem 0.4rem',
  borderRadius: 8,
  background: '#e0f2fe',
  color: '#0369a1',
  fontSize: '0.85rem',
  textDecoration: 'none',
  justifyContent: 'center'
};
const loadingStyle = { textAlign: 'center', color: '#6b7280', padding: '2rem' };
const emptyStyle = { textAlign: 'center', color: '#6b7280', padding: '2rem' };
const filterContainer = {
  display: 'flex',
  gap: '1rem',
  marginBottom: '1rem',
  flexWrap: 'wrap',
  fontFamily: "'Inter', sans-serif",
  fontSize: '13px'
};
const searchInput = { width: '400px', padding: '0.5rem 1rem', borderRadius: 8, border: '1px solid #d1d5db' };
const statusSelectFilter = {
  padding: '0.5rem 1rem',
  borderRadius: 8,
  border: '1px solid #d1d5db',
  minWidth: 160
};
