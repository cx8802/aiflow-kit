const settings = {
  bridgeUrl: document.querySelector("#bridge-url"),
  token: document.querySelector("#project-token"),
  elementResult: document.querySelector("#element-result")
};

const controls = {
  save: document.querySelector("#save-settings"),
  check: document.querySelector("#check-bridge"),
  pickElement: document.querySelector("#pick-element")
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

async function sendElementToBridge(element) {
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
  return payload;
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
