import React from 'react';

const StatusBadge = (props) => {
  const myStatus = props.status;

  let myBackgroundColor = 'bg-amber-100';
  let myTextColor = 'text-amber-700';
  let myDotColor = 'bg-amber-500';

  if (myStatus === 'Conforme') {
    myBackgroundColor = 'bg-emerald-100';
    myTextColor = 'text-emerald-700';
    myDotColor = 'bg-emerald-500';
  } else if (myStatus === 'Non conforme') {
    myBackgroundColor = 'bg-red-100';
    myTextColor = 'text-red-700';
    myDotColor = 'bg-red-500';
  } else {
    myBackgroundColor = 'bg-amber-100';
    myTextColor = 'text-amber-700';
    myDotColor = 'bg-amber-500';
  }

  return (
    <span className={'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ' + myBackgroundColor + ' ' + myTextColor}>
      <span className={'w-1.5 h-1.5 rounded-full ' + myDotColor}></span>
      {myStatus}
    </span>
  );
};

export default StatusBadge;
