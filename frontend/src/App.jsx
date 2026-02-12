import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import ResultPage from './pages/ResultPage';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/results/:id" element={<ResultPage />} />
        <Route path="/videos" element={
          <div style={{ color: 'white', padding: '2rem', textAlign: 'center' }}>
            <h2>Video History</h2>
            <p>Coming soon...</p>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
