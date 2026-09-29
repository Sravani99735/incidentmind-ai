/**
 * 60-Second Guided Demo Logic for Hackathon Judges
 * Steps through INC-0101 -> INC-0145 -> INC-0182 progression.
 */

let currentStep = 1;
const totalSteps = 3;
let autoplayTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  loadStep(1);
});

async function loadStep(stepNum) {
  currentStep = stepNum;

  // Update pills
  for (let i = 1; i <= totalSteps; i++) {
    const pill = document.getElementById(`step-pill-${i}`);
    if (pill) {
      if (i === currentStep) pill.classList.add("active");
      else pill.classList.remove("active");
    }
  }

  // Update buttons
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");
  if (btnPrev) btnPrev.disabled = currentStep === 1;
  if (btnNext) {
    if (currentStep === totalSteps) {
      btnNext.textContent = "Finish & Open Workspace 🚀";
      btnNext.onclick = () => { window.location.href = "/analyzer?incident_id=INC-0182"; };
    } else {
      btnNext.textContent = "Next Step →";
      btnNext.onclick = nextStep;
    }
  }

  const counter = document.getElementById("demo-step-counter");
  if (counter) counter.textContent = `Step ${currentStep} of ${totalSteps}`;

  try {
    const res = await fetch(`/api/demo/state?step=${currentStep}`);
    const data = await res.json();
    const s = data.step_data;

    document.getElementById("demo-step-badge").textContent = `Step ${s.step} of ${totalSteps}`;
    document.getElementById("demo-step-title").textContent = s.title;
    document.getElementById("demo-badge-sub").textContent = s.badge;
    document.getElementById("demo-desc").textContent = s.description;

    // Telemetry
    const telBox = document.getElementById("demo-telemetry-box");
    if (s.failed_action) {
      telBox.innerHTML = `
        <div style="margin-bottom: 6px;"><strong class="text-danger">Failed Action:</strong> ${s.failed_action}</div>
        <div><strong class="text-success">Verified Fix:</strong> ${s.actual_fix}</div>
      `;
    } else if (s.agent_behavior) {
      telBox.innerHTML = `
        <div style="line-height: 1.5;"><strong class="text-accent">Autonomous Agent Reasoning:</strong><br>${s.agent_behavior.replace(/\n/g, '<br>')}</div>
      `;
    } else {
      telBox.innerHTML = `
        <code>Symptoms: ${s.symptoms.join(', ')}<br>Telemetry: ${s.telemetry}</code>
      `;
    }

    // Action Taken
    const actionText = document.getElementById("demo-action-text");
    if (actionText) {
      actionText.textContent = s.action_taken || (s.agent_behavior ? "Evaluated live telemetry against historical models; scaled pool safely." : s.actual_fix);
    }

    // Hindsight memories stored
    const memList = document.getElementById("demo-hindsight-list");
    if (memList) {
      memList.innerHTML = s.hindsight_stored.map(m => `<li>${m}</li>`).join("");
    }

    // Lesson
    const lessonText = document.getElementById("demo-lesson-text");
    if (lessonText) {
      lessonText.textContent = s.lesson;
    }
  } catch (err) {
    console.error("Error loading demo step:", err);
  }
}

function nextStep() {
  if (currentStep < totalSteps) {
    loadStep(currentStep + 1);
  }
}

function prevStep() {
  if (currentStep > 1) {
    loadStep(currentStep - 1);
  }
}

function goToStep(num) {
  loadStep(num);
}

function startAutoplay() {
  const btn = document.getElementById("btn-autoplay");
  if (autoplayTimer) {
    clearInterval(autoplayTimer);
    autoplayTimer = null;
    btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg> Auto-Play 60s Demo`;
    return;
  }

  loadStep(1);
  let step = 1;
  btn.innerHTML = `⏸️ Playing Demo (Step ${step}/3)...`;

  autoplayTimer = setInterval(() => {
    step++;
    if (step <= totalSteps) {
      loadStep(step);
      btn.innerHTML = `⏸️ Playing Demo (Step ${step}/3)...`;
    } else {
      clearInterval(autoplayTimer);
      autoplayTimer = null;
      btn.innerHTML = `✅ Demo Completed!`;
      setTimeout(() => {
        btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg> Auto-Play 60s Demo`;
      }, 4000);
    }
  }, 18000); // 18 seconds per step = ~54 seconds total demo!
}

async function resetDemo() {
  try {
    await fetch("/api/demo/reset", { method: "POST" });
    loadStep(1);
  } catch (err) {
    console.error("Reset demo error:", err);
  }
}
