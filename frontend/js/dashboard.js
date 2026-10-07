/* Dashboard: load profile + health, require login. */
document.addEventListener("DOMContentLoaded", async () => {
  if (!getToken()) {
    window.location.href = "/login.html";
    return;
  }
  checkHealth();
  const { res, body } = await apiFetch("/api/users/me");
  if (!res.ok || !body || !body.success) {
    clearToken();
    window.location.href = "/login.html";
    return;
  }
  const u = body.data.user;
  document.getElementById("welcome").textContent = `Welcome, ${u.name}`;
  document.getElementById("f-id").textContent = u.id;
  document.getElementById("f-email").textContent = u.email;
  document.getElementById("f-created").textContent = u.created_at || "—";
  document.getElementById("f-auth").textContent = "Authenticated (JWT)";
});
