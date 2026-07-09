/**
 * DocMind AI — compare.js
 * Handles document comparison UI.
 */

document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.COMPARE_DATA || {};

  const docA = document.getElementById("docA");
  const docB = document.getElementById("docB");
  const compareBtn = document.getElementById("compareBtn");
  const compareLoading = document.getElementById("compareLoading");
  const compareResults = document.getElementById("compareResults");
  const compareEmpty = document.getElementById("compareEmpty");

  compareBtn?.addEventListener("click", runCompare);

  async function runCompare() {
    const idA = parseInt(docA?.value);
    const idB = parseInt(docB?.value);

    if (!idA || !idB) {
      showToast("Please select both documents.", "danger");
      return;
    }
    if (idA === idB) {
      showToast("Please select two different documents.", "danger");
      return;
    }

    compareEmpty?.classList.add("d-none");
    compareResults?.classList.add("d-none");
    compareLoading?.classList.remove("d-none");
    compareBtn.disabled = true;

    try {
      const res = await fetch(cfg.compareUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id_a: idA, doc_id_b: idB }),
      });
      const data = await res.json();
      compareLoading?.classList.add("d-none");

      if (data.error) {
        showToast(data.error, "danger");
        compareEmpty?.classList.remove("d-none");
      } else {
        document.getElementById("resultSimilarities").innerHTML = formatAIText(data.similarities || data.raw || "—");
        document.getElementById("resultDifferences").innerHTML = formatAIText(data.differences || "—");
        document.getElementById("resultTopics").innerHTML = formatAIText(data.key_topics || "—");
        document.getElementById("resultSummary").innerHTML = formatAIText(data.summary || "—");
        compareResults?.classList.remove("d-none");
        showToast("Comparison complete!", "success");
      }
    } catch (err) {
      compareLoading?.classList.add("d-none");
      compareEmpty?.classList.remove("d-none");
      showToast("Network error. Try again.", "danger");
    } finally {
      compareBtn.disabled = false;
    }
  }
});
