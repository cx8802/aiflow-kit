import { createRequire } from "node:module";
import { mkdir, readFile, writeFile, appendFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error("Usage: node runner.mjs <input.json>");
    process.exit(2);
  }

  const input = JSON.parse(await readFile(inputPath, "utf8"));
  await mkdir(input.outputDir, { recursive: true });

  const sdk = await loadSdk(input.packageDir);
  const prompt = await buildPrompt(input);
  const messagesPath = path.join(input.outputDir, "messages.jsonl");
  const usage = {
    run_id: path.basename(input.outputDir),
    task: input.task,
    model: input.model,
    started_at: new Date().toISOString(),
    input_tokens: 0,
    output_tokens: 0,
    cache_read_tokens: 0,
    cache_creation_tokens: 0,
    total_cost_usd: 0
  };

  let resultText = "";
  const options = {
    cwd: input.cwd,
    model: input.model,
    maxTurns: input.maxTurns,
    maxBudgetUsd: input.maxBudgetUsd,
    permissionMode: input.permissionMode,
    allowedTools: input.allowedTools,
    disallowedTools: input.disallowedTools,
    env: process.env,
    settings: {
      env: claudeEnvironment(process.env),
      includeCoAuthoredBy: false
    },
    settingSources: []
  };
  if (input.claudeCodeExecutable) {
    options.pathToClaudeCodeExecutable = input.claudeCodeExecutable;
  }

  for await (const message of sdk.query({ prompt, options })) {
    await appendFile(messagesPath, JSON.stringify(message) + "\n", "utf8");
    if (message.type === "result") {
      if (typeof message.result === "string") {
        resultText = message.result;
      }
      mergeUsage(usage, message);
    }
  }

  if (!resultText) {
    resultText = "No result text returned by Claude Agent SDK.";
  }

  await writeFile(path.join(input.outputDir, "result.md"), resultText.trim() + "\n", "utf8");
  if (input.writeResultTo) {
    await mkdir(path.dirname(input.writeResultTo), { recursive: true });
    await writeFile(input.writeResultTo, resultText.trim() + "\n", "utf8");
  }
  usage.finished_at = new Date().toISOString();
  await writeFile(path.join(input.outputDir, "usage.json"), JSON.stringify(usage, null, 2) + "\n", "utf8");
  if (input.usageFile) {
    await mkdir(path.dirname(input.usageFile), { recursive: true });
    await appendFile(input.usageFile, JSON.stringify(usage) + "\n", "utf8");
  }
}

function claudeEnvironment(env) {
  const keys = [
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_NAME",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_NAME",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
    "API_TIMEOUT_MS",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY"
  ];
  return Object.fromEntries(keys.filter((key) => env[key]).map((key) => [key, env[key]]));
}

async function loadSdk(packageDir) {
  const requireFromPackage = createRequire(path.join(packageDir, "package.json"));
  const sdkEntry = requireFromPackage.resolve("@anthropic-ai/claude-agent-sdk");
  return import(pathToFileURL(sdkEntry).href);
}

async function buildPrompt(input) {
  const sections = [
    "# Aiflow Claude Agent Task",
    "",
    "You are a project-local worker. Follow the requested task, keep the output concise, and do not reveal secrets.",
    "",
    "## Task",
    "",
    input.prompt,
    ""
  ];

  if (Array.isArray(input.contextFiles) && input.contextFiles.length) {
    const maxChars = Number.isFinite(input.maxContextFileChars) ? input.maxContextFileChars : 12000;
    sections.push("## Context Files", "");
    for (const relative of input.contextFiles) {
      const filePath = path.join(input.cwd, relative);
      try {
        const content = await readFile(filePath, "utf8");
        sections.push(`### ${relative}`, "", "```text", content.slice(0, maxChars), "```", "");
      } catch {
        // Missing context files are fine.
      }
    }
  }

  return sections.join("\n");
}

function mergeUsage(usage, message) {
  if (typeof message.total_cost_usd === "number") {
    usage.total_cost_usd = message.total_cost_usd;
  }
  const source = message.usage || {};
  usage.input_tokens += numberValue(source.input_tokens);
  usage.output_tokens += numberValue(source.output_tokens);
  usage.cache_read_tokens += numberValue(source.cache_read_input_tokens);
  usage.cache_creation_tokens += numberValue(source.cache_creation_input_tokens);
}

function numberValue(value) {
  return typeof value === "number" ? value : 0;
}

main().catch(async (error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
