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

let automationTabId = null;

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
    setStatus(`自动化任务 ${completed.jobId} ${completed.status}`, completed.status === "completed" ? "ok" : "error");
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

async function runNextAutomationJob() {
  const response = await fetch(`${normalizedBridgeUrl()}/automation/next`, {
    headers: {
      "X-Aiflow-Token": settings.token.value.trim()
    }
  });
  const payload = await readPayload(response);
  if (!response.ok) {
    throw new Error(payload.error || `读取自动化任务失败：${response.status}`);
  }
  if (!payload.job) {
    throw new Error("没有待执行的自动化任务。");
  }

  const result = await runAutomationJob(payload.job);
  const resultResponse = await fetch(`${normalizedBridgeUrl()}/automation/${encodeURIComponent(payload.job.id)}/result`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Aiflow-Token": settings.token.value.trim()
    },
    body: JSON.stringify(result)
  });
  const resultPayload = await readPayload(resultResponse);
  if (!resultResponse.ok) {
    throw new Error(resultPayload.error || `回写自动化结果失败：${resultResponse.status}`);
  }
  return { ...result, saved: resultPayload.result };
}

async function runAutomationJob(job) {
  const results = [];
  try {
    for (const [index, step] of (job.steps || []).entries()) {
      const startedAt = new Date().toISOString();
      const stepResult = await runAutomationStep(step);
      results.push({
        index,
        status: "completed",
        startedAt,
        completedAt: new Date().toISOString(),
        ...stepResult
      });
    }
    return { status: "completed", jobId: job.id, results };
  } catch (error) {
    return { status: "failed", jobId: job.id, error: error.message || String(error), results };
  }
}

async function runAutomationStep(step) {
  if (step.action === "open") {
    return openAutomationTab(step.value || "");
  }
  if (step.action === "wait") {
    const ms = Math.max(0, Math.min(Number(step.value || 1000) || 0, 60000));
    await sleep(ms);
    return { action: "wait", text: `已等待 ${ms}ms。` };
  }
  if (!["extract", "click", "fill"].includes(step.action)) {
    throw new Error(`不支持的动作：${step.action || ""}`);
  }
  const tabId = automationTabId || (await readActiveTabId());
  await injectAdapter(tabId);
  return executeAdapterAction(tabId, step.action, step.selector || "", step.value || "");
}

async function openAutomationTab(rawUrl) {
  const url = new URL(rawUrl);
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("open 动作只允许 http 或 https URL。");
  }
  const tab = await createTab(url.href);
  automationTabId = tab.id;
  await waitForTabComplete(tab.id, 20000);
  return { action: "open", url: url.href, tabId: tab.id, text: "已打开页面。" };
}

function createTab(url) {
  return new Promise((resolve, reject) => {
    chrome.tabs.create({ url, active: true }, (tab) => {
      const error = chrome.runtime.lastError;
      if (error) {
        reject(new Error(error.message));
        return;
      }
      resolve(tab);
    });
  });
}

function readActiveTabId() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const error = chrome.runtime.lastError;
      if (error) {
        reject(new Error(error.message));
        return;
      }
      const tab = tabs[0];
      if (!tab?.id) {
        reject(new Error("没有可执行自动化的活动标签页。"));
        return;
      }
      automationTabId = tab.id;
      resolve(tab.id);
    });
  });
}

function waitForTabComplete(tabId, timeoutMs) {
  return new Promise((resolve) => {
    let finished = false;
    const finish = () => {
      if (finished) {
        return;
      }
      finished = true;
      clearTimeout(timer);
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    };
    const listener = (updatedTabId, changeInfo) => {
      if (updatedTabId === tabId && changeInfo.status === "complete") {
        finish();
      }
    };
    const timer = setTimeout(finish, timeoutMs);
    chrome.tabs.onUpdated.addListener(listener);
    chrome.tabs.get(tabId, (tab) => {
      if (!chrome.runtime.lastError && tab?.status === "complete") {
        finish();
      }
    });
  });
}

function injectAdapter(tabId) {
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript({ target: { tabId }, files: ["adapter-runtime.js"] }, () => {
      const error = chrome.runtime.lastError;
      if (error) {
        reject(new Error(error.message));
        return;
      }
      resolve();
    });
  });
}

function executeAdapterAction(tabId, action, selector, value) {
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId },
        func: (currentAction, currentSelector, currentValue) =>
          globalThis.runAdapterActionInPage(currentAction, currentSelector, currentValue),
        args: [action, selector, value]
      },
      (results) => {
        const error = chrome.runtime.lastError;
        if (error) {
          reject(new Error(error.message));
          return;
        }
        resolve(results?.[0]?.result || { action, selector, text: "" });
      }
    );
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function setStatus(message, state) {
  statusText.textContent = message;
  statusDot.className = `status-dot ${state || ""}`.trim();
}
