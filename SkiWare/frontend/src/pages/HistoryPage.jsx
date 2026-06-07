import { useState, useEffect } from 'react';

export default function HistoryPage({ currentUser, onViewAssessment, onBackToHome }) {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [loadingId, setLoadingId] = useState(null);

  useEffect(() => {
    if (!currentUser) return;
    fetch(`/api/assessments?userId=${encodeURIComponent(currentUser.id)}`)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => setAssessments(data.assessments))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [currentUser]);

  const handleCardClick = async (id) => {
    setLoadingId(id);
    try {
      const res = await fetch(`/api/assessments/${id}`);
      if (res.ok) {
        const detail = await res.json();
        onViewAssessment(detail.request, detail.response);
      }
    } catch {
      // ignore
    } finally {
      setLoadingId(null);
    }
  };

  if (!currentUser) {
    return (
      <main className="main-container">
        <section className="history-page">
          <h1>Assessment History</h1>
          <p className="lead">Sign in to view your past assessments.</p>
          <button className="btn-secondary" onClick={onBackToHome}>
            Back to home
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="main-container">
      <section className="history-page">
        <div className="page-header">
          <h1>Assessment History</h1>
          <p>Your past gear assessments.</p>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner" aria-hidden="true" />
            <p>Loading history…</p>
          </div>
        ) : error ? (
          <div className="loading-state">
            <p>Failed to load assessment history.</p>
          </div>
        ) : assessments.length === 0 ? (
          <p className="lead">No assessments yet. Run one to get started.</p>
        ) : (
          <div className="history-list">
            {assessments.map((a) => (
              <button
                key={a.id}
                className="history-card"
                onClick={() => handleCardClick(a.id)}
                disabled={loadingId === a.id}
              >
                <div className="history-card-top">
                  <span className={`safety-badge small ${a.safeToSki ? 'safe' : 'unsafe'}`}>
                    {a.safeToSki ? 'Safe' : 'Unsafe'}
                  </span>
                  <span className={`verdict-pill verdict-${a.verdict.toLowerCase()}`}>
                    {a.verdict}
                  </span>
                </div>
                <div className="history-card-body">
                  <strong>{a.brand || capitalize(a.equipmentType)}</strong>
                  <span className="history-severity">Severity {a.severity}/5</span>
                </div>
                <div className="history-card-date">
                  {new Date(a.createdAt).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="results-buttons" style={{ marginTop: '32px' }}>
          <button className="btn-secondary" onClick={onBackToHome}>
            Back to home
          </button>
        </div>
      </section>
    </main>
  );
}

function capitalize(value) {
  if (!value) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}
