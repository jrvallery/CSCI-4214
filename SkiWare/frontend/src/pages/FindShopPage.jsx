import { useEffect, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const LAST_KNOWN_COORDS_KEY = 'skiware:last-known-shop-search-coords';
const LAST_KNOWN_COORDS_MAX_AGE_MS = 1800000;
const GEOLOCATION_CACHED_TIMEOUT_MS = 1500;
const GEOLOCATION_FRESH_TIMEOUT_MS = 15000;
const SHOPS_FETCH_TIMEOUT_MS = 12000;

function getCurrentPosition(options) {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, options);
  });
}

function loadStoredCoords() {
  try {
    const raw = window.localStorage.getItem(LAST_KNOWN_COORDS_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (
      typeof parsed?.latitude !== 'number' ||
      typeof parsed?.longitude !== 'number' ||
      typeof parsed?.timestamp !== 'number'
    ) {
      window.localStorage.removeItem(LAST_KNOWN_COORDS_KEY);
      return null;
    }

    if (Date.now() - parsed.timestamp > LAST_KNOWN_COORDS_MAX_AGE_MS) {
      window.localStorage.removeItem(LAST_KNOWN_COORDS_KEY);
      return null;
    }

    return parsed;
  } catch {
    window.localStorage.removeItem(LAST_KNOWN_COORDS_KEY);
    return null;
  }
}

function saveStoredCoords(latitude, longitude) {
  try {
    window.localStorage.setItem(
      LAST_KNOWN_COORDS_KEY,
      JSON.stringify({
        latitude,
        longitude,
        timestamp: Date.now(),
      })
    );
  } catch {
    // Ignore storage errors and continue with the live search flow.
  }
}

const shopIcon = L.divIcon({
  className: '',
  html: '<div class="map-dot map-dot-shop"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
  popupAnchor: [0, -10],
});

const userIcon = L.divIcon({
  className: '',
  html: '<div class="map-dot map-dot-user"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

function MapController({ selectedShop }) {
  const map = useMap();
  useEffect(() => {
    if (selectedShop) {
      map.flyTo([selectedShop.lat, selectedShop.lon], 15, { duration: 0.7 });
    }
  }, [selectedShop]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

export default function FindShopPage({ onBackToHome }) {
  const [status, setStatus] = useState('locating');
  const [shops, setShops] = useState([]);
  const [userCoords, setUserCoords] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [selectedShop, setSelectedShop] = useState(null);

  const handleFindShops = async () => {
    if (!navigator.geolocation) {
      setErrorMsg('Geolocation is not supported by your browser.');
      setStatus('error');
      return;
    }

    const searchStartedAt = performance.now();
    setStatus('locating');
    setErrorMsg('');
    setSelectedShop(null);

    let latitude;
    let longitude;
    let locationSource = 'fresh-geolocation';

    try {
      const storedCoords = loadStoredCoords();
      if (storedCoords) {
        latitude = storedCoords.latitude;
        longitude = storedCoords.longitude;
        locationSource = 'stored-last-known';
        console.info('[FindShopPage] Using stored last-known location', {
          geolocationDurationMs: Math.round(performance.now() - searchStartedAt),
          latitude,
          longitude,
          ageMs: Date.now() - storedCoords.timestamp,
        });
      } else {
        try {
          const cachedPosition = await getCurrentPosition({
            enableHighAccuracy: false,
            timeout: GEOLOCATION_CACHED_TIMEOUT_MS,
            maximumAge: Infinity,
          });
          latitude = cachedPosition.coords.latitude;
          longitude = cachedPosition.coords.longitude;
          locationSource = 'browser-geolocation-cache';
          console.info('[FindShopPage] Using browser cached location', {
            geolocationDurationMs: Math.round(performance.now() - searchStartedAt),
            latitude,
            longitude,
          });
          saveStoredCoords(latitude, longitude);
        } catch (cachedErr) {
          console.warn('[FindShopPage] Cached geolocation unavailable', {
            code: cachedErr.code,
            message: cachedErr.message,
            geolocationDurationMs: Math.round(performance.now() - searchStartedAt),
          });

          const freshPosition = await getCurrentPosition({
            enableHighAccuracy: false,
            timeout: GEOLOCATION_FRESH_TIMEOUT_MS,
            maximumAge: 0,
          });
          latitude = freshPosition.coords.latitude;
          longitude = freshPosition.coords.longitude;
          console.info('[FindShopPage] Fresh geolocation resolved', {
            geolocationDurationMs: Math.round(performance.now() - searchStartedAt),
            latitude,
            longitude,
          });
          saveStoredCoords(latitude, longitude);
        }
      }
    } catch (err) {
      console.warn('[FindShopPage] Geolocation failed', {
        code: err.code,
        message: err.message,
        geolocationDurationMs: Math.round(performance.now() - searchStartedAt),
      });
      if (err.code === 1) {
        setStatus('denied');
        return;
      }
      setErrorMsg(
        err.code === 3
          ? 'Location lookup timed out. Please try again.'
          : 'Could not determine your location. Please try again.'
      );
      setStatus('error');
      return;
    }

    setUserCoords([latitude, longitude]);
    setStatus('loading');

    const controller = new AbortController();
    const fetchStartedAt = performance.now();
    const timeoutId = window.setTimeout(() => controller.abort(), SHOPS_FETCH_TIMEOUT_MS);

    try {
      const res = await fetch(`/api/shops/nearest?lat=${latitude}&lon=${longitude}`, {
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      console.info('[FindShopPage] Shop search completed', {
        locationSource,
        fetchDurationMs: Math.round(performance.now() - fetchStartedAt),
        totalDurationMs: Math.round(performance.now() - searchStartedAt),
        resultCount: data.length,
      });
      setShops(data);
      setStatus('success');
    } catch (err) {
      console.error('[FindShopPage]', err);
      setErrorMsg(
        err.name === 'AbortError'
          ? 'Nearby shop search timed out. Please try again.'
          : 'Could not load nearby shops. Please try again.'
      );
      setStatus('error');
    } finally {
      window.clearTimeout(timeoutId);
    }
  };

  useEffect(() => {
    handleFindShops();

    if (!navigator.permissions) return;

    let cleanup = null;
    let cancelled = false;
    navigator.permissions.query({ name: 'geolocation' }).then((permStatus) => {
      if (cancelled) return;
      const onChange = () => {
        if (permStatus.state === 'granted') {
          handleFindShops();
        }
      };
      permStatus.addEventListener('change', onChange);
      cleanup = () => permStatus.removeEventListener('change', onChange);
    });

    return () => {
      cancelled = true;
      if (cleanup) cleanup();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const mapBounds =
    userCoords && shops.length > 0
      ? [userCoords, ...shops.map((s) => [s.lat, s.lon])]
      : userCoords
      ? [userCoords]
      : null;

  const isBusy = status === 'locating' || status === 'loading';

  return (
    <main className="main-container">
      <section className="shop-page">
        {status === 'denied' ? (
          <div className="shop-intro">
            <div className="shop-location-prompt">
              <div className="shop-location-icon">📍</div>
              <h1>Location access required</h1>
              <p>
                To find ski and snowboard shops near you, please enable location
                access in your browser settings, then come back to this page.
              </p>
              <div className="shop-actions">
                <button className="btn-primary" onClick={handleFindShops}>
                  Try again
                </button>
                <button className="btn-secondary" onClick={onBackToHome}>
                  Back to home
                </button>
              </div>
            </div>
          </div>
        ) : status !== 'success' ? (
          <div className="shop-intro">
            <h1>Find a nearby shop</h1>
            <p>
              Locate ski and snowboard shops near you for tuning, waxing, and repair
              services within 15 miles.
            </p>
            {isBusy && (
              <p className="shop-status-msg">
                {status === 'locating' ? 'Detecting your location…' : 'Searching for nearby shops…'}
              </p>
            )}
            {status === 'error' && (
              <>
                <p className="shop-error-msg">{errorMsg}</p>
                <div className="shop-actions">
                  <button className="btn-primary" onClick={handleFindShops}>
                    Try again
                  </button>
                  <button className="btn-secondary" onClick={onBackToHome}>
                    Back to home
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="shop-results">
            <div className="shop-results-header">
              <div className="shop-results-count">
                {shops.length} shop{shops.length !== 1 ? 's' : ''} found
              </div>
              <div className="shop-actions">
                <button className="btn-secondary" onClick={onBackToHome}>
                  Back to home
                </button>
                <button className="btn-primary" onClick={handleFindShops}>
                  Search again
                </button>
              </div>
            </div>

            {shops.length === 0 ? (
              <p className="shop-status-msg">No shops found within 15 miles.</p>
            ) : (
              <div className="shop-results-layout">
                <div className="shop-list-panel">
                  <ul className="shop-list">
                    {shops.map((shop, i) => (
                      <li
                        key={i}
                        className={`shop-card${selectedShop === shop ? ' shop-card--selected' : ''}`}
                        onClick={() => setSelectedShop(shop)}
                      >
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
                            <a
                              className="shop-link"
                              href={`tel:${shop.phone}`}
                              onClick={(e) => e.stopPropagation()}
                            >
                              {shop.phone}
                            </a>
                          )}
                          {shop.website && (
                            <a
                              className="shop-link"
                              href={shop.website}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Website
                            </a>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>

                {mapBounds && (
                  <div className="shop-map-panel">
                    <MapContainer
                      bounds={mapBounds}
                      boundsOptions={{ padding: [40, 40] }}
                      className="shop-map"
                      scrollWheelZoom
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />

                      <Marker position={userCoords} icon={userIcon}>
                        <Popup>Your location</Popup>
                      </Marker>

                      {shops.map((shop, i) => (
                        <Marker key={i} position={[shop.lat, shop.lon]} icon={shopIcon}>
                          <Popup>
                            <strong>{shop.name}</strong>
                            {shop.address && <><br />{shop.address}</>}
                            {shop.phone && (
                              <><br /><a href={`tel:${shop.phone}`}>{shop.phone}</a></>
                            )}
                            {shop.website && (
                              <><br /><a href={shop.website} target="_blank" rel="noreferrer">Website</a></>
                            )}
                            <><br /><strong>{shop.distance_miles} mi away</strong></>
                          </Popup>
                        </Marker>
                      ))}

                      <MapController selectedShop={selectedShop} />
                    </MapContainer>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
