import { useState, useEffect } from 'react';

const RETAILERS = [
  { name: 'Amazon', url: (q) => `https://www.amazon.com/s?k=${encodeURIComponent(q)}` },
  { name: 'REI', url: (q) => `https://www.rei.com/search?q=${encodeURIComponent(q)}` },
  { name: 'evo', url: (q) => `https://www.evo.com/search?q=${encodeURIComponent(q)}` },
  { name: 'Backcountry', url: (q) => `https://www.backcountry.com/search?q=${encodeURIComponent(q)}` },
  { name: 'Peter Glenn', url: (q) => `https://www.peterglenn.com/search?q=${encodeURIComponent(q)}` },
];

export default function ResultsPage({ formData, results, error, onBackToHome, onNewAssessment }) {
  if (!formData) {
    return <main className="main-container">Loading…</main>;
  }

  const equipmentName = buildEquipmentName(formData);

  return (
    <main className="main-container">
      <section className="results-page">
        <div className="assessment-summary">
          <div className="section-title" style={{ color: 'rgba(255,255,255,0.55)' }}>
            Your assessment
          </div>
          <h2>{equipmentName}</h2>
          <p className="summary-subtitle">Based on what you told us about your setup.</p>
          <div className="summary-grid">
            <SummaryItem label="Snow" value={capitalize(formData.snowCondition || formData.terrain)} />
            <SummaryItem label="Terrain" value={capitalize(formData.terrainType || formData.style)} />
            <SummaryItem label="Days since wax" value={String(formData.daysSinceWax)} />
            <SummaryItem label="Days since edge" value={String(formData.daysSinceEdgeWork)} />
          </div>
        </div>

        {error ? (
          <div className="loading-state">
            <p>Something went wrong — please try again.</p>
          </div>
        ) : !results ? (
          <div className="loading-state">
            <div className="loading-spinner" aria-hidden="true" />
            <p>Analyzing your gear…</p>
          </div>
        ) : (
          <>
            <div className="verdict-card">
              <div className="verdict-status">
                <span className={`safety-badge ${results.safeToSki ? 'safe' : 'unsafe'}`}>
                  {results.safeToSki ? 'Safe to ski' : 'Do not ski'}
                </span>
                <SeverityDots severity={results.severity} />
              </div>
              <div className="verdict-details">
                <VerdictDetail
                  label="Verdict"
                  value={results.verdict === 'DIY' ? 'DIY repair' : 'Shop repair'}
                  highlight={results.verdict}
                />
                <VerdictDetail label="Est. cost" value={results.shopCostEstimate} />
                <VerdictDetail label="Est. time" value={results.timeEstimate} />
                <VerdictDetail label="Skill level" value={capitalize(results.skillLevel)} />
              </div>
            </div>

            {results.recommendations?.length > 0 && (
              <div className="recommendations-section">
                <h2>Recommendations</h2>
                {results.recommendations.map((rec, index) => (
                  <article key={`${rec.title}-${index}`} className="recommendation-card">
                    <div
                      className={`recommendation-icon ${rec.severity.toLowerCase()}`}
                      aria-hidden="true"
                    >
                      <SeverityIcon severity={rec.severity} />
                    </div>
                    <div className="recommendation-content">
                      <div className="recommendation-heading">
                        <h3>{rec.title}</h3>
                        <span className={`severity-badge ${rec.severity.toLowerCase()}`}>
                          {rec.severity}
                        </span>
                      </div>
                      <p className="recommendation-description">{rec.description}</p>
                    </div>
                  </article>
                ))}
              </div>
            )}

            {results.repairSteps?.length > 0 && (
              <div className="repair-section">
                <h2>Repair steps</h2>
                <ol className="repair-steps-list">
                  {results.repairSteps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
              </div>
            )}

            {results.partsList?.length > 0 && (
              <div className="parts-section">
                <h2>Parts &amp; materials</h2>
                <div className="parts-list">
                  {results.partsList.map((part, index) => (
                    <div key={index} className="part-card">
                      <div className="part-name">{part.name}</div>
                      <div className="part-links">
                        {RETAILERS.map((retailer) => (
                          <a
                            key={retailer.name}
                            href={retailer.url(part.searchQuery)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="part-link"
                          >
                            {retailer.name}
                          </a>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {results.youtubeSuggestions?.length > 0 && (
              <div className="youtube-section">
                <h2>Video guides</h2>
                <ul className="youtube-list">
                  {results.youtubeSuggestions.map((query, index) => (
                    <li key={index}>
                      <a
                        href={`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="youtube-link"
                      >
                        <YoutubeIcon />
                        {query}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {results && <NearbyShops />}

        <div className="results-buttons">
          <button className="btn-secondary" onClick={onBackToHome}>
            Back to home
          </button>
          <button className="btn-primary" onClick={onNewAssessment}>
            New assessment
          </button>
        </div>
      </section>
    </main>
  );
}

function NearbyShops() {
  const [status, setStatus] = useState('locating');
  const [shops, setShops] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    async function load() {
      if (!navigator.geolocation) {
        setStatus('unsupported');
        return;
      }

      setStatus('locating');
      let latitude, longitude;

      try {
        const getPosition = (opts) =>
          new Promise((resolve, reject) =>
            navigator.geolocation.getCurrentPosition(resolve, reject, opts)
          );
        try {
          const pos = await getPosition({ enableHighAccuracy: false, timeout: 1500, maximumAge: Infinity });
          latitude = pos.coords.latitude;
          longitude = pos.coords.longitude;
        } catch {
          const pos = await getPosition({ enableHighAccuracy: false, timeout: 15000, maximumAge: 0 });
          latitude = pos.coords.latitude;
          longitude = pos.coords.longitude;
        }
      } catch (err) {
        if (err.code === 1) { setStatus('denied'); return; }
        setErrorMsg('Could not determine your location.');
        setStatus('error');
        return;
      }

      setStatus('loading');
      try {
        const res = await fetch(`/api/shops/nearest?lat=${latitude}&lon=${longitude}&ranked=true`);
        if (!res.ok) throw new Error('Server error');
        const data = await res.json();
        setShops(data);
        setStatus('success');
      } catch {
        setErrorMsg('Could not load nearby shops.');
        setStatus('error');
      }
    }

    load();
  }, []);

  if (status === 'unsupported' || status === 'denied') return null;

  return (
    <div className="nearby-shops-section">
      <h2>Nearby shops</h2>
      {(status === 'locating' || status === 'loading') && (
        <p className="shop-status-msg">
          {status === 'locating' ? 'Detecting your location…' : 'Searching for nearby shops…'}
        </p>
      )}
      {status === 'error' && <p className="shop-error-msg">{errorMsg}</p>}
      {status === 'success' && shops.length === 0 && (
        <p className="shop-status-msg">No shops found within 15 miles.</p>
      )}
      {status === 'success' && shops.length > 0 && (
        <ul className="shop-list">
          {shops.map((shop, i) => (
            <li key={i} className="shop-card">
              <div className="shop-card-header">
                <span className="shop-card-name">{shop.name}</span>
                <span className="shop-distance">{shop.distance_miles} mi</span>
              </div>
              {shop.rating != null && (
                <div className="shop-rating">
                  ★ {shop.rating.toFixed(1)}
                  {shop.user_rating_count != null && (
                    <span className="shop-rating-count">
                      ({shop.user_rating_count.toLocaleString()})
                    </span>
                  )}
                </div>
              )}
              {shop.address && <p className="shop-detail">{shop.address}</p>}
              <div className="shop-links">
                {shop.phone && (
                  <a className="shop-link" href={`tel:${shop.phone}`}>{shop.phone}</a>
                )}
                {shop.website && (
                  <a className="shop-link" href={shop.website} target="_blank" rel="noreferrer">Website</a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div className="summary-item">
      <div className="summary-item-label">{label}</div>
      <div className="summary-item-value">{value}</div>
    </div>
  );
}

function VerdictDetail({ label, value, highlight }) {
  return (
    <div className="verdict-detail-item">
      <div className="verdict-detail-label">{label}</div>
      <div className={`verdict-detail-value${highlight ? ` verdict-${highlight.toLowerCase()}` : ''}`}>
        {value}
      </div>
    </div>
  );
}

function SeverityDots({ severity }) {
  return (
    <div className="severity-dots" aria-label={`Severity ${severity} out of 5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`severity-dot ${i < severity ? severityDotClass(severity) : 'severity-dot--empty'}`}
        />
      ))}
      <span className="severity-dots-label">Severity {severity}/5</span>
    </div>
  );
}

function severityDotClass(severity) {
  if (severity >= 4) return 'severity-dot--high';
  if (severity >= 3) return 'severity-dot--medium';
  return 'severity-dot--low';
}

function SeverityIcon({ severity }) {
  if (severity === 'HIGH') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12" y2="17" />
      </svg>
    );
  }
  if (severity === 'MEDIUM') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12" y2="16" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function YoutubeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1C4.5 20.5 12 20.5 12 20.5s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8ZM9.75 15.5v-7l6.5 3.5-6.5 3.5Z" />
    </svg>
  );
}

function buildEquipmentName(formData) {
  const brand = formData.brand ? `${formData.brand} ` : '';
  const equipment = formData.equipmentType === 'skis' ? 'Skis' : 'Snowboard';
  const length = formData.length ? ` (${formData.length}in)` : '';
  return `${brand}${equipment}${length}`;
}

function capitalize(value) {
  if (!value) return '—';
  return value
    .split(/[-\s]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
