/**
 * Global JavaScript utilities for IncidentMind AI
 */

document.addEventListener("DOMContentLoaded", () => {
  // Update live clock or connection heartbeat if needed
  checkHindsightHeartbeat();
});

async function checkHindsightHeartbeat() {
  try {
    const res = await fetch("/api/hindsight/status");
    const data = await res.json();
    // Heartbeat status is handled by context processor on page loads
  } catch (err) {
    console.debug("Hindsight status ping:", err.message);
  }
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast-notice toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("fade-out");
    setTimeout(() => toast.remove(), 400);
  }, 3000);
}
