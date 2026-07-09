/**
 * DocMind AI — main.js
 * Global utilities: theme toggle, sidebar toggle, toast helper,
 * drag-and-drop upload zone.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ── Dark / Light mode toggle ──────────────────────────────────────────────
  // All dark styles live in main.css via [data-theme="dark"] CSS variables.
  // No separate stylesheet swap needed — just toggle the attribute.
  const html = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon   = document.getElementById("themeIcon");

  function applyTheme(theme) {
    html.setAttribute("data-theme", theme);
    if (themeIcon) {
      themeIcon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
    }
  }

  // Initialise from the attribute set server-side (persisted in DB per user)
  applyTheme(html.getAttribute("data-theme") || "light");

  if (themeToggle) {
    themeToggle.addEventListener("click", async () => {
      const newTheme = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(newTheme);
      try { await fetch("/auth/toggle-theme", { method: "POST" }); } catch (_) {}
    });
  }

  // ── Sidebar toggle (mobile) ───────────────────────────────────────────────
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    // Close on outside click
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") &&
          !sidebar.contains(e.target) &&
          !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  // ── Auto-dismiss flash alerts ─────────────────────────────────────────────
  document.querySelectorAll(".alert").forEach((el) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 5000);
  });
});

// ── Toast utility ─────────────────────────────────────────────────────────────
window.showToast = function (message, type = "primary") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const id = `toast-${Date.now()}`;
  const icons = { success: "check-circle-fill", danger: "x-circle-fill", info: "info-circle-fill", primary: "cpu-fill" };
  const icon = icons[type] || "info-circle-fill";
  container.insertAdjacentHTML("beforeend", `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi bi-${icon}"></i> ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `);
  const toastEl = document.getElementById(id);
  const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 4000 });
  toast.show();
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
};

// ── Markdown-ish text formatter ───────────────────────────────────────────────
window.formatAIText = function (text) {
  if (!text) return "";

  // 1. Bold: **word**
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // 2. Headings: # H1 / ## H2 / ### H3
  text = text.replace(/^#{1,3}\s+(.+)$/gm, "<strong class='d-block mt-2'>$1</strong>");

  // 3. Bullet lines — support -, *, • and numbered 1. 2. 3.
  text = text.replace(/^(?:[-*•]|\d+\.)\s+(.+)$/gm, "<li>$1</li>");

  // 4. Wrap consecutive <li> blocks in <ul> — split on blank lines first
  const parts = text.split(/\n{2,}/);
  text = parts.map((chunk) => {
    if (chunk.includes("<li>")) {
      // Clean orphan newlines around li tags
      return "<ul class='ps-3 my-1'>" + chunk.replace(/\n?(<li>)/g, "$1").replace(/(<\/li>)\n?/g, "$1") + "</ul>";
    }
    return chunk;
  }).join("<br/><br/>");

  // 5. Remaining single newlines → <br/>
  text = text.replace(/\n/g, "<br/>");

  return text;
};
