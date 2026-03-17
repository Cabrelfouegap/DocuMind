import React, { useEffect, useState } from 'react';
import { fetchDocuments as getDocs } from '../api/documents.js';
import StatCard from '../components/StatCard.jsx';
import FilterBar from '../components/FilterBar.jsx';
import SupplierCard from '../components/SupplierCard.jsx';

const CRMView = () => {
  const [tousLesDocs, setTousLesDocs] = useState([]);
  const [enChargement, setEnChargement] = useState(true);
  const [recherche, setRecherche] = useState('');

  useEffect(() => {
    getDocs()
      .then((reponse) => {
        setTousLesDocs(reponse.data);
        setEnChargement(false);
      })
      .catch((err) => {
        console.error("Erreur chargement:", err);
        setEnChargement(false);
      });
  }, []);

  const creerListeFournisseurs = () => {
    const dictionnaire = {};

    for (let i = 0; i < tousLesDocs.length; i++) {
      const doc = tousLesDocs[i];
      const siret = doc.extractedData?.siret || 'Sans SIRET';

      let nomFournisseur = 'Fournisseur Inconnu';
      if (doc.originalName.toLowerCase().includes('vigilance')) {
        nomFournisseur = 'URSSAF / Administration';
      } else if (doc.originalName.toLowerCase().includes('contrat')) {
        nomFournisseur = 'Service Prestation Plus';
      } else if (doc.originalName.toLowerCase().includes('facture')) {
        const morceaux = doc.originalName.split('_');
        if (morceaux.length > 2) {
          nomFournisseur = morceaux[1];
        } else {
          nomFournisseur = 'Fournisseur Divers';
        }
      }

      if (!dictionnaire[siret]) {
        dictionnaire[siret] = {
          siret: siret,
          name: nomFournisseur,
          totalAmount: 0,
          documents: []
        };
      }

      dictionnaire[siret].documents.push(doc);

      if (doc.status === 'Conforme' && doc.extractedData?.amountTTC) {
        dictionnaire[siret].totalAmount = dictionnaire[siret].totalAmount + doc.extractedData.amountTTC;
      }
    }

    return Object.values(dictionnaire);
  };

  const laListeComplete = creerListeFournisseurs();

  const fournisseursFiltrés = laListeComplete.filter((f) => {
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
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default CRMView;
