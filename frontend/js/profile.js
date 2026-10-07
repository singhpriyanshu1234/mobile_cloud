/* Profile: view name/email, update name, delete account. */
document.addEventListener("DOMContentLoaded", async () => {
  if (!getToken()) {
    window.location.href = "/login.html";
    return;
  }
  const { res, body } = await apiFetch("/api/users/me");
  if (!res.ok || !body || !body.success) {
    clearToken();
    window.location.href = "/login.html";
    return;
  }
  const u = body.data.user;
  document.getElementById("f-name").textContent = u.name;
  document.getElementById("f-email").textContent = u.email;
  document.getElementById("name").value = u.name;

  document.getElementById("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const r = await apiFetch("/api/users/me", {
      method: "PUT",
      body: JSON.stringify({ name }),
    });
    if (!r.res.ok || !r.body || !r.body.success) {
      return showMsg(apiError(r.body, "Update failed."));
    }
    document.getElementById("f-name").textContent = r.body.data.user.name;
    showMsg("Profile updated.", true);
  });

  document.getElementById("delete-btn").addEventListener("click", async () => {
    if (!confirm("Delete your account permanently?")) return;
    const r = await apiFetch("/api/users/me", { method: "DELETE" });
    if (!r.res.ok || !r.body || !r.body.success) {
      return showMsg(apiError(r.body, "Delete failed."));
    }
    clearToken();
    window.location.href = "/";
  });
});
