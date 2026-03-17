import React from 'react';

const StatCard = (props) => {
  const myLabel = props.label;
  const myValue = props.value;
  const myAccentColor = props.accent;

  let finalColor = 'text-slate-800';
  if (myAccentColor !== undefined && myAccentColor !== null) {
     finalColor = myAccentColor;
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-3 flex flex-col gap-0.5 shadow-sm">
      <span className={'text-xl font-bold ' + finalColor}>{myValue}</span>
      <span className="text-xs text-slate-500">{myLabel}</span>
    </div>
  );
};

export default StatCard;
