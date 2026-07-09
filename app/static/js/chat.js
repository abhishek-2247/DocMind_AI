/**
 * DocMind AI — chat.js
 * Handles the AI Chat interface: sending messages, streaming responses,
 * rendering bubbles, and managing conversations.
 */

document.addEventListener("DOMContentLoaded", () => {
  const cfg = window.CHAT_DATA || {};
  let convId = cfg.convId;
  let docId = cfg.docId;

  const docSelect = document.getElementById("docSelect");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const chatMessages = document.getElementById("chatMessages");
  const chatEmpty = document.getElementById("chatEmpty");
  const thinkingOverlay = document.getElementById("thinkingOverlay");
  const currentConvLabel = document.getElementById("currentConvLabel");
  const newConvBtn = document.getElementById("newConvBtn");

  if (docSelect) {
    docSelect.addEventListener("change", () => {
      docId = parseInt(docSelect.value) || null;
    });
  }

  // Quick prompt buttons
  document.querySelectorAll(".quick-prompt").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const prompt = btn.dataset.prompt || btn.textContent.trim();
      if (chatInput) {
        chatInput.value = prompt;
        chatInput.dispatchEvent(new Event("input"));
        chatInput.focus();
      }
    });
  });

  // Send on Enter (Shift+Enter for newline)
  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }
  if (sendBtn) sendBtn.addEventListener("click", sendMessage);

  // New conversation button
  if (newConvBtn) {
    newConvBtn.addEventListener("click", async () => {
      const res = await fetch(cfg.newConvUrl, { method: "POST" });
      const data = await res.json();
      convId = data.conv_id;
      chatMessages.innerHTML = "";
      addEmptyState();
      if (currentConvLabel) currentConvLabel.textContent = "New conversation";
      showToast("New conversation started.", "success");
    });
  }

  async function sendMessage() {
    const message = chatInput?.value.trim();
    if (!message) return;
    if (!docId) {
      showToast("Please select a document first.", "danger");
      return;
    }

    // Remove empty state
    const empty = document.getElementById("chatEmpty");
    if (empty) empty.remove();

    // Render user bubble
    appendBubble("user", message);
    chatInput.value = "";
    chatInput.style.height = "auto";

    // Show thinking
    thinkingOverlay?.classList.remove("d-none");
    sendBtn.disabled = true;

    try {
      const res = await fetch(cfg.sendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, doc_id: docId, conv_id: convId }),
      });
      const data = await res.json();
      if (data.error) {
        showToast(data.error, "danger");
        appendBubble("assistant", `⚠️ ${data.error}`);
      } else {
        convId = data.conv_id;
        if (currentConvLabel) currentConvLabel.textContent = data.conv_title?.substring(0, 50) || "";
        appendBubble("assistant", data.answer);
      }
    } catch (err) {
      appendBubble("assistant", "⚠️ Network error — please try again.");
      showToast("Network error.", "danger");
    } finally {
      thinkingOverlay?.classList.add("d-none");
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  function appendBubble(role, content) {
    const wrap = document.createElement("div");
    wrap.className = `chat-bubble-wrap ${role}`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const avatarContent = role === "user"
      ? (document.querySelector(".user-avatar")?.textContent?.trim() || "U")
      : '<i class="bi bi-cpu-fill"></i>';

    wrap.innerHTML = `
      <div class="chat-avatar">${avatarContent}</div>
      <div class="chat-bubble">
        <div class="bubble-content">${formatAIText(content)}</div>
        <div class="bubble-time">${timeStr}</div>
      </div>`;

    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function addEmptyState() {
    const div = document.createElement("div");
    div.id = "chatEmpty";
    div.className = "chat-empty text-center py-5";
    div.innerHTML = `
      <i class="bi bi-chat-dots text-muted" style="font-size:4rem"></i>
      <h5 class="mt-3">Start a Conversation</h5>
      <p class="text-muted">Select a document above, then ask anything about it.</p>`;
    chatMessages.appendChild(div);
  }

  // Scroll to bottom on load if there are messages
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
});
