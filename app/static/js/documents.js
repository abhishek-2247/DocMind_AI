/**
 * DocMind AI — documents.js
 * Drag-and-drop upload zone, form auto-submit on file select.
 */

document.addEventListener("DOMContentLoaded", () => {
  const uploadZone = document.getElementById("uploadZone");
  const fileInput = document.getElementById("fileInput");
  const uploadForm = document.getElementById("uploadForm");
  const fileNameEl = document.getElementById("uploadFileName");
  const progress = document.getElementById("uploadProgress");
  const progressBar = progress?.querySelector(".progress-bar");

  if (!uploadZone || !fileInput || !uploadForm) return;

  // Drag-and-drop handlers
  ["dragenter", "dragover"].forEach((evt) => {
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.remove("drag-over");
    });
  });

  uploadZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length) {
      fileInput.files = files;
      handleFile(files[0]);
    }
  });

  // Click-to-browse
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
  });

  function handleFile(file) {
    const allowed = ["pdf", "docx", "pptx", "txt"];
    const ext = file.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      showToast(`File type ".${ext}" is not supported.`, "danger");
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      showToast("File exceeds the 16 MB limit.", "danger");
      return;
    }

    // Show filename
    fileNameEl.textContent = `Selected: ${file.name}`;
    fileNameEl.classList.remove("d-none");

    // Progress UI
    progress.classList.remove("d-none");

    // Fake progress then submit
    let pct = 0;
    const ticker = setInterval(() => {
      pct = Math.min(pct + 15, 90);
      if (progressBar) progressBar.style.width = pct + "%";
    }, 120);

    setTimeout(() => {
      clearInterval(ticker);
      if (progressBar) progressBar.style.width = "100%";
      uploadForm.submit();
    }, 900);
  }

  // Click anywhere in zone (not just the button)
  uploadZone.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") fileInput.click();
  });
});
