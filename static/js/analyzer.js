/**
 * IncidentMind AI — Incident Investigation Workspace Frontend Logic
 * Coordinates SRE agent chat, NLP intent processing, telemetry tools,
 * Hindsight memory drawer updates, and human approval gateway.
 */

let activeApprovalData = null;
let currentConversationId = null;

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const incId = urlParams.get("incident_id");
  if (incId) {
    // Automatically load incident context memories
    loadIncidentMemories(incId);
  }
});

function switchIncident(incidentId) {
  if (!incidentId) return;
  window.location.href = `/analyzer?incident_id=${encodeURIComponent(incidentId)}`;
}

function sendQuickPrompt(promptText) {
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = promptText;
    document.getElementById("chat-form").dispatchEvent(new Event("submit", { cancelable: true }));
  }
}

function clearChat() {
  const container = document.getElementById("chat-messages");
  if (container) {
    container.innerHTML = `
      <div class="msg-row msg-agent">
        <div class="msg-avatar">IM</div>
        <div class="msg-bubble">
          <div class="msg-content">
            History cleared. Ready to triage an active alert or answer any SRE questions!
          </div>
          <div class="msg-meta">
            <span class="msg-time">Just now</span>
            <span class="msg-tag">IncidentMind SRE Agent</span>
          </div>
        </div>
      </div>
    `;
  }
  dismissApproval();
}

async function handleChatSubmit(event) {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  const btnSend = document.getElementById("btn-send");
  btnSend.disabled = true;

  // Append user message bubble
  appendMessage("user", message);
  input.value = "";

  const incSelect = document.getElementById("incident-select");
  const targetIncidentId = incSelect ? incSelect.value : null;

  // Add typing indicator
  const typingIndicator = appendTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        conversation_id: currentConversationId,
        incident_id: targetIncidentId
      })
    });

    const data = await res.json();
    typingIndicator.remove();

    if (data.conversation_id) {
      currentConversationId = data.conversation_id;
    }

    // Append agent message bubble
    appendMessage("agent", data.content, data.memories_used, data.why_useful);

    // Update Hindsight memory drawer if memories were recalled
    if (data.memories_used && data.memories_used.length > 0) {
      renderRecalledMemories(data.memories_used);
    }

    // Check if human approval gateway is triggered
    if (data.approval_needed) {
      showApprovalBanner(data.approval_needed);
    } else {
      dismissApproval();
    }
  } catch (err) {
    typingIndicator.remove();
    appendMessage("agent", `⚠️ Error contacting agent engine: ${err.message}`);
  } finally {
    btnSend.disabled = false;
    input.focus();
  }
}

function appendMessage(sender, text, memoriesUsed = [], whyUseful = null) {
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const msgRow = document.createElement("div");
  msgRow.className = `msg-row msg-${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = sender === "agent" ? "IM" : "YOU";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  const content = document.createElement("div");
  content.className = "msg-content";
  content.innerHTML = renderMarkdown(text);

  bubble.appendChild(content);

  const meta = document.createElement("div");
  meta.className = "msg-meta";
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  meta.innerHTML = `<span class="msg-time">${now}</span>`;

  if (sender === "agent") {
    if (memoriesUsed && memoriesUsed.length > 0) {
      meta.innerHTML += ` &bull; <span class="badge-mini text-accent">${memoriesUsed.length} Hindsight Memories Applied</span>`;
    }
    if (whyUseful) {
      meta.innerHTML += ` &bull; <span class="text-xs text-muted" title="${whyUseful}">Why Useful Rationale Included</span>`;
    }
  }

  bubble.appendChild(meta);
  msgRow.appendChild(avatar);
  msgRow.appendChild(bubble);

  container.appendChild(msgRow);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
  const container = document.getElementById("chat-messages");
  const msgRow = document.createElement("div");
  msgRow.className = "msg-row msg-agent typing-row";
  msgRow.innerHTML = `
    <div class="msg-avatar">IM</div>
    <div class="msg-bubble" style="padding: 10px 14px;">
      <span class="status-dot dot-accent" style="display: inline-block; animation: pulse-glow 1s infinite;"></span>
      <span class="text-xs text-muted" style="margin-left: 8px;">IncidentMind is recalling Hindsight memories &amp; checking telemetry...</span>
    </div>
  `;
  container.appendChild(msgRow);
  container.scrollTop = container.scrollHeight;
  return msgRow;
}

function renderRecalledMemories(memories) {
  const stream = document.getElementById("memory-cards-stream");
  const badge = document.getElementById("mem-count-badge");
  const divBox = document.getElementById("divergence-box");
  if (!stream) return;

  stream.innerHTML = "";
  if (badge) {
    badge.textContent = `${memories.length} recalled`;
  }

  // Check for divergence pattern
  const hasPool = memories.some(m => m.text && m.text.toLowerCase().includes("pool"));
  const hasAuth = memories.some(m => m.text && (m.text.toLowerCase().includes("credential") || m.text.toLowerCase().includes("auth")));

  if (hasPool && hasAuth && divBox) {
    divBox.style.display = "block";
  } else if (divBox) {
    divBox.style.display = "none";
  }

  memories.forEach(m => {
    const item = document.createElement("div");
    item.className = `recalled-mem-item ${m.is_warning ? 'item-failed' : 'item-success'}`;

    const badgeLabel = m.is_warning ? "⚠️ FAILED FIX CAUTION" : "✅ PROVEN RESOLUTION";
    const badgeClass = m.is_warning ? "badge-failed" : "badge-resolution";

    item.innerHTML = `
      <div class="recalled-top">
        <span class="font-mono text-xs text-accent"><strong>${m.incident_id || 'INC-HIST'}</strong></span>
        <span class="badge-category ${badgeClass}" style="font-size: 10px;">${badgeLabel}</span>
      </div>
      <p class="recalled-text">${m.text}</p>
      ${m.why_useful ? `<div class="recalled-why"><strong>Why Useful:</strong> ${m.why_useful}</div>` : ''}
    `;
    stream.appendChild(item);
  });
}

async function loadIncidentMemories(incidentId) {
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ incident_id: incidentId })
    });
    const data = await res.json();
    if (data.recall && data.recall.memories) {
      renderRecalledMemories(data.recall.memories);
    }
  } catch (err) {
    console.debug("Auto load memories error:", err);
  }
}

// ==================== DIAGNOSTIC TOOLS ====================

async function runDiagnosticTool(toolName) {
  const incSelect = document.getElementById("incident-select");
  const serviceName = incSelect ? incSelect.options[incSelect.selectedIndex].text.split(":")[1].split("(")[0].trim() : "Payment API";

  const panel = document.getElementById("tool-output-panel");
  const title = document.getElementById("tool-viewer-name");
  const content = document.getElementById("tool-viewer-content");

  panel.style.display = "block";
  title.textContent = `Running ${toolName}...`;
  content.textContent = "Executing simulated SRE diagnostic probe...";

  try {
    const res = await fetch("/api/tools/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool_name: toolName,
        parameters: { service_name: serviceName, lines: 15 }
      })
    });

    const data = await res.json();
    if (data.success) {
      title.textContent = `${toolName} [SUCCESS]`;
      content.textContent = JSON.stringify(data.data, null, 2);

      // Notify in chat
      appendMessage("agent", `🛠️ **Executed Tool**: \`${toolName}\` for \`${serviceName}\`\n\n\`\`\`json\n${JSON.stringify(data.data, null, 2)}\n\`\`\``);
    } else {
      title.textContent = `${toolName} [ERROR]`;
      content.textContent = data.error || "Failed to execute tool";
    }
  } catch (err) {
    title.textContent = `${toolName} [FAILED]`;
    content.textContent = err.message;
  }
}

function closeToolOutput() {
  const panel = document.getElementById("tool-output-panel");
  if (panel) panel.style.display = "none";
}

// ==================== HUMAN APPROVAL GATEWAY ====================

function showApprovalBanner(approval) {
  activeApprovalData = approval;
  const banner = document.getElementById("approval-banner");
  if (!banner) return;

  document.getElementById("approval-title").textContent = approval.action_type ? approval.action_type.replace(/_/g, " ").toUpperCase() : "Remediation Authorization";
  document.getElementById("approval-desc").textContent = approval.description || "Action requires human approval.";
  document.getElementById("approval-risk").textContent = `Risk: ${approval.risk_level || 'Medium'}`;

  banner.style.display = "block";
}

function dismissApproval() {
  activeApprovalData = null;
  const banner = document.getElementById("approval-banner");
  if (banner) banner.style.display = "none";
}

async function confirmApproval() {
  if (!activeApprovalData) return;

  const btn = document.getElementById("btn-approve");
  btn.disabled = true;
  btn.textContent = "Executing...";

  try {
    const res = await fetch("/api/tools/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_id: activeApprovalData.action_id,
        action_type: activeApprovalData.action_type,
        target_service: activeApprovalData.target_service,
        parameters: activeApprovalData.parameters,
        approved_by: "On-Call SRE (Verified)"
      })
    });

    const result = await res.json();
    dismissApproval();

    appendMessage("agent", `🛡️ **Remediation Authorized & Executed**:\n\n- **Action**: \`${activeApprovalData.action_type}\`\n- **Target**: \`${activeApprovalData.target_service}\`\n- **Audit Status**: \`${result.status}\`\n- **Post-Action Telemetry**: Health Status: **${result.post_action_telemetry.health_status}**, Pool Saturation: **${result.post_action_telemetry.pool_saturation_pct}%**, Queue: **${result.post_action_telemetry.waiting_queue}**.\n\n✅ Incident state has transitioned to **Resolved** and all lessons have been retained in Hindsight.`);
  } catch (err) {
    alert("Approval execution error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Authorize Remediation";
  }
}

// Basic markdown formatter
function renderMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks
  html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="font-mono">$1</code>');
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  // Headers
  html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  // Blockquotes
  html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');
  // List items
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
  // Clean redundant uls
  html = html.replace(/<\/ul>\s*<ul>/g, '');
  // Newlines
  html = html.replace(/\n\n/g, '<br><br>');

  return html;
}
