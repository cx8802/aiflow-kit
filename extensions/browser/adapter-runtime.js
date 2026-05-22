async function runAdapterActionInPage(action, selector, value) {
  const selectedText = window.getSelection()?.toString().trim() || "";

  if (action === "snapshot") {
    return snapshotPage(selector || "");
  }

  if (action === "extract") {
    const target = selector ? findSingleTarget(selector) : null;
    const source = target || document.body || document.documentElement;
    const text = target ? target.innerText || target.textContent || "" : selectedText || source?.innerText || source?.textContent || "";
    return {
      action,
      selector,
      title: document.title,
      url: window.location.href,
      text: text.trim().slice(0, 120000)
    };
  }

  if (action === "scroll") {
    const target = selector ? findSingleTarget(selector) : null;
    return scrollPage(selector || "", value, target);
  }

  if (!selector) {
    throw new Error(`${action} requires a selector.`);
  }

  const target = findSingleTarget(selector);

  if (action === "click") {
    target.scrollIntoView({ block: "center", inline: "nearest" });
    target.click();
    return {
      action,
      selector,
      title: document.title,
      url: window.location.href,
      snapshot: compactPageSignal(),
      text: "clicked"
    };
  }

  if (action === "fill") {
    target.scrollIntoView({ block: "center", inline: "nearest" });
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
      throw new Error("Fill target must be input, textarea, or contenteditable.");
    }
    return {
      action,
      selector,
      title: document.title,
      url: window.location.href,
      snapshot: compactPageSignal(),
      text: "filled"
    };
  }

  throw new Error(`Unsupported adapter action: ${action}`);
}

function findSingleTarget(selector) {
  const matches = Array.from(document.querySelectorAll(selector));
  if (matches.length === 0) {
    throw new Error(`Selector not found: ${selector}`);
  }
  if (matches.length > 1) {
    throw new Error(`Selector is ambiguous (${matches.length} matches): ${selector}`);
  }
  return matches[0];
}

function snapshotPage(selector) {
  const source = selector ? findSingleTarget(selector) : document.body || document.documentElement;
  return {
    action: "snapshot",
    selector,
    title: document.title,
    url: window.location.href,
    signal: compactPageSignal(source)
  };
}

function compactPageSignal(source = document.body || document.documentElement) {
  const links = Array.from(document.querySelectorAll("a[href]")).slice(0, 30).map((item) => ({
    text: cleanText(item.innerText || item.textContent || item.getAttribute("aria-label") || ""),
    href: item.href
  }));
  const controls = Array.from(document.querySelectorAll("button, input, textarea, select, [role='button'], [contenteditable='true']"))
    .slice(0, 40)
    .map((item) => ({
      tag: item.tagName.toLowerCase(),
      type: item.getAttribute("type") || "",
      text: cleanText(item.innerText || item.textContent || item.getAttribute("aria-label") || item.getAttribute("placeholder") || ""),
      id: item.id || "",
      name: item.getAttribute("name") || "",
      disabled: Boolean(item.disabled || item.getAttribute("aria-disabled") === "true")
    }));
  return {
    title: document.title,
    url: window.location.href,
    text: cleanText(source?.innerText || source?.textContent || ""),
    scrollX: window.scrollX,
    scrollY: window.scrollY,
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    },
    links,
    controls
  };
}

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim().slice(0, 2000);
}

function scrollPage(selector, value, target) {
  const rawValue = String(value || "down").trim().toLowerCase();
  const viewportStep = Math.max(200, Math.round(window.innerHeight * 0.8));
  let deltaX = 0;
  let deltaY = viewportStep;
  let absoluteY = null;

  if (rawValue === "up") {
    deltaY = -viewportStep;
  } else if (rawValue === "down" || rawValue === "") {
    deltaY = viewportStep;
  } else if (rawValue === "top") {
    absoluteY = 0;
  } else if (rawValue === "bottom") {
    absoluteY = document.documentElement.scrollHeight;
  } else if (/^-?\d+$/.test(rawValue)) {
    deltaY = Number(rawValue);
  } else if (/^-?\d+\s*,\s*-?\d+$/.test(rawValue)) {
    const [x, y] = rawValue.split(",").map((item) => Number(item.trim()));
    deltaX = x;
    deltaY = y;
  } else {
    throw new Error("scroll value must be down, up, top, bottom, pixels, or x,y.");
  }

  if (target instanceof HTMLElement) {
    target.scrollIntoView({ block: "center", inline: "nearest" });
  }
  if (absoluteY !== null) {
    window.scrollTo({ top: absoluteY, left: window.scrollX });
  } else {
    window.scrollBy({ left: deltaX, top: deltaY });
  }

  return {
    action: "scroll",
    selector,
    title: document.title,
    url: window.location.href,
    scrollX: window.scrollX,
    scrollY: window.scrollY,
    text: "scrolled"
  };
}

globalThis.runAdapterActionInPage = runAdapterActionInPage;
