import { useRef, useState } from 'react';

const SKILL_LEVELS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' },
];

const SKIER_TYPES = [
  { value: '1', label: 'Type 1', sub: 'Cautious' },
  { value: '2', label: 'Type 2', sub: 'Moderate' },
  { value: '3', label: 'Type 3', sub: 'Aggressive' },
];

const EQUIPMENT_AGE_OPTIONS = [
  { value: '0-1 year', label: '0-1 years' },
  { value: '1-2 years', label: '1-2 years' },
  { value: '2-5 years', label: '2-5 years' },
  { value: '5+ years', label: '5+ years' },
];

const SPORTS = ['Skier', 'Snowboarder'];
const TERRAIN = ['groomers', 'park', 'powder', 'backcountry', 'hybrid'];

const EMPTY_FORM = {
  name: '',
  email: '',
  skillLevel: 'intermediate',
  skierType: '',
  birthday: '',
  weightLbs: '',
  heightFt: '',
  heightInPart: '',
  bootSoleLengthMm: '',
  preferredSport: 'Skier',
  equipment: [],
  preferredTerrain: 'hybrid',
  password: '',
  confirmPassword: '',
};

function userToForm(user) {
  return {
    name: user.name ?? '',
    email: user.email ?? '',
    skillLevel: user.skillLevel ?? 'intermediate',
    skierType: user.skierType != null ? String(user.skierType) : '',
    birthday: user.birthday ?? '',
    weightLbs: user.weightLbs != null ? String(user.weightLbs) : '',
    heightFt: user.heightIn != null ? String(Math.floor(user.heightIn / 12)) : '',
    heightInPart:
      user.heightIn != null ? String(parseFloat((user.heightIn % 12).toFixed(1))) : '',
    bootSoleLengthMm:
      user.bootSoleLengthMm != null ? String(user.bootSoleLengthMm) : '',
    preferredSport: user.preferredSport ?? 'Skier',
    equipment: user.equipment ?? [],
    preferredTerrain: user.preferredTerrain ?? 'hybrid',
    password: '',
    confirmPassword: '',
  };
}

function buildPayload(form) {
  const payload = {
    name: form.name,
    email: form.email,
    skillLevel: form.skillLevel,
    skierType: form.skierType !== '' ? parseInt(form.skierType) : null,
    birthday: form.birthday || null,
    weightLbs: form.weightLbs !== '' ? parseFloat(form.weightLbs) : null,
    heightIn:
      form.heightFt !== '' || form.heightInPart !== ''
        ? (parseInt(form.heightFt) || 0) * 12 + (parseFloat(form.heightInPart) || 0)
        : null,
    bootSoleLengthMm:
      form.bootSoleLengthMm !== '' ? parseInt(form.bootSoleLengthMm) : null,
    preferredSport: form.preferredSport,
    equipment: form.equipment,
    preferredTerrain: form.preferredTerrain,
  };
  if (form.password) {
    payload.password = form.password;
  }
  return payload;
}

function capitalize(value) {
  if (!value) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatHeight(heightIn) {
  if (heightIn == null) return null;
  const feet = Math.floor(heightIn / 12);
  const inches = parseFloat((heightIn % 12).toFixed(1));
  return `${feet}' ${inches}"`;
}

export default function UserPage({ initialView, currentUser, onLogin, onLogout, onBackToHome }) {
  const [view, setView] = useState(
    initialView || (currentUser ? 'profile' : 'idle')
  );
  const [form, setForm] = useState(
    initialView === 'create' ? EMPTY_FORM : currentUser ? userToForm(currentUser) : EMPTY_FORM
  );
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadingIdx, setUploadingIdx] = useState(null);
  const [uploadErrors, setUploadErrors] = useState({});
  const fileInputRefs = useRef({});

  const setField = (field) => (val) => setForm((f) => ({ ...f, [field]: val }));
  const setFieldE = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleImageUpload = async (i, e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingIdx(i);
    setUploadErrors((prev) => ({ ...prev, [i]: null }));
    try {
      const body = new FormData();
      body.append('file', file);
      const res = await fetch('/api/images/upload', { method: 'POST', body });
      if (res.ok) {
        const { url } = await res.json();
        // Use functional update so we always operate on the latest state,
        // not the stale closure-captured `form.equipment`.
        setForm((f) => ({
          ...f,
          equipment: f.equipment.map((eq, j) =>
            j === i ? { ...eq, images: [...(eq.images || []), url] } : eq
          ),
        }));
      } else {
        const err = await res.json().catch(() => ({}));
        const msg =
          res.status === 415
            ? 'Only JPEG, PNG, WebP, or GIF images are supported.'
            : res.status === 413
              ? 'Image must be under 10 MB.'
              : err.detail || 'Upload failed. Please try again.';
        setUploadErrors((prev) => ({ ...prev, [i]: msg }));
      }
    } catch {
      setUploadErrors((prev) => ({ ...prev, [i]: 'Connection error. Please try again.' }));
    } finally {
      setUploadingIdx(null);
      // reset so the same file can be picked again
      if (fileInputRefs.current[i]) fileInputRefs.current[i].value = '';
    }
  };

  const removeImage = (i, imgIdx) => {
    setForm((f) => ({
      ...f,
      equipment: f.equipment.map((eq, j) =>
        j === i ? { ...eq, images: (eq.images || []).filter((_, k) => k !== imgIdx) } : eq
      ),
    }));
  };

  const handleSignIn = async () => {
    const email = loginEmail.trim();
    if (!email || !loginPassword) {
      setLoginError('Please enter your email and password.');
      return;
    }
    setLoading(true);
    setLoginError('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: loginPassword }),
      });
      if (res.ok) {
        const user = await res.json();
        onLogin(user);
        setForm(userToForm(user));
        setView('profile');
      } else if (res.status === 401) {
        setLoginError('Invalid email or password.');
      } else {
        setLoginError('Something went wrong. Please try again.');
      }
    } catch {
      setLoginError('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (view === 'create') {
      if (!form.password) {
        setSubmitError('Password is required.');
        return;
      }
      if (form.password !== form.confirmPassword) {
        setSubmitError('Passwords do not match.');
        return;
      }
    }
    if (view === 'edit' && form.password) {
      if (form.password !== form.confirmPassword) {
        setSubmitError('Passwords do not match.');
        return;
      }
    }
    setLoading(true);
    setSubmitError('');
    try {
      const res = await fetch(`/api/users/${encodeURIComponent(form.email)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload(form)),
      });
      if (res.ok) {
        const user = await res.json();
        onLogin(user);
        setForm(userToForm(user));
        setView('profile');
      } else {
        const err = await res.json();
        setSubmitError(
          typeof err.detail === 'string'
            ? err.detail
            : 'Please check your inputs and try again.'
        );
      }
    } catch {
      setSubmitError('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    onLogout();
    setForm(EMPTY_FORM);
    setLoginEmail('');
    setLoginPassword('');
    setView('idle');
  };

  // ── Idle ────────────────────────────────────────────────────────────────────
  if (view === 'idle') {
    return (
      <main className="main-container">
        <div className="user-page">
          <h1>My account</h1>
          <p className="lead">
            Sign in to view your profile and DIN, or create a new account.
          </p>
          <div className="form-actions-stack">
            <button className="btn-primary btn-full" onClick={() => setView('login')}>
              Sign in
            </button>
            <button
              className="btn-secondary btn-full"
              onClick={() => {
                setForm(EMPTY_FORM);
                setView('create');
              }}
            >
              Create account
            </button>
            <button className="btn-ghost btn-full" onClick={onBackToHome}>
              Back to home
            </button>
          </div>
        </div>
      </main>
    );
  }

  // ── Login ───────────────────────────────────────────────────────────────────
  if (view === 'login') {
    return (
      <main className="main-container">
        <div className="user-page">
          <h1>Sign in</h1>
          <p className="lead">Enter your email and password.</p>
          <div className="stacked-fields">
            <div className="form-group">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSignIn()}
                placeholder="you@example.com"
                autoFocus
              />
            </div>
            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSignIn()}
                placeholder="••••••••"
              />
            </div>
          </div>
          {loginError && <p className="form-error">{loginError}</p>}
          <div className="form-actions-stack">
            <button
              className="btn-primary btn-full"
              onClick={handleSignIn}
              disabled={loading}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
            <button className="btn-secondary btn-full" onClick={() => setView('idle')}>
              Cancel
            </button>
          </div>
          <p className="lead" style={{ marginTop: '18px', marginBottom: 0 }}>
            No account?{' '}
            <button
              type="button"
              className="inline-link"
              onClick={() => {
                setForm(EMPTY_FORM);
                setView('create');
              }}
            >
              Create one
            </button>
          </p>
        </div>
      </main>
    );
  }

  // ── Profile view ────────────────────────────────────────────────────────────
  if (view === 'profile' && currentUser) {
    const u = currentUser;
    return (
      <main className="main-container">
        <section className="user-profile-page">
          <div className="user-profile-card">
            <div>
              <h2 className="user-profile-name">{u.name}</h2>
              <p className="user-profile-email">{u.email}</p>
            </div>
            {u.DIN != null && (
              <div className="user-din-badge">
                <span className="user-din-label">DIN</span>
                <span className="user-din-value">{u.DIN}</span>
              </div>
            )}
          </div>

          <div className="profile-detail-list">
            <div className="profile-section-header">Riding style</div>
            <ProfileDetail label="Sport" value={u.preferredSport} />
            <ProfileDetail label="Skill level" value={capitalize(u.skillLevel)} />
            <ProfileDetail
              label="Skier type"
              value={u.skierType != null ? `Type ${u.skierType}` : '—'}
            />
            <ProfileDetail
              label="Preferred terrain"
              value={capitalize(u.preferredTerrain)}
            />

            {(u.birthday || u.weightLbs != null || u.heightIn != null || u.bootSoleLengthMm != null) && (
              <>
                <div className="profile-section-header">Physical &amp; binding</div>
                {u.birthday && <ProfileDetail label="Birthday" value={u.birthday} />}
                {u.weightLbs != null && (
                  <ProfileDetail label="Weight" value={`${u.weightLbs} lbs`} />
                )}
                {u.heightIn != null && (
                  <ProfileDetail label="Height" value={formatHeight(u.heightIn)} />
                )}
                {u.bootSoleLengthMm != null && (
                  <ProfileDetail
                    label="Boot sole length"
                    value={`${u.bootSoleLengthMm} mm`}
                  />
                )}
              </>
            )}

            {u.equipment && u.equipment.length > 0 && (
              <>
                <div className="profile-section-header">Equipment</div>
                <div className="profile-detail" style={{ gridColumn: '1 / -1' }}>
                  <ul className="profile-equipment-list">
                    {u.equipment.map((item, i) => (
                      <li key={i} className="profile-equipment-item">
                        {item.images?.[0] && (
                          <img
                            src={item.images[0]}
                            alt=""
                            className="profile-equip-thumb"
                          />
                        )}
                        <span>
                          {[
                            item.name,
                            item.length && `${item.length}cm`,
                            item.width && `${item.width}mm`,
                            item.bindingType,
                            item.age,
                          ]
                            .filter(Boolean)
                            .join(' · ')}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>

          <div className="profile-actions">
            <button
              className="btn-secondary"
              onClick={() => {
                setForm(userToForm(u));
                setView('edit');
              }}
            >
              Edit profile
            </button>
            <button
              className="btn-secondary"
              onClick={() => {
                setForm(userToForm(u));
                setView('equipment');
              }}
            >
              Manage equipment
            </button>
            <button className="btn-secondary" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        </section>
      </main>
    );
  }

  // ── Equipment management ────────────────────────────────────────────────────
  if (view === 'equipment' && currentUser) {
    const handleEquipmentSave = async () => {
      setLoading(true);
      setSubmitError('');
      try {
        const payload = buildPayload(userToForm(currentUser));
        payload.equipment = form.equipment;
        const res = await fetch(`/api/users/${encodeURIComponent(currentUser.email)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const user = await res.json();
          onLogin(user);
          setForm(userToForm(user));
          setView('profile');
        } else {
          const err = await res.json().catch(() => ({}));
          setSubmitError(
            typeof err.detail === 'string'
              ? err.detail
              : 'Could not save equipment. Please try again.'
          );
        }
      } catch {
        setSubmitError('Connection error. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    return (
      <main className="main-container">
        <section className="form-page">
          <div className="page-header">
            <h1>Manage equipment</h1>
            <p>Add, edit, or remove your gear.</p>
          </div>

          <div className="assessment-form">
            <div className="form-section">
              <div className="equipment-editor">
                {form.equipment.map((item, i) => {
                  const updateItem = (field) => (e) => {
                    const updated = form.equipment.map((eq, j) =>
                      j === i ? { ...eq, [field]: e.target.value } : eq
                    );
                    setField('equipment')(updated);
                  };
                  const images = item.images || [];
                  return (
                    <div key={i} className="equipment-item-card">
                      <div className="equipment-item-fields">
                        <div className="form-group">
                          <label>Name / brand</label>
                          <input
                            type="text"
                            value={item.name}
                            onChange={updateItem('name')}
                            placeholder="Rossignol Experience 88"
                          />
                        </div>
                        <div className="form-group">
                          <label>Length (cm)</label>
                          <input
                            type="text"
                            value={item.length}
                            onChange={updateItem('length')}
                            placeholder="180"
                          />
                        </div>
                        <div className="form-group">
                          <label>Width (mm)</label>
                          <input
                            type="text"
                            value={item.width}
                            onChange={updateItem('width')}
                            placeholder="88"
                          />
                        </div>
                        <div className="form-group">
                          <label>Binding type</label>
                          <input
                            type="text"
                            value={item.bindingType ?? ''}
                            onChange={updateItem('bindingType')}
                            placeholder="Alpine, Tech/Pin, Strap…"
                          />
                        </div>
                      </div>

                      {images.length > 0 && (
                        <div className="equipment-images">
                          {images.map((url, imgIdx) => (
                            <div
                              key={imgIdx}
                              className={`equipment-image-thumb${imgIdx === 0 ? ' default' : ''}`}
                            >
                              <img src={url} alt={imgIdx === 0 ? 'Default photo' : `Photo ${imgIdx + 1}`} />
                              {imgIdx === 0 && (
                                <span className="default-badge">Default</span>
                              )}
                              <button
                                type="button"
                                className="remove-image-btn"
                                onClick={() => removeImage(i, imgIdx)}
                                aria-label="Remove photo"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="equipment-item-footer">
                        <label className={`add-photo-label${uploadingIdx === i ? ' uploading' : ''}`}>
                          <input
                            type="file"
                            accept="image/*"
                            className="visually-hidden"
                            ref={(el) => { fileInputRefs.current[i] = el; }}
                            onChange={(e) => handleImageUpload(i, e)}
                            disabled={uploadingIdx === i}
                          />
                          {uploadingIdx === i
                            ? <><span className="spinner" />Uploading…</>
                            : '+ Add photo'}
                        </label>
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() =>
                            setField('equipment')(
                              form.equipment.filter((_, j) => j !== i)
                            )
                          }
                        >
                          Remove
                        </button>
                      </div>
                      {uploadErrors[i] && (
                        <p className="upload-error">{uploadErrors[i]}</p>
                      )}
                    </div>
                  );
                })}
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() =>
                    setField('equipment')([
                      ...form.equipment,
                      { name: '', length: '', width: '', bindingType: '', images: [] },
                    ])
                  }
                >
                  + Add equipment
                </button>
              </div>
            </div>

            {submitError && <p className="form-error">{submitError}</p>}

            <div className="form-buttons">
              <button
                className="btn-primary"
                onClick={handleEquipmentSave}
                disabled={loading}
              >
                {loading ? 'Saving…' : 'Save equipment'}
              </button>
              <button
                className="btn-secondary"
                onClick={() => {
                  setForm(userToForm(currentUser));
                  setView('profile');
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </section>
      </main>
    );
  }

  // ── Create / Edit form ──────────────────────────────────────────────────────
  const isEdit = view === 'edit';

  const TileButton = ({ field, value, label, sub }) => (
    <button
      type="button"
      className={`tile-option${sub ? ' compact' : ''}${form[field] === value ? ' selected' : ''}`}
      onClick={() => setField(field)(value)}
    >
      {label}
      {sub && <span className="tile-sub">{sub}</span>}
    </button>
  );

  return (
    <main className="main-container">
      <section className="form-page">
        <div className="page-header">
          <h1>{isEdit ? 'Edit profile' : 'Create account'}</h1>
          <p>Personal details are used to calculate your DIN setting.</p>
        </div>

        <div className="assessment-form">
          <div className="form-section">
            <div className="section-title">Account</div>
            <div className="section-subtitle">Required</div>
            <div className="stacked-fields">
              <div className="form-group">
                <label htmlFor="u-name">Full name</label>
                <input
                  id="u-name"
                  type="text"
                  value={form.name}
                  onChange={setFieldE('name')}
                  placeholder="Alex Smith"
                />
              </div>
              <div className="form-group">
                <label htmlFor="u-email">Email</label>
                <input
                  id="u-email"
                  type="email"
                  value={form.email}
                  onChange={setFieldE('email')}
                  placeholder="you@example.com"
                  disabled={isEdit}
                />
              </div>
              {!isEdit && (
                <>
                  <div className="form-group">
                    <label htmlFor="u-password">Password</label>
                    <input
                      id="u-password"
                      type="password"
                      value={form.password}
                      onChange={setFieldE('password')}
                      placeholder="Min. 8 characters"
                      autoComplete="new-password"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="u-confirm-password">Confirm password</label>
                    <input
                      id="u-confirm-password"
                      type="password"
                      value={form.confirmPassword}
                      onChange={setFieldE('confirmPassword')}
                      placeholder="Re-enter password"
                      autoComplete="new-password"
                    />
                  </div>
                </>
              )}
            </div>
            <div className="choice-group" style={{ marginTop: '18px' }}>
              <div className="choice-group-title">Skill level</div>
              <div className="segmented-grid grid-4">
                {SKILL_LEVELS.map(({ value, label }) => (
                  <TileButton key={value} field="skillLevel" value={value} label={label} />
                ))}
              </div>
            </div>
          </div>

          <div className="form-section">
            <div className="section-title">Binding &amp; physical info</div>
            <div className="section-subtitle">Required · used to calculate your DIN</div>
            <div className="choice-group">
              <div className="choice-group-title">Skier type</div>
              <div className="segmented-grid grid-3">
                {SKIER_TYPES.map(({ value, label, sub }) => (
                  <TileButton
                    key={value}
                    field="skierType"
                    value={value}
                    label={label}
                    sub={sub}
                  />
                ))}
              </div>
            </div>
            <div className="stacked-fields" style={{ marginTop: '18px' }}>
              <div className="form-group">
                <label htmlFor="u-birthday">Birthday</label>
                <input
                  id="u-birthday"
                  type="date"
                  value={form.birthday}
                  onChange={setFieldE('birthday')}
                />
              </div>
              <div className="form-group">
                <label htmlFor="u-weight">Weight (lbs)</label>
                <input
                  id="u-weight"
                  type="number"
                  value={form.weightLbs}
                  onChange={setFieldE('weightLbs')}
                  placeholder="155"
                  min="44"
                  max="661"
                  step="0.5"
                />
              </div>
              <div className="form-group">
                <label>Height</label>
                <div className="input-grid">
                  <input
                    type="number"
                    value={form.heightFt}
                    onChange={setFieldE('heightFt')}
                    placeholder="ft"
                    min="3"
                    max="8"
                    step="1"
                  />
                  <input
                    type="number"
                    value={form.heightInPart}
                    onChange={setFieldE('heightInPart')}
                    placeholder="in"
                    min="0"
                    max="11"
                    step="0.5"
                  />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="u-bsl">Boot sole length (mm)</label>
                <input
                  id="u-bsl"
                  type="number"
                  value={form.bootSoleLengthMm}
                  onChange={setFieldE('bootSoleLengthMm')}
                  placeholder="295"
                  min="200"
                  max="400"
                  step="1"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <div className="section-title">Preferences</div>
            <div className="section-subtitle">Optional · personalizes recommendations</div>
            <div className="choice-group">
              <div className="choice-group-title">Sport</div>
              <div className="segmented-grid grid-2">
                {SPORTS.map((s) => (
                  <TileButton key={s} field="preferredSport" value={s} label={s} />
                ))}
              </div>
            </div>

            <div className="choice-group">
              <div className="choice-group-title">Preferred terrain</div>
              <div className="segmented-grid grid-3">
                {TERRAIN.map((t) => (
                  <TileButton
                    key={t}
                    field="preferredTerrain"
                    value={t}
                    label={capitalize(t)}
                  />
                ))}
              </div>
            </div>
          </div>

          {isEdit && (
            <div className="form-section">
              <div className="section-title">Change password</div>
              <div className="section-subtitle">Optional · leave blank to keep current</div>
              <div className="stacked-fields">
                <div className="form-group">
                  <label htmlFor="u-new-password">New password</label>
                  <input
                    id="u-new-password"
                    type="password"
                    value={form.password}
                    onChange={setFieldE('password')}
                    placeholder="Min. 8 characters"
                    autoComplete="new-password"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="u-confirm-new-password">Confirm new password</label>
                  <input
                    id="u-confirm-new-password"
                    type="password"
                    value={form.confirmPassword}
                    onChange={setFieldE('confirmPassword')}
                    placeholder="Re-enter new password"
                    autoComplete="new-password"
                  />
                </div>
              </div>
            </div>
          )}

          {submitError && <p className="form-error">{submitError}</p>}

          <div className="form-buttons">
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? 'Saving…' : isEdit ? 'Save changes' : 'Create account'}
            </button>
            <button
              className="btn-secondary"
              onClick={() => setView(currentUser ? 'profile' : 'idle')}
            >
              Cancel
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}

function ProfileDetail({ label, value }) {
  return (
    <div className="profile-detail">
      <div className="profile-detail-label">{label}</div>
      <div className="profile-detail-value">{value}</div>
    </div>
  );
}
