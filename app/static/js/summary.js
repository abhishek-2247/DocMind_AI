/**
 * DocMind AI — summary.js
 * Handles AI summary generation UI.
 */

document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.SUMMARY_DATA || {};

  const docSelect = document.getElementById("docSelect");
  const generateBtn = document.getElementById("generateBtn");
  const summaryEmpty = document.getElementById("summaryEmpty");
  const summaryLoading = document.getElementById("summaryLoading");
  const summaryResult = document.getElementById("summaryResult");
  const summaryContent = document.getElementById("summaryContent");
  const summaryDocName = document.getElementById("summaryDocName");
  const styleLabel = document.getElementById("styleLabel");
  const copyBtn = document.getElementById("copyBtn");

  generateBtn?.addEventListener("click", generateSummary);

  async function generateSummary() {
    const docId = docSelect?.value;
    if (!docId) {
      showToast("Please select a document.", "danger");
      return;
    }
    const style = document.querySelector('input[name="summaryStyle"]:checked')?.value || "bullets";

    // UI transitions
    summaryEmpty?.classList.add("d-none");
    summaryResult?.classList.add("d-none");
    summaryLoading?.classList.remove("d-none");
    generateBtn.disabled = true;

    try {
      const res = await fetch(cfg.generateUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: parseInt(docId), style }),
      });
      const data = await res.json();

      summaryLoading?.classList.add("d-none");

      if (data.error) {
        showToast(data.error, "danger");
        summaryEmpty?.classList.remove("d-none");
      } else {
        const styleNames = { short: "Short Summary", detailed: "Detailed Summary", bullets: "Bullet Points" };
        const styleColors = { short: "bg-primary text-white", detailed: "bg-success text-white", bullets: "bg-warning text-dark" };
        if (styleLabel) {
          styleLabel.textContent = styleNames[style] || style;
          styleLabel.className = `badge mb-3 ${styleColors[style] || "bg-secondary"}`;
        }
        if (summaryDocName) summaryDocName.textContent = `— ${data.doc_name}`;
        if (summaryContent) summaryContent.innerHTML = formatAIText(data.summary);
        summaryResult?.classList.remove("d-none");
        copyBtn?.classList.remove("d-none");
        showToast("Summary generated!", "success");
      }
    } catch (err) {
      summaryLoading?.classList.add("d-none");
      summaryEmpty?.classList.remove("d-none");
      showToast("Network error. Try again.", "danger");
    } finally {
      generateBtn.disabled = false;
    }
  }

  copyBtn?.addEventListener("click", () => {
    const text = summaryContent?.innerText || "";
    navigator.clipboard.writeText(text).then(() => showToast("Copied to clipboard!", "success"));
  });
});
