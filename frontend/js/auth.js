/* Shared auth helpers for the demo frontend. Token is kept in
   localStorage for demonstration simplicity (see README security note). */

const TOKEN_KEY = "auth_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function showMsg(text, ok = false) {
  const el = document.getElementById("msg");
  if (!el) return;
  el.textContent = text;
  el.className = "msg " + (ok ? "ok" : "error");
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(path, { ...options, headers });
  let body = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  return { res, body };
}

function apiError(body, fallback) {
  if (body && body.error && body.error.message) return body.error.message;
  if (body && body.detail) return String(body.detail);
  return fallback;
}

function setPill(id, online, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = "pill " + (online ? "online" : "offline");
}

async function checkHealth() {
  try {
    const r = await fetch("/api/health");
    setPill("api-status", r.ok, r.ok ? "Online" : "Offline");
  } catch {
    setPill("api-status", false, "Offline");
  }
  try {
    const r = await fetch("/api/health/database");
    const b = await r.json();
    const ok = r.ok && b && b.database === "online";
    setPill("db-status", ok, ok ? "Online" : "Offline");
  } catch {
    setPill("db-status", false, "Offline");
  }
}

async function signup(name, email, password, confirm) {
  if (!name || !email || !password) return showMsg("All fields are required.");
  if (password !== confirm) return showMsg("Passwords do not match.");
  if (password.length < 6) return showMsg("Password must be at least 6 characters.");
  const { res, body } = await apiFetch("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok || !body || !body.success) return showMsg(apiError(body, "Signup failed."));
  saveToken(body.data.access_token);
  window.location.href = "/dashboard.html";
}

async function login(email, password) {
  if (!email || !password) return showMsg("Email and password are required.");
  const { res, body } = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok || !body || !body.success) return showMsg(apiError(body, "Login failed."));
  saveToken(body.data.access_token);
  window.location.href = "/dashboard.html";
}

async function logout() {
  try {
    await apiFetch("/api/auth/logout", { method: "POST" });
  } finally {
    clearToken();
    window.location.href = "/login.html";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const link = document.getElementById("logout-link");
  if (link) link.addEventListener("click", (e) => { e.preventDefault(); logout(); });
  const btn = document.getElementById("logout-btn");
  if (btn) btn.addEventListener("click", logout);
});
