import React from 'react';

const FilterBar = (props) => {
  const texteRecherche = props.search;
  const setTexteRecherche = props.onSearch;
  
  const filtreStatut = props.status;
  const setFiltreStatut = props.onStatus;
  
  const lesComptages = props.counts;

  const quandOnTape = (event) => {
    setTexteRecherche(event.target.value);
  };

  const tousLesStatus = ['Tous', 'En attente', 'Warning', 'Conforme', 'Non conforme'];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
      <div className="relative flex-1 max-w-xs">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8" /><path strokeLinecap="round" d="M21 21l-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={texteRecherche}
          onChange={quandOnTape}
          placeholder={props.placeholder || "Rechercher un fichier…"}
          className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition-colors"
        />
      </div>

      {!props.hideStatus && (
        <div className="flex gap-1.5 flex-wrap">
          {tousLesStatus.map((nomStatut) => {
            let nombre = 0;
            if (nomStatut === 'Tous') {
              nombre = lesComptages?.total || 0;
            } else {
              nombre = lesComptages?.[nomStatut] || 0;
            }

            const estSelectionne = (filtreStatut === nomStatut);

            let classesBouton = 'border border-slate-200 ';
            if (nomStatut === 'Tous') {
              if (estSelectionne) classesBouton += 'bg-slate-800 text-white border-slate-800';
              else classesBouton += 'bg-white text-slate-600 hover:bg-slate-100';
            } else if (nomStatut === 'En attente') {
              if (estSelectionne) classesBouton += 'bg-slate-600 text-white border-slate-600';
              else classesBouton += 'bg-white text-slate-700 hover:bg-slate-100';
            } else if (nomStatut === 'Warning') {
              if (estSelectionne) classesBouton += 'bg-orange-500 text-white border-orange-500';
              else classesBouton += 'bg-white text-orange-700 hover:bg-orange-50';
            } else if (nomStatut === 'Conforme') {
              if (estSelectionne) classesBouton += 'bg-emerald-600 text-white border-emerald-600';
              else classesBouton += 'bg-white text-emerald-700 hover:bg-emerald-50';
            } else if (nomStatut === 'Non conforme') {
              if (estSelectionne) classesBouton += 'bg-red-600 text-white border-red-600';
              else classesBouton += 'bg-white text-red-700 hover:bg-red-50';
            }

            return (
              <button
                key={nomStatut}
                onClick={() => { setFiltreStatut(nomStatut); }}
                className={'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ' + classesBouton}
              >
                {nomStatut}
                <span className={'text-[10px] font-bold tabular-nums ' + (estSelectionne ? 'opacity-80' : 'opacity-60')}>
                  {nombre}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FilterBar;
