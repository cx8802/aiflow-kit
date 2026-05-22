const settings = {
  bridgeUrl: document.querySelector("#bridge-url"),
  token: document.querySelector("#project-token"),
  automationResult: document.querySelector("#automation-result")
};

const controls = {
  save: document.querySelector("#save-settings"),
  check: document.querySelector("#check-bridge"),
  runAutomation: document.querySelector("#run-automation")
};

const statusText = document.querySelector("#status-text");
const statusDot = document.querySelector("#status-dot");

loadSettings();

controls.save.addEventListener("click", async () => {
  await withBusy(controls.save, async () => {
    await saveSettings();
    await checkBridge();
  });
});

controls.check.addEventListener("click", async () => {
  await withBusy(controls.check, checkBridge);
});

controls.runAutomation.addEventListener("click", async () => {
  await withBusy(controls.runAutomation, async () => {
    await saveSettings();
    const completed = await runNextAutomationJob();
    settings.automationResult.value = JSON.stringify(completed, null, 2);
    setStatus(`Automation job ${completed.jobId} ${completed.status}`, completed.status === "completed" ? "ok" : "error");
  });
});

async function saveSettings() {
  await chrome.storage.local.set({
    bridgeUrl: normalizedBridgeUrl(),
    projectToken: settings.token.value.trim()
  });
}

async function checkBridge() {
  const response = await fetch(`${normalizedBridgeUrl()}/health`);
  const payload = await readPayload(response);
  if (!response.ok) {
    throw new Error(payload.error || `Bridge check failed: ${response.status}`);
  }
  setStatus(`Connected: ${payload.project}; actions: ${payload.actionsDir || "not returned"}`, "ok");
}

async function loadSettings() {
  const saved = await chrome.storage.local.get(["bridgeUrl", "projectToken"]);
  if (saved.bridgeUrl) {
    settings.bridgeUrl.value = saved.bridgeUrl;
  }
  if (saved.projectToken) {
    settings.token.value = saved.projectToken;
  }
}

function normalizedBridgeUrl() {
  return settings.bridgeUrl.value.trim().replace(/\/+$/, "");
}

async function runNextAutomationJob() {
  const response = await sendRuntimeMessage({
    type: "aiflow.runNextAutomationJob",
    bridgeUrl: normalizedBridgeUrl(),
    token: settings.token.value.trim()
  });
  if (!response?.ok) {
    throw new Error(response?.error || "Background automation failed.");
  }
  return response.result;
}

function sendRuntimeMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      const error = chrome.runtime.lastError;
      if (error) {
        reject(new Error(error.message));
        return;
      }
      resolve(response);
    });
  });
}

async function readPayload(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function withBusy(button, work) {
  button.disabled = true;
  try {
    await work();
  } catch (error) {
    setStatus(error.message || String(error), "error");
  } finally {
    button.disabled = false;
  }
}

function setStatus(message, state) {
  statusText.textContent = message;
  statusDot.className = `status-dot ${state || ""}`.trim();
}
