const settings = {
  bridgeUrl: document.querySelector("#bridge-url"),
  token: document.querySelector("#project-token")
};

const controls = {
  save: document.querySelector("#save-settings"),
  check: document.querySelector("#check-bridge")
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
    throw new Error(payload.error || `桥接检查失败：${response.status}`);
  }
  setStatus(`已连接：${payload.project}，元素目录 ${payload.elementsDir || "未返回"}`, "ok");
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
