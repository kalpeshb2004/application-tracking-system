// Backend address (Django). Change here only, when you deploy.
const API_BASE = "http://127.0.0.1:8000/api";

// ---------- Token storage ----------
// Keys are "access" / "refresh", so old FastAPI tokens are ignored.
const Auth = {
  getToken: () => localStorage.getItem("access"),
  getRefresh: () => localStorage.getItem("refresh"),
  setTokens(access, refresh) {
    localStorage.setItem("access", access);
    if (refresh) localStorage.setItem("refresh", refresh);
  },
  logout() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("token");   // old FastAPI token
    window.location.href = "login.html";
  },
  // Call at top of every protected page
  requireLogin() {
    if (!this.getToken()) window.location.href = "login.html";
  },
};

// Django needs a trailing "/" before the query string.
// "/applications?limit=5" → "/applications/?limit=5"
function withSlash(path) {
  const [p, query] = path.split("?");
  const fixed = p.endsWith("/") ? p : p + "/";
  return query === undefined ? fixed : `${fixed}?${query}`;
}

// DRF errors come in 3 shapes:
//   {"detail": "text"}               → text
//   {"email": ["msg1", "msg2"]}      → "email: msg1 msg2"
//   {"days": "text"}                 → "days: text"
function formatError(data) {
  if (!data) return null;
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;

  const parts = [];
  for (const [key, val] of Object.entries(data)) {
    const text = Array.isArray(val) ? val.join(" ") : String(val);
    parts.push(key === "non_field_errors" ? text : `${key}: ${text}`);
  }
  return parts.length ? parts.join(" | ") : null;
}

// ---------- Silent token refresh ----------
// Access token lives 60 min. The refresh token (7 days) gets a new one.
let refreshing = null;   // share one refresh between parallel requests

async function refreshAccess() {
  const refresh = Auth.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(API_BASE + "/auth/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    Auth.setTokens(data.access, data.refresh);
    return true;
  } catch {
    return false;
  }
}

// One function for every API call.
async function apiFetch(path, options = {}, retried = false) {
  const { json, ...rest } = options;
  const headers = { ...(rest.headers || {}) };

  // Login / register / refresh must not carry an old token
  const isAuthCall = /^\/auth\/(login|register|refresh)/.test(path);
  const token = Auth.getToken();
  if (token && !isAuthCall) headers["Authorization"] = `Bearer ${token}`;

  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    rest.body = JSON.stringify(json);
  }

  let res;
  try {
    res = await fetch(API_BASE + withSlash(path), { ...rest, headers });
  } catch {
    throw new Error("Cannot reach server. Is the backend running?");
  }

  // Access token expired → refresh once, retry the same request
  if (res.status === 401 && token && !isAuthCall) {
    if (!retried) {
      refreshing = refreshing || refreshAccess().finally(() => { refreshing = null; });
      if (await refreshing) return apiFetch(path, options, true);
    }
    Auth.logout();
    throw new Error("Session expired. Please login again.");
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(formatError(data) || `Error ${res.status}`);
  return data;
}