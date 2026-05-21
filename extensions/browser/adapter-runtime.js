async function runAdapterActionInPage(action, selector, value) {
  const selectedText = window.getSelection()?.toString().trim() || "";

  if (action === "extract") {
    const target = selector ? document.querySelector(selector) : null;
    if (selector && !target) {
      throw new Error(`未找到选择器：${selector}`);
    }
    const text = target ? target.innerText || target.textContent || "" : selectedText;
    return {
      action,
      selector,
      title: document.title,
      url: window.location.href,
      text: text.trim().slice(0, 120000)
    };
  }

  if (!selector) {
    throw new Error(`${action} 需要选择器。`);
  }

  const target = document.querySelector(selector);
  if (!target) {
    throw new Error(`未找到选择器：${selector}`);
  }

  if (action === "click") {
    target.click();
    return {
      action,
      selector,
      title: document.title,
      url: window.location.href,
      text: "已点击。"
    };
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
      throw new Error("填表目标必须是 input、textarea 或 contenteditable 元素。");
    }
    return {
      action,
      selector,
      title: document.title,
      url: window.location.href,
      text: "已填入。"
    };
  }

  throw new Error(`不支持的适配器动作：${action}`);
}
