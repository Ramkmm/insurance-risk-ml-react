import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "https://insurance-risk-ml.onrender.com";

const DEFAULT_FORM = {
  house_age: 10,
  location_risk: 0.5,
  roof_type: 1,
  past_claims: 1,
  property_value: 500000,
};

const FEATURES = [
  { icon: "◈", title: "ML Risk Score", text: "XGBoost-powered property risk assessment." },
  { icon: "₹", title: "Premium Estimate", text: "Illustrative annual premium based on predicted risk." },
  { icon: "✦", title: "Explainable AI", text: "Feature importance shows what drives the prediction." },
];

function formatINR(value, decimals = 0) {
  return `₹${Number(value || 0).toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

function getRiskMeta(category = "") {
  const value = category.toLowerCase();
  if (value.includes("high")) return { className: "high", icon: "!", label: "High Risk" };
  if (value.includes("medium")) return { className: "medium", icon: "~", label: "Medium Risk" };
  return { className: "low", icon: "✓", label: "Low Risk" };
}

function App() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(() => localStorage.getItem("access_token") || "");
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [predictLoading, setPredictLoading] = useState(false);

  useEffect(() => {
    if (token) loadCurrentUser(token);
  }, [token]);

  async function loadCurrentUser(accessToken) {
    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (!response.ok) {
        logout();
        return;
      }

      setUser(await response.json());
    } catch {
      setError("Unable to connect to the API. Please try again.");
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setMessage("");
  }

  async function handleAuth(event) {
    event.preventDefault();
    setAuthLoading(true);
    setError("");
    setMessage("");

    try {
      const endpoint = mode === "register" ? "/auth/register" : "/auth/login";
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed.");
      }

      if (mode === "register") {
        setMessage("Registration successful. You can now log in.");
        setMode("login");
        setPassword("");
      } else {
        localStorage.setItem("access_token", data.access_token);
        setToken(data.access_token);
        setMessage("Login successful.");
        setPassword("");
      }
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Could not reach the API. Please check your connection and try again."
          : err.message
      );
    } finally {
      setAuthLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken("");
    setUser(null);
    setResult(null);
    setMessage("");
    setError("");
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function predictRisk(event) {
    event.preventDefault();
    setPredictLoading(true);
    setError("");
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          house_age: Number(form.house_age),
          location_risk: Number(form.location_risk),
          roof_type: Number(form.roof_type),
          past_claims: Number(form.past_claims),
          property_value: Number(form.property_value),
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          throw new Error("Your session has expired. Please log in again.");
        }
        throw new Error(data.detail || "Prediction failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Could not reach the prediction API. Please try again."
          : err.message
      );
    } finally {
      setPredictLoading(false);
    }
  }

  const riskMeta = useMemo(
    () => getRiskMeta(result?.risk_category),
    [result?.risk_category]
  );

  const riskPercentage = result
    ? Math.min(100, Math.max(0, Number(result.risk_percentage ?? result.risk_score * 100)))
    : 0;

  if (!token || !user) {
    return (
      <div className="auth-page">
        <div className="auth-shell">
          <section className="auth-hero">
            <div className="brand-mark">⌂</div>
            <div className="eyebrow"><span /> AI PROPERTY INTELLIGENCE</div>
            <h1>House Insurance<br /><em>Risk</em></h1>
            <p className="auth-lead">
              Turn property information into an explainable AI risk assessment and an illustrative premium estimate.
            </p>

            <div className="hero-points">
              {FEATURES.map((feature) => (
                <div className="hero-point" key={feature.title}>
                  <div className="hero-point-icon">{feature.icon}</div>
                  <div>
                    <strong>{feature.title}</strong>
                    <span>{feature.text}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="tech-strip">
              <span>React</span><span>FastAPI</span><span>XGBoost</span><span>MongoDB</span>
            </div>
          </section>

          <section className="auth-card">
            <div className="mobile-brand">
              <div className="brand-mark small">⌂</div>
              <span>House Insurance Risk</span>
            </div>

            <div className="status-pill"><span className="status-dot" /> Demo environment · Secure JWT access</div>
            <h2>{mode === "login" ? "Welcome back" : "Create your demo account"}</h2>
            <p className="auth-subtitle">
              {mode === "login"
                ? "Sign in to run property risk assessments."
                : "Register once to access the protected prediction dashboard."}
            </p>

            <div className="tabs">
              <button type="button" className={mode === "login" ? "active" : ""} onClick={() => switchMode("login")}>Login</button>
              <button type="button" className={mode === "register" ? "active" : ""} onClick={() => switchMode("register")}>Register</button>
            </div>

            <form onSubmit={handleAuth}>
              <label htmlFor="email">Email address</label>
              <input id="email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />

              <label htmlFor="password">Password</label>
              <input id="password" type="password" placeholder="Minimum 6 characters" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required autoComplete={mode === "login" ? "current-password" : "new-password"} />

              <button className="primary-button auth-submit" disabled={authLoading}>
                {authLoading ? "Please wait…" : mode === "login" ? "Sign in to dashboard" : "Create demo account"}
                {!authLoading && <span>→</span>}
              </button>
            </form>

            {message && <div className="success">✓ {message}</div>}
            {error && <div className="error">{error}</div>}

            <p className="demo-note">Demo estimate only — not an actual insurance quote.</p>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand compact">
            <div className="brand-mark small">⌂</div>
            <div><strong>House Insurance Risk</strong><span>AI Property Intelligence</span></div>
          </div>
          <div className="user-area">
            <div className="user-avatar">{user.email?.charAt(0).toUpperCase()}</div>
            <span>{user.email}</span>
            <button onClick={logout} className="logout-button">Log out</button>
          </div>
        </div>
      </header>

      <main className="dashboard">
        <section className="dashboard-hero">
          <div>
            <div className="eyebrow"><span /> LIVE AI ASSESSMENT</div>
            <h1>Property Risk <em>Assessment</em></h1>
            <p>Enter property details to calculate an AI-based risk score, risk category and illustrative annual premium.</p>
          </div>
          <div className="api-badge"><span className="status-dot" /> API connected</div>
        </section>

        <div className="dashboard-grid">
          <section className="panel input-panel">
            <div className="panel-heading">
              <div><span className="section-kicker">INPUT</span><h2>Property details</h2></div>
              <div className="step-badge">01</div>
            </div>

            <form onSubmit={predictRisk}>
              <div className="field">
                <label htmlFor="house-age">House age</label>
                <div className="input-row"><input id="house-age" type="number" min="0" max="100" value={form.house_age} onChange={(e) => updateForm("house_age", e.target.value)} /><span>years</span></div>
              </div>

              <div className="field">
                <label htmlFor="location-risk">Location risk <span className="label-help">0 = lower · 1 = higher</span></label>
                <div className="range-line">
                  <input id="location-risk" type="range" min="0" max="1" step="0.01" value={form.location_risk} onChange={(e) => updateForm("location_risk", e.target.value)} />
                  <strong>{Number(form.location_risk).toFixed(2)}</strong>
                </div>
              </div>

              <div className="field">
                <label htmlFor="roof-type">Roof type</label>
                <select id="roof-type" value={form.roof_type} onChange={(e) => updateForm("roof_type", e.target.value)}>
                  <option value="1">Type 1</option><option value="2">Type 2</option><option value="3">Type 3</option><option value="4">Type 4</option><option value="5">Type 5</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="past-claims">Past claims</label>
                <input id="past-claims" type="number" min="0" max="10" value={form.past_claims} onChange={(e) => updateForm("past_claims", e.target.value)} />
              </div>

              <div className="field">
                <label htmlFor="property-value">Property value</label>
                <div className="currency-input"><span>₹</span><input id="property-value" type="number" min="10000" step="10000" value={form.property_value} onChange={(e) => updateForm("property_value", e.target.value)} /></div>
              </div>

              <button className="primary-button predict-button" disabled={predictLoading}>
                {predictLoading ? "Analyzing property…" : "Calculate risk"}<span>{predictLoading ? "" : "→"}</span>
              </button>
            </form>
            {error && <div className="error">{error}</div>}
          </section>

          <section className="panel result-panel">
            <div className="panel-heading">
              <div><span className="section-kicker">OUTPUT</span><h2>Risk assessment</h2></div>
              {result && <div className={`risk-chip ${riskMeta.className}`}><span>{riskMeta.icon}</span>{riskMeta.label}</div>}
            </div>

            {!result ? (
              <div className="empty-result">
                <div className="empty-visual"><div>✦</div><span>AI</span></div>
                <h3>Ready for assessment</h3>
                <p>Enter property details on the left and run the model to see your result.</p>
              </div>
            ) : (
              <>
                <div className={`risk-score ${riskMeta.className}`}>
                  <div className="risk-score-top"><span>Predicted risk score</span><small>{riskMeta.label}</small></div>
                  <strong>{riskPercentage.toFixed(2)}<sup>%</sup></strong>
                  <div className="risk-bar"><div style={{ width: `${riskPercentage}%` }} /></div>
                </div>

                <div className="result-grid">
                  <div className="result-box accent-blue"><span>Annual premium</span><strong>{formatINR(result.recommended_premium, 2)}</strong><small>Illustrative estimate</small></div>
                  <div className="result-box"><span>Premium rate</span><strong>{(Number(result.premium_rate || 0) * 100).toFixed(3)}%</strong><small>Applied to property value</small></div>
                  <div className="result-box"><span>Property value</span><strong>{formatINR(form.property_value)}</strong><small>Assessment input</small></div>
                  <div className="result-box"><span>Model output</span><strong>{result.risk_category}</strong><small>Predicted category</small></div>
                </div>

                {result.feature_importance && (
                  <div className="importance">
                    <div className="importance-heading"><div><span className="section-kicker">EXPLAINABILITY</span><h3>Feature importance</h3></div><span>Model drivers</span></div>
                    {Object.entries(result.feature_importance).map(([feature, value]) => (
                      <div className="importance-row" key={feature}>
                        <div className="importance-label"><span>{feature.replaceAll("_", " ")}</span><strong>{(Number(value) * 100).toFixed(1)}%</strong></div>
                        <div className="importance-bar"><div style={{ width: `${Math.min(100, Number(value) * 100)}%` }} /></div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </section>
        </div>

        <div className="dashboard-footnote"><span>●</span> Demo estimate only — not an actuarial insurance quote.</div>
      </main>
    </div>
  );
}

export default App;
