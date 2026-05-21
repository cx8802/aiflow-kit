const settings = {
  bridgeUrl: document.querySelector("#bridge-url"),
  token: document.querySelector("#project-token"),
  note: document.querySelector("#capture-note"),
  adapter: document.querySelector("#adapter-select"),
  action: document.querySelector("#action-select"),
  selector: document.querySelector("#action-selector"),
  value: document.querySelector("#action-value"),
  result: document.querySelector("#action-result"),
  elementResult: document.querySelector("#element-result"),
  automationResult: document.querySelector("#automation-result")
};

const controls = {
  save: document.querySelector("#save-settings"),
  check: document.querySelector("#check-bridge"),
  pickElement: document.querySelector("#pick-element"),
  capture: document.querySelector("#capture-selection"),
  reloadAdapters: document.querySelector("#reload-adapters"),
  runAction: document.querySelector("#run-action"),
  runAutomation: document.querySelector("#run-automation"),
  toggleExecutor: document.querySelector("#toggle-executor")
};

const statusText = document.querySelector("#status-text");
const statusDot = document.querySelector("#status-dot");
let adapters = [];
let executorTimer = null;
let executorBusy = false;
const EXECUTOR_INTERVAL_MS = 1500;

loadSettings();
loadAdapters();

controls.save.addEventListener("click", async () => {
  await withBusy(controls.save, async () => {
    await saveSettings();
    await checkBridge();
  });
});

controls.check.addEventListener("click", async () => {
  await withBusy(controls.check, checkBridge);
});

controls.pickElement.addEventListener("click", async () => {
  await withBusy(controls.pickElement, async () => {
    await saveSettings();
    setStatus("请在当前网页中单击要选择的元素，按 Esc 取消。", "ok");
    const element = await pickElementFromActiveTab();
    const response = await fetch(`${normalizedBridgeUrl()}/elements`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Aiflow-Token": settings.token.value.trim()
      },
      body: JSON.stringify(element)
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new Error(payload.error || `元素写入失败：${response.status}`);
    }
    settings.elementResult.value = JSON.stringify(
      {
        saved: payload.element,
        selector: element.selector,
        tagName: element.tagName,
        text: element.text
      },
      null,
      2
    );
    setStatus(`元素已发送到后端：${payload.element}`, "ok");
  });
});

controls.capture.addEventListener("click", async () => {
  await withBusy(controls.capture, async () => {
    const page = await readActivePageContext();
    const response = await fetch(`${normalizedBridgeUrl()}/captures`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Aiflow-Token": settings.token.value.trim()
      },
      body: JSON.stringify({
        type: page.selection ? "selection" : "page",
        url: page.url,
        title: page.title,
        selection: page.selection,
        note: settings.note.value.trim()
      })
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new Error(payload.error || `采集失败：${response.status}`);
    }
    settings.note.value = "";
    setStatus(`已保存：${payload.capture}`, "ok");
  });
});

controls.reloadAdapters.addEventListener("click", async () => {
  await withBusy(controls.reloadAdapters, loadAdapters);
});

settings.adapter.addEventListener("change", populateActions);
settings.action.addEventListener("change", updateActionFields);

controls.runAction.addEventListener("click", async () => {
  await withBusy(controls.runAction, async () => {
    const adapter = selectedAdapter();
    const action = selectedAction();
    if (!adapter || !action) {
      throw new Error("请先选择适配器动作。");
    }
    const page = await runActionInActiveTab(action.id, settings.selector.value.trim(), settings.value.value);
    settings.result.value = JSON.stringify(
      {
        adapter: adapter.id,
        ...page
      },
      null,
      2
    );
    setStatus(`${adapter.displayName}：${action.label} 已完成。`, "ok");
  });
});

controls.runAutomation.addEventListener("click", async () => {
  await withBusy(controls.runAutomation, async () => {
    await runNextAutomationJob({ quietWhenEmpty: false });
  });
});

controls.toggleExecutor.addEventListener("click", () => {
  if (executorTimer) {
    stopExecutor("后台执行器已停止。");
    return;
  }
  startExecutor();
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

async function loadAdapters() {
  const indexResponse = await fetch(chrome.runtime.getURL("adapters/index.json"));
  const index = await readPayload(indexResponse);
  if (!indexResponse.ok || !Array.isArray(index.adapters)) {
    throw new Error("无法加载适配器注册表。");
  }
  adapters = await Promise.all(
    index.adapters.map(async (file) => {
      const response = await fetch(chrome.runtime.getURL(`adapters/${file}`));
      const payload = await readPayload(response);
      if (!response.ok) {
        throw new Error(`无法加载适配器：${file}`);
      }
      return payload;
    })
  );
  settings.adapter.replaceChildren(
    ...adapters.map((adapter) => new Option(adapter.displayName || adapter.id, adapter.id))
  );
  populateActions();
}

function populateActions() {
  const adapter = selectedAdapter();
  settings.action.replaceChildren(
    ...(adapter?.actions || []).map((action) => new Option(action.label || action.id, action.id))
  );
  updateActionFields();
}

function updateActionFields() {
  const action = selectedAction();
  settings.selector.disabled = !action;
  settings.value.disabled = !action?.usesValue;
  settings.selector.placeholder = action?.requiresSelector
    ? "#submit, [data-row], main h1"
    : "可选；留空则使用当前选中文本";
}

function selectedAdapter() {
  return adapters.find((adapter) => adapter.id === settings.adapter.value);
}

function selectedAction() {
  const adapter = selectedAdapter();
  return adapter?.actions?.find((action) => action.id === settings.action.value);
}

function normalizedBridgeUrl() {
  return settings.bridgeUrl.value.trim().replace(/\/+$/, "");
}

async function pickElementFromActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("没有可用的当前标签页。");
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: pickElementInPage
  });
  if (!result?.result) {
    throw new Error("未返回元素信息。");
  }
  if (result.result.cancelled) {
    throw new Error("已取消选择元素。");
  }
  return result.result;
}

function pickElementInPage() {
  return new Promise((resolve) => {
    if (window.__aiflowElementPickerCleanup) {
      window.__aiflowElementPickerCleanup();
    }

    const overlay = document.createElement("div");
    overlay.style.cssText = [
      "position:fixed",
      "z-index:2147483647",
      "pointer-events:none",
      "border:2px solid #0f766e",
      "background:rgba(15,118,110,0.12)",
      "box-shadow:0 0 0 99999px rgba(15,23,42,0.08)",
      "border-radius:3px",
      "display:none"
    ].join(";");
    document.documentElement.appendChild(overlay);

    function cleanup() {
      document.removeEventListener("mousemove", onMouseMove, true);
      document.removeEventListener("click", onClick, true);
      document.removeEventListener("keydown", onKeyDown, true);
      overlay.remove();
      window.__aiflowElementPickerCleanup = null;
    }

    function finish(payload) {
      cleanup();
      resolve(payload);
    }

    function onMouseMove(event) {
      const target = event.target;
      if (!(target instanceof Element) || target === overlay) {
        return;
      }
      const rect = target.getBoundingClientRect();
      overlay.style.display = "block";
      overlay.style.left = `${Math.max(0, rect.left)}px`;
      overlay.style.top = `${Math.max(0, rect.top)}px`;
      overlay.style.width = `${Math.max(0, rect.width)}px`;
      overlay.style.height = `${Math.max(0, rect.height)}px`;
    }

    function onClick(event) {
      const target = event.target;
      if (!(target instanceof Element) || target === overlay) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      finish(readElement(target));
    }

    function onKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        finish({ cancelled: true });
      }
    }

    function readElement(element) {
      const rect = element.getBoundingClientRect();
      return {
        url: window.location.href,
        title: document.title,
        selector: cssPath(element),
        tagName: element.tagName.toLowerCase(),
        id: element.id || "",
        className: typeof element.className === "string" ? element.className : "",
        text: readText(element),
        href: "href" in element ? String(element.href || "") : "",
        value: readValue(element),
        attributes: readAttributes(element),
        rect: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        }
      };
    }

    function readText(element) {
      const text = element instanceof HTMLElement ? element.innerText || element.textContent || "" : element.textContent || "";
      return text.replace(/\s+/g, " ").trim().slice(0, 2000);
    }

    function readValue(element) {
      if (!("value" in element)) {
        return "";
      }
      const type = String(element.getAttribute("type") || "").toLowerCase();
      if (type === "password" || type === "hidden") {
        return "";
      }
      return String(element.value || "").slice(0, 2000);
    }

    function readAttributes(element) {
      const allowed = new Set(["name", "type", "role", "aria-label", "placeholder", "title", "alt"]);
      const attributes = {};
      for (const attr of Array.from(element.attributes)) {
        if (allowed.has(attr.name) || attr.name.startsWith("data-")) {
          attributes[attr.name] = attr.value.slice(0, 500);
        }
      }
      return attributes;
    }

    function cssPath(element) {
      if (element.id) {
        return `#${escapeCss(element.id)}`;
      }
      const parts = [];
      let current = element;
      while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.documentElement) {
        let selector = current.tagName.toLowerCase();
        if (current.id) {
          selector += `#${escapeCss(current.id)}`;
          parts.unshift(selector);
          break;
        }
        const classNames = Array.from(current.classList || [])
          .filter((name) => /^[a-zA-Z0-9_-]+$/.test(name))
          .slice(0, 2);
        if (classNames.length) {
          selector += `.${classNames.map((name) => escapeCss(name)).join(".")}`;
        }
        const parent = current.parentElement;
        if (parent) {
          const sameTagSiblings = Array.from(parent.children).filter((child) => child.tagName === current.tagName);
          if (sameTagSiblings.length > 1) {
            selector += `:nth-of-type(${sameTagSiblings.indexOf(current) + 1})`;
          }
        }
        parts.unshift(selector);
        current = parent;
      }
      return parts.join(" > ");
    }

    function escapeCss(value) {
      if (window.CSS?.escape) {
        return CSS.escape(value);
      }
      return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
    }

    window.__aiflowElementPickerCleanup = cleanup;
    document.addEventListener("mousemove", onMouseMove, true);
    document.addEventListener("click", onClick, true);
    document.addEventListener("keydown", onKeyDown, true);
  });
}

async function runActionInActiveTab(action, selector, value) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("没有可用的当前标签页。");
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: runAdapterActionInPage,
    args: [action, selector, value]
  });
  if (!result?.result) {
    throw new Error("适配器动作没有返回结果。");
  }
  return result.result;
}

async function runAutomationJob(job) {
  const results = [];
  try {
    for (const [index, step] of (job.steps || []).entries()) {
      const startedAt = new Date().toISOString();
      if (step.action === "wait") {
        await sleep(Number(step.value || 1000));
        results.push({
          index,
          action: step.action,
          status: "completed",
          startedAt,
          completedAt: new Date().toISOString(),
          text: `已等待 ${step.value || 1000} 毫秒。`
        });
        continue;
      }
      const stepResult = await runActionInActiveTab(step.action, step.selector || "", step.value || "");
      results.push({
        index,
        status: "completed",
        startedAt,
        completedAt: new Date().toISOString(),
        ...stepResult
      });
    }
    return {
      status: "completed",
      jobId: job.id,
      results
    };
  } catch (error) {
    return {
      status: "failed",
      jobId: job.id,
      error: error.message || String(error),
      results
    };
  }
}

async function runNextAutomationJob({ quietWhenEmpty }) {
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
    if (!quietWhenEmpty) {
      setStatus("没有待执行的自动化任务。", "ok");
      settings.automationResult.value = "";
    }
    return false;
  }

  const result = await runAutomationJob(payload.job);
  settings.automationResult.value = JSON.stringify(result, null, 2);
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
  const label = result.status === "completed" ? "已完成" : "失败";
  setStatus(`自动化任务 ${payload.job.id} ${label}。`, result.status === "completed" ? "ok" : "error");
  return true;
}

function startExecutor() {
  controls.toggleExecutor.textContent = "停止执行器";
  setStatus("后台执行器已启动，等待项目后台任务。", "ok");
  executorTimer = window.setInterval(async () => {
    if (executorBusy) {
      return;
    }
    executorBusy = true;
    try {
      await runNextAutomationJob({ quietWhenEmpty: true });
    } catch (error) {
      stopExecutor(error.message || String(error), "error");
    } finally {
      executorBusy = false;
    }
  }, EXECUTOR_INTERVAL_MS);
}

function stopExecutor(message, state = "ok") {
  if (executorTimer) {
    window.clearInterval(executorTimer);
    executorTimer = null;
  }
  executorBusy = false;
  controls.toggleExecutor.textContent = "启动执行器";
  setStatus(message, state);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, Math.min(Number(ms) || 0, 60000))));
}

async function readActivePageContext() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("没有可用的当前标签页。");
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => ({
      title: document.title,
      url: window.location.href,
      selection: window.getSelection()?.toString().trim() || ""
    })
  });
  if (!result?.result) {
    throw new Error("无法读取当前页面。");
  }
  return result.result;
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
