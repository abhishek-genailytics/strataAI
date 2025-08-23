import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="bg-blue-600 text-white p-4">
          <h1 className="text-2xl font-bold">StrataAI</h1>
          <p className="text-sm">Unified AI API Gateway</p>
        </header>
        
        <main className="container mx-auto p-4">
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

const Home = () => (
  <div className="text-center">
    <h2 className="text-3xl font-bold mb-4">Welcome to StrataAI</h2>
    <p className="text-gray-600">Your unified gateway to AI providers</p>
  </div>
);

export default App;
