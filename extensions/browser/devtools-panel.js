const settings = {
  bridgeUrl: document.querySelector("#bridge-url"),
  token: document.querySelector("#project-token"),
  elementResult: document.querySelector("#element-result")
};

const controls = {
  save: document.querySelector("#save-settings"),
  check: document.querySelector("#check-bridge"),
  pickElement: document.querySelector("#pick-element"),
  capturePage: document.querySelector("#capture-page"),
  captureNetwork: document.querySelector("#capture-network"),
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

controls.pickElement.addEventListener("click", async () => {
  await withBusy(controls.pickElement, async () => {
    await saveSettings();
    const element = await readSelectedDevtoolsElement();
    const payload = await sendElementToBridge(element);
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

controls.capturePage.addEventListener("click", async () => {
  await withBusy(controls.capturePage, async () => {
    await saveSettings();
    const page = await readCurrentPageSnapshot();
    const payload = await sendPayloadToBridge("/pages", page);
    settings.elementResult.value = JSON.stringify({ saved: payload.page, url: page.url, title: page.title }, null, 2);
    setStatus(`页面代码已发送到后端：${payload.page}`, "ok");
  });
});

controls.captureNetwork.addEventListener("click", async () => {
  await withBusy(controls.captureNetwork, async () => {
    await saveSettings();
    const capture = await readNetworkSummary();
    const payload = await sendPayloadToBridge("/requests", capture);
    settings.elementResult.value = JSON.stringify(
      { saved: payload.requests, count: capture.entries.length, url: capture.url },
      null,
      2
    );
    setStatus(`请求摘要已发送到后端：${payload.requests}`, "ok");
  });
});

controls.runAutomation.addEventListener("click", async () => {
  await withBusy(controls.runAutomation, async () => {
    await saveSettings();
    const completed = await runNextAutomationJob();
    settings.elementResult.value = JSON.stringify(completed, null, 2);
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

function readSelectedDevtoolsElement() {
  const expression = `(() => {
    const element = $0;
    if (!(element instanceof Element)) {
      return { error: "请先用 DevTools 左上角的选择元素工具选中一个页面元素。" };
    }

    function readText(target) {
      const text = target instanceof HTMLElement ? target.innerText || target.textContent || "" : target.textContent || "";
      return text.replace(/\\s+/g, " ").trim().slice(0, 2000);
    }

    function readValue(target) {
      if (!("value" in target)) {
        return "";
      }
      const type = String(target.getAttribute("type") || "").toLowerCase();
      if (type === "password" || type === "hidden") {
        return "";
      }
      return String(target.value || "").slice(0, 2000);
    }

    function readAttributes(target) {
      const allowed = new Set(["name", "type", "role", "aria-label", "placeholder", "title", "alt"]);
      const attributes = {};
      for (const attr of Array.from(target.attributes)) {
        if (allowed.has(attr.name) || attr.name.startsWith("data-")) {
          attributes[attr.name] = attr.value.slice(0, 500);
        }
      }
      return attributes;
    }

    function escapeCss(value) {
      if (window.CSS?.escape) {
        return CSS.escape(value);
      }
      return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\\\$&");
    }

    function cssPath(target) {
      if (target.id) {
        return "#" + escapeCss(target.id);
      }
      const parts = [];
      let current = target;
      while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.documentElement) {
        let selector = current.tagName.toLowerCase();
        if (current.id) {
          selector += "#" + escapeCss(current.id);
          parts.unshift(selector);
          break;
        }
        const classNames = Array.from(current.classList || [])
          .filter((name) => /^[a-zA-Z0-9_-]+$/.test(name))
          .slice(0, 2);
        if (classNames.length) {
          selector += "." + classNames.map((name) => escapeCss(name)).join(".");
        }
        const parent = current.parentElement;
        if (parent) {
          const sameTagSiblings = Array.from(parent.children).filter((child) => child.tagName === current.tagName);
          if (sameTagSiblings.length > 1) {
            selector += ":nth-of-type(" + (sameTagSiblings.indexOf(current) + 1) + ")";
          }
        }
        parts.unshift(selector);
        current = parent;
      }
      return parts.join(" > ");
    }

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
  })()`;

  return new Promise((resolve, reject) => {
    chrome.devtools.inspectedWindow.eval(expression, { useContentScriptContext: false }, (result, exceptionInfo) => {
      if (exceptionInfo) {
        reject(new Error(exceptionInfo.description || exceptionInfo.value || "读取 DevTools 当前元素失败。"));
        return;
      }
      if (result?.error) {
        reject(new Error(result.error));
        return;
      }
      resolve(result);
    });
  });
}

function readCurrentPageSnapshot() {
  const expression = `(() => ({
    url: window.location.href,
    title: document.title,
    html: document.documentElement ? document.documentElement.outerHTML.slice(0, 500000) : "",
    text: document.body ? (document.body.innerText || document.body.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 120000) : ""
  }))()`;
  return evalInInspectedWindow(expression, "读取页面代码失败。");
}

async function readNetworkSummary() {
  const page = await evalInInspectedWindow(
    `(() => ({ url: window.location.href, title: document.title }))()`,
    "读取当前页面信息失败。"
  );
  return new Promise((resolve) => {
    chrome.devtools.network.getHAR((harLog) => {
      const entries = (harLog.entries || []).slice(-500).map((entry) => ({
        url: entry.request?.url || "",
        method: entry.request?.method || "",
        status: entry.response?.status || 0,
        statusText: entry.response?.statusText || "",
        mimeType: entry.response?.content?.mimeType || "",
        resourceType: entry._resourceType || "",
        startedDateTime: entry.startedDateTime || "",
        time: entry.time || 0
      }));
      resolve({
        url: page.url || "",
        title: page.title || "",
        entries
      });
    });
  });
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
      if (step.action === "wait") {
        await sleep(Number(step.value || 1000));
        results.push({ index, action: "wait", status: "completed", startedAt, completedAt: new Date().toISOString() });
        continue;
      }
      const stepResult = await runPageAction(step);
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

function runPageAction(step) {
  if (step.action === "open") {
    const url = JSON.stringify(step.value || "");
    return evalInInspectedWindow(
      `(() => { window.location.href = ${url}; return { action: "open", url: window.location.href, text: "navigating" }; })()`,
      "打开网址失败。"
    );
  }

  const action = JSON.stringify(step.action || "");
  const selector = JSON.stringify(step.selector || "");
  const value = JSON.stringify(step.value || "");
  const expression = `(() => {
    const action = ${action};
    const selector = ${selector};
    const value = ${value};
    const target = selector ? document.querySelector(selector) : null;
    if (selector && !target) {
      return { error: "未找到选择器：" + selector };
    }
    if (action === "extract") {
      const source = target || document.body || document.documentElement;
      return {
        action,
        selector,
        url: window.location.href,
        title: document.title,
        text: source ? (source.innerText || source.textContent || "").trim().slice(0, 120000) : ""
      };
    }
    if (action === "click") {
      target.click();
      return { action, selector, url: window.location.href, title: document.title, text: "clicked" };
    }
    if (action === "fill") {
      if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) {
        target.focus();
        target.value = value;
        target.dispatchEvent(new Event("input", { bubbles: true }));
        target.dispatchEvent(new Event("change", { bubbles: true }));
      } else if (target instanceof HTMLElement && target.isContentEditable) {
        target.focus();
        target.textContent = value;
        target.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
      } else {
        return { error: "填表目标必须是 input、textarea 或 contenteditable 元素。" };
      }
      return { action, selector, url: window.location.href, title: document.title, text: "filled" };
    }
    return { error: "不支持的动作：" + action };
  })()`;
  return evalInInspectedWindow(expression, "执行页面动作失败。").then((result) => {
    if (result?.error) {
      throw new Error(result.error);
    }
    return result;
  });
}

function evalInInspectedWindow(expression, fallbackMessage) {
  return new Promise((resolve, reject) => {
    chrome.devtools.inspectedWindow.eval(expression, { useContentScriptContext: false }, (result, exceptionInfo) => {
      if (exceptionInfo) {
        reject(new Error(exceptionInfo.description || exceptionInfo.value || fallbackMessage));
        return;
      }
      if (result?.error) {
        reject(new Error(result.error));
        return;
      }
      resolve(result);
    });
  });
}

async function sendElementToBridge(element) {
  return sendPayloadToBridge("/elements", element);
}

async function sendPayloadToBridge(path, payload) {
  const response = await fetch(`${normalizedBridgeUrl()}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Aiflow-Token": settings.token.value.trim()
    },
    body: JSON.stringify(payload)
  });
  const result = await readPayload(response);
  if (!response.ok) {
    throw new Error(result.error || `写入失败：${response.status}`);
  }
  return result;
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
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, Math.min(Number(ms) || 0, 60000))));
}

function setStatus(message, state) {
  statusText.textContent = message;
  statusDot.className = `status-dot ${state || ""}`.trim();
}
