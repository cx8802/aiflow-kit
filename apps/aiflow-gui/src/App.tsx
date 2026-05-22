import {
  ArrowUp,
  Bot,
  ChevronRight,
  CircleDot,
  FileCode2,
  FolderGit2,
  GitBranch,
  Layers3,
  MessageSquareDiff,
  Plus,
  Settings2,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
} from "lucide-react";
import { useState } from "react";
import "./App.css";

const agents = {
  codex: {
    label: "Codex",
    mode: "Local worktree",
    icon: TerminalSquare,
    prompt: "Ask Codex to change code, review a diff, or run verification",
    reply:
      "I created the Tauri shell, replaced the starter screen, and checked the new UI at desktop and mobile sizes.",
  },
  claude: {
    label: "Claude Code",
    mode: "Project rules",
    icon: Bot,
    prompt: "Ask Claude Code to plan, implement, or hand off a repo task",
    reply:
      "I can pick up the same project context, follow CLAUDE.md, and keep the GUI work aligned with the shared plan.",
  },
} as const;

const threads = [
  {
    id: "tauri-shell",
    title: "Tauri GUI shell",
    summary: "Desktop thread surface for aiflow agents",
    age: "Now",
  },
  {
    id: "browser-bridge",
    title: "Browser bridge review",
    summary: "Adapter changes and capture status",
    age: "1h",
  },
  {
    id: "skill-updater",
    title: "Updater boundary",
    summary: "Global skills and project install split",
    age: "Today",
  },
] as const;

const reviewFiles = [
  { name: "src/App.tsx", delta: "+214 -41", tone: "mixed" },
  { name: "src/App.css", delta: "+428 -93", tone: "mixed" },
  { name: "src-tauri/tauri.conf.json", delta: "+6 -4", tone: "added" },
  { name: "README.md", delta: "+19 -5", tone: "added" },
];

type AgentKey = keyof typeof agents;
type ThreadId = (typeof threads)[number]["id"];

function App() {
  const [activeAgent, setActiveAgent] = useState<AgentKey>("codex");
  const [activeThread, setActiveThread] = useState<ThreadId>("tauri-shell");
  const agent = agents[activeAgent];
  const AgentIcon = agent.icon;
  const thread = threads.find((item) => item.id === activeThread) ?? threads[0];

  return (
    <main className="app-shell">
      <aside className="project-sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            af
          </span>
          <div>
            <strong>aiflow</strong>
            <span>Desktop</span>
          </div>
        </div>

        <button className="new-thread" type="button">
          <Plus size={18} />
          New task
        </button>

        <section className="project-group" aria-label="Project threads">
          <p className="eyebrow">Project</p>
          <button className="project-button" type="button">
            <FolderGit2 size={18} />
            <span>aiflow-kit</span>
            <ChevronRight size={16} />
          </button>

          <div className="thread-list">
            {threads.map((item) => (
              <button
                className={item.id === activeThread ? "thread-link active" : "thread-link"}
                key={item.id}
                onClick={() => setActiveThread(item.id)}
                type="button"
              >
                <strong>{item.title}</strong>
                <span>{item.summary}</span>
                <small>{item.age}</small>
              </button>
            ))}
          </div>
        </section>

        <nav className="sidebar-tools" aria-label="Desktop sections">
          <button type="button">
            <Layers3 size={17} />
            Skills
          </button>
          <button type="button">
            <Sparkles size={17} />
            Automations
          </button>
          <button type="button">
            <Settings2 size={17} />
            Settings
          </button>
        </nav>
      </aside>

      <section className="thread-surface">
        <header className="thread-header">
          <div className="thread-title">
            <p className="eyebrow">aiflow-kit</p>
            <h1>{thread.title}</h1>
            <span>{thread.summary}</span>
          </div>

          <div className="agent-tabs" role="tablist" aria-label="Agent surface">
            {(Object.keys(agents) as AgentKey[]).map((key) => (
              <button
                aria-selected={key === activeAgent}
                className={key === activeAgent ? "active" : ""}
                key={key}
                onClick={() => setActiveAgent(key)}
                role="tab"
                type="button"
              >
                {agents[key].label}
              </button>
            ))}
          </div>
        </header>

        <section className="thread-scroll" aria-label="Task thread">
          <article className="message user-message">
            <div className="message-label">
              <CircleDot size={16} />
              User
            </div>
            <p>Create a Tauri 2 GUI for Claude Code and Codex, modeled around agent work.</p>
          </article>

          <article className="message agent-message">
            <div className="message-label">
              <AgentIcon size={17} />
              {agent.label}
              <span>{agent.mode}</span>
            </div>
            <p>{agent.reply}</p>

            <section className="inline-review" aria-label="Thread review summary">
              <div>
                <MessageSquareDiff size={18} />
                <strong>Review changes in thread</strong>
              </div>
              <span>4 files ready</span>
              <b>+667</b>
              <em>-143</em>
            </section>
          </article>
        </section>

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
          }}
        >
          <div className="composer-meta">
            <span>
              <FolderGit2 size={15} />
              aiflow-kit
            </span>
            <span>
              <GitBranch size={15} />
              gui/tauri-shell
            </span>
            <span>{agent.label}</span>
          </div>

          <textarea aria-label="Task prompt" placeholder={agent.prompt} rows={3} />

          <div className="composer-actions">
            <button aria-label="Add context" title="Add context" type="button">
              <Plus size={19} />
            </button>
            <button aria-label="Send task" className="send-task" title="Send task" type="submit">
              <ArrowUp size={19} />
            </button>
          </div>
        </form>
      </section>

      <aside className="review-inspector">
        <section className="inspector-block">
          <div className="inspector-heading">
            <FileCode2 size={18} />
            <h2>Changes</h2>
          </div>
          <div className="review-total">
            <span>4 files edited</span>
            <b>+667</b>
            <em>-143</em>
          </div>

          <div className="file-list">
            {reviewFiles.map((file) => (
              <button className={`file-row ${file.tone}`} key={file.name} type="button">
                <span>{file.name}</span>
                <strong>{file.delta}</strong>
                <ChevronRight size={15} />
              </button>
            ))}
          </div>
        </section>

        <section className="inspector-block split">
          <div>
            <p className="eyebrow">Workspace</p>
            <strong>Local worktree</strong>
            <span>Shared project rules</span>
          </div>
          <div>
            <p className="eyebrow">Branch</p>
            <strong>gui/tauri-shell</strong>
            <span>D:\code_work\aiflow-kit</span>
          </div>
        </section>

        <section className="inspector-block verify-block">
          <div className="inspector-heading">
            <ShieldCheck size={18} />
            <h2>Verification</h2>
          </div>
          <div className="verify-row passed">
            <span>Frontend build</span>
            <strong>Passed</strong>
          </div>
          <div className="verify-row passed">
            <span>Viewport checks</span>
            <strong>Passed</strong>
          </div>
          <div className="verify-row pending">
            <span>Tauri desktop build</span>
            <strong>Rust missing</strong>
          </div>
        </section>
      </aside>
    </main>
  );
}

export default App;
