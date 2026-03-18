import React from 'react';
import { Routes, Route } from 'react-router-dom';
import CRMView from './pages/CRMView.jsx';
import ConformityView from './pages/ConformityView.jsx';
import ValidationResultsView from './pages/ValidationResultsView.jsx';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<CRMView />} />
      <Route path="/conformity" element={<ConformityView />} />
      <Route path="/validation" element={<ValidationResultsView />} />
    </Routes>
  );
};

export default App;
