import { useState } from 'react';
import './App.css';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import FormPage from './pages/FormPage';
import ResultsPage from './pages/ResultsPage';
import FindShopPage from './pages/FindShopPage';
import UserPage from './pages/UserPage';
import HistoryPage from './pages/HistoryPage';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [formData, setFormData] = useState(null);
  const [results, setResults] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [assessmentError, setAssessmentError] = useState(false);
  const [userPageInitialView, setUserPageInitialView] = useState(null);

  const handleNavigate = (page) => {
    if (page === 'home') {
      handleBackToHome();
      return;
    }
    if (page === 'signIn') {
      setUserPageInitialView('login');
      setCurrentPage('user');
      return;
    }
    if (page === 'createAccount') {
      setUserPageInitialView('create');
      setCurrentPage('user');
      return;
    }
    if (page === 'user') {
      setUserPageInitialView(null);
    }
    setCurrentPage(page);
  };

  const handleLogin = (user) => setCurrentUser(user);
  const handleLogout = () => setCurrentUser(null);

  const handleStartAssessment = () => setCurrentPage('form');
  const handleFindShop = () => setCurrentPage('findShop');

  const handleFormSubmit = async (data) => {
    setFormData(data);
    setResults(null);
    setAssessmentError(false);
    setCurrentPage('results');

    try {
      const url = currentUser
        ? `/api/assess?userId=${encodeURIComponent(currentUser.id)}`
        : '/api/assess';
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setResults(await response.json());
      } else {
        setAssessmentError(true);
      }
    } catch (error) {
      console.error('Assessment request failed', error);
      setAssessmentError(true);
    }
  };

  const handleViewAssessment = (requestData, responseData) => {
    setFormData(requestData);
    setResults(responseData);
    setAssessmentError(false);
    setCurrentPage('results');
  };

  const handleBackToHome = () => {
    setCurrentPage('home');
    setFormData(null);
    setResults(null);
    setAssessmentError(false);
  };

  const handleNewAssessment = () => {
    setCurrentPage('form');
    setResults(null);
    setAssessmentError(false);
  };

  return (
    <div className="app">
      <Header
        currentPage={currentPage}
        onNavigate={handleNavigate}
        currentUser={currentUser}
        onLogout={handleLogout}
      />
      {currentPage === 'home' && (
        <HomePage
          onStartAssessment={handleStartAssessment}
          onFindShop={handleFindShop}
        />
      )}
      {currentPage === 'form' && (
        <FormPage
          onSubmit={handleFormSubmit}
          onCancel={handleBackToHome}
          currentUser={currentUser}
        />
      )}
      {currentPage === 'results' && (
        <ResultsPage
          formData={formData}
          results={results}
          error={assessmentError}
          onBackToHome={handleBackToHome}
          onNewAssessment={handleNewAssessment}
        />
      )}
      {currentPage === 'findShop' && <FindShopPage onBackToHome={handleBackToHome} />}
      {currentPage === 'history' && (
        <HistoryPage
          currentUser={currentUser}
          onViewAssessment={handleViewAssessment}
          onBackToHome={handleBackToHome}
        />
      )}
      {currentPage === 'user' && (
        <UserPage
          key={userPageInitialView}
          initialView={userPageInitialView}
          currentUser={currentUser}
          onLogin={handleLogin}
          onLogout={handleLogout}
          onBackToHome={handleBackToHome}
        />
      )}
    </div>
  );
}

export default App;
