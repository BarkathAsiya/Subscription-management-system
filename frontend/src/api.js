const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("subsentry_token");
}

export function saveSession(data) {
  localStorage.setItem("subsentry_token", data.access_token);
  localStorage.setItem("subsentry_user", JSON.stringify(data.user));
}

export function clearSession() {
  localStorage.removeItem("subsentry_token");
  localStorage.removeItem("subsentry_user");
}

export function getSavedUser() {
  try { return JSON.parse(localStorage.getItem("subsentry_user") || "null"); }
  catch { return null; }
}

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail) ? detail.map(x => x.msg || x).join(" ") : (detail || "Something went wrong.");
    throw new Error(message);
  }
  return data;
}
