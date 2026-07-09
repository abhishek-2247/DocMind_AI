/**
 * DocMind AI — insights.js
 * Handles AI Insights generation UI.
 */

document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.INSIGHTS_DATA || {};

  const docSelect = document.getElementById("docSelect");
  const generateBtn = document.getElementById("generateInsightsBtn");
  const insightsLoading = document.getElementById("insightsLoading");
  const insightsResults = document.getElementById("insightsResults");
  const insightsEmpty = document.getElementById("insightsEmpty");

  // If doc already selected server-side, show results
  if (cfg.docId) insightsResults?.classList.remove("d-none");

  docSelect?.addEventListener("change", () => {
    // Reset on new selection
    insightsResults?.classList.add("d-none");
    insightsEmpty?.classList.remove("d-none");
  });

  generateBtn?.addEventListener("click", generateInsights);

  async function generateInsights() {
    const docId = parseInt(docSelect?.value) || cfg.docId;
    if (!docId) {
      showToast("Please select a document.", "danger");
      return;
    }

    insightsEmpty?.classList.add("d-none");
    insightsResults?.classList.add("d-none");
    insightsLoading?.classList.remove("d-none");
    generateBtn.disabled = true;

    try {
      const res = await fetch(cfg.generateUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: docId }),
      });
      const data = await res.json();
      insightsLoading?.classList.add("d-none");

      if (data.error) {
        showToast(data.error, "danger");
        insightsEmpty?.classList.remove("d-none");
        return;
      }

      // Populate stats
      const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
      set("si-pages", data.page_count || "—");
      set("si-words", (data.word_count || 0).toLocaleString());
      set("si-readtime", `~${data.reading_time || "—"} min`);
      set("si-tags", (data.tags || []).length);

      // Keywords
      renderBadges("insightsKeywords", data.keywords || [], "bg-primary text-white");
      renderBadges("insightsTopics", data.topics || [], "bg-success text-white");
      renderBadges("insightsTags", data.tags || [], "bg-accent-soft text-accent");

      const summaryEl = document.getElementById("insightsSummary");
      if (summaryEl) summaryEl.textContent = data.one_line_summary || "—";

      insightsResults?.classList.remove("d-none");
      showToast("Insights extracted!", "success");
    } catch (err) {
      insightsLoading?.classList.add("d-none");
      insightsEmpty?.classList.remove("d-none");
      showToast("Network error. Try again.", "danger");
    } finally {
      generateBtn.disabled = false;
    }
  }

  function renderBadges(containerId, items, cssClass) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = items.map(
      (item) => `<span class="badge ${cssClass} rounded-pill px-3">${item}</span>`
    ).join("");
  }
});
