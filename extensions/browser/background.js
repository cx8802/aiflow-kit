chrome.action.onClicked.addListener(() => {
  chrome.runtime.openOptionsPage();
});

let automationTabId = null;

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "aiflow.runNextAutomationJob") {
    return false;
  }

  runNextAutomationJob(message.bridgeUrl, message.token)
    .then((result) => sendResponse({ ok: true, result }))
    .catch((error) => sendResponse({ ok: false, error: error.message || String(error) }));
  return true;
});

async function runNextAutomationJob(bridgeUrl, token) {
  const normalizedBridgeUrl = normalizeBridgeUrl(bridgeUrl);
  const projectToken = String(token || "").trim();
  if (!normalizedBridgeUrl) {
    throw new Error("Bridge URL is required.");
  }
  if (!projectToken) {
    throw new Error("Project token is required.");
  }

  const response = await fetch(`${normalizedBridgeUrl}/automation/next`, {
    headers: {
      "X-Aiflow-Token": projectToken
    }
  });
  const payload = await readPayload(response);
  if (!response.ok) {
    throw new Error(payload.error || `Failed to read automation job: ${response.status}`);
  }
  if (!payload.job) {
    throw new Error("No pending backend automation job.");
  }

  const result = await runAutomationJob(payload.job);
  const resultResponse = await fetch(`${normalizedBridgeUrl}/automation/${encodeURIComponent(payload.job.id)}/result`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Aiflow-Token": projectToken
    },
    body: JSON.stringify(result)
  });
  const resultPayload = await readPayload(resultResponse);
  if (!resultResponse.ok) {
    throw new Error(resultPayload.error || `Failed to write automation result: ${resultResponse.status}`);
  }
  return { ...result, saved: resultPayload.result };
}

async function runAutomationJob(job) {
  const results = [];
  try {
    automationTabId = null;
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
    return { action: "wait", text: `waited ${ms}ms` };
  }
  if (!["snapshot", "extract", "click", "fill", "scroll"].includes(step.action)) {
    throw new Error(`Unsupported action: ${step.action || ""}`);
  }

  const tabId = automationTabId || (await readActiveTabId());
  await injectAdapter(tabId);
  return executeAdapterAction(tabId, step.action, step.selector || "", step.value || "");
}

async function openAutomationTab(rawUrl) {
  const url = new URL(rawUrl);
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("open action only allows http or https URLs.");
  }
  const tab = await createTab(url.href);
  automationTabId = tab.id;
  await waitForTabComplete(tab.id, 20000);
  return { action: "open", url: url.href, tabId: tab.id, text: "opened" };
}

function createTab(url) {
  return new Promise((resolve, reject) => {
    chrome.tabs.create({ url, active: false }, (tab) => {
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
        reject(new Error("No active tab is available for automation."));
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

function normalizeBridgeUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

async function readPayload(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
