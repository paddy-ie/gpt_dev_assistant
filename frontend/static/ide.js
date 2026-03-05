const state = {
  project: "root",
  selectedPath: null,
  selectedType: null,
  currentPath: null,
  originalContent: "",
  dirty: false,
};

const assistantState = {
  messages: [],
  loading: false,
};

const agentState = {
  jobId: null,
  events: [],
  cursor: 0,
  polling: null,
  status: 'idle',
};

const ui = {
  status: document.getElementById("status"),
  projectSelect: document.getElementById("project-select"),
  newProject: document.getElementById("new-project"),
  deleteProject: document.getElementById("delete-project"),
  fileTree: document.getElementById("file-tree"),
  editor: document.getElementById("editor"),
  currentPath: document.getElementById("current-path"),
  saveBtn: document.getElementById("save-btn"),
  runBtn: document.getElementById("run-btn"),
  output: document.getElementById("run-output"),
  sidebarActions: document.querySelector(".sidebar-actions"),
  assistantForm: document.getElementById("assistant-form"),
  assistantInput: document.getElementById("assistant-input"),
  assistantSubmit: document.getElementById("assistant-submit"),
  assistantClear: document.getElementById("assistant-clear"),
  assistantLog: document.getElementById("assistant-log"),
  assistantIncludeFile: document.getElementById("assistant-include-file"),
  agentForm: document.getElementById("agent-form"),
  agentGoal: document.getElementById("agent-goal"),
  agentTestCommand: document.getElementById("agent-test-command"),
  agentReflections: document.getElementById("agent-reflections"),
  agentTimeout: document.getElementById("agent-timeout"),
  agentModel: document.getElementById("agent-model"),
  agentStart: document.getElementById("agent-start"),
  agentStop: document.getElementById("agent-stop"),
  agentStatus: document.getElementById("agent-status"),
  agentLog: document.getElementById("agent-log"),
};

init();

async function init() {
  attachEvents();
  await refreshProjects();
  await loadTree();
  clearEditor();
  await loadAssistantHistory();
  renderAssistantLog();
  renderAgentLog();
  updateAgentControls();
  setAgentStatusBadge('Idle', 'idle');
  setStatus("Ready");
}

function attachEvents() {
  ui.projectSelect.addEventListener("change", async (event) => {
    if (!(await confirmDiscard())) {
      ui.projectSelect.value = state.project;
      return;
    }
    state.project = event.target.value;
    state.selectedPath = null;
    state.currentPath = null;
    await loadTree();
    clearEditor();
    await loadAssistantHistory();
  });

  ui.newProject.addEventListener("click", async () => {
    const name = prompt("New project name");
    if (!name) {
      return;
    }
    try {
      await apiRequest("/api/projects", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      });
      await refreshProjects(name.trim());
      await loadTree();
      await loadAssistantHistory();
      setStatus(`Project "${name}" created`, "success");
    } catch (error) {
      setStatus(error.message, "error");
    }
  });

  ui.deleteProject.addEventListener("click", async () => {
    if (state.project === "root") {
      alert("The root workspace cannot be deleted.");
      return;
    }
    if (!confirm(`Delete project "${state.project}"? This cannot be undone.`)) {
      return;
    }
    try {
      await apiRequest(`/api/projects/${encodeURIComponent(state.project)}`, {
        method: "DELETE",
      });
      await refreshProjects("root");
      await loadTree();
      clearEditor();
      await loadAssistantHistory();
      setStatus("Project deleted", "success");
    } catch (error) {
      setStatus(error.message, "error");
    }
  });

  ui.sidebarActions.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) {
      return;
    }
    try {
      const action = button.dataset.action;
      if (action === "new-file") {
        await createEntry("file");
      } else if (action === "new-folder") {
        await createEntry("dir");
      } else if (action === "rename") {
        await renameEntry();
      } else if (action === "delete") {
        await deleteEntry();
      }
    } catch (error) {
      setStatus(error.message, "error");
    }
  });

  ui.fileTree.addEventListener("click", async (event) => {
    const target = event.target.closest("li[data-path]");
    if (!target) {
      return;
    }
    event.stopPropagation();
    const path = target.dataset.path;
    const type = target.dataset.type;
    selectTreeItem(path, type);
    if (type === "dir") {
      target.classList.toggle("collapsed");
    } else if (type === "file") {
      if (!(await confirmDiscard())) {
        return;
      }
      await openFile(path);
    }
  });

  ui.editor.addEventListener("input", () => {
    if (!state.currentPath) {
      return;
    }
    state.dirty = ui.editor.value !== state.originalContent;
    updateEditorState();
  });

  ui.saveBtn.addEventListener("click", async () => {
    await saveFile();
  });

  ui.runBtn.addEventListener("click", async () => {
    await runFile();
  });

  ui.assistantForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (assistantState.loading) {
      return;
    }
    const prompt = ui.assistantInput.value.trim();
    if (!prompt) {
      return;
    }
    appendAssistantMessage("user", prompt);
    ui.assistantInput.value = "";
    await askAssistant(prompt);
  });

  ui.assistantClear.addEventListener("click", async () => {
    try {
      await apiRequest("/api/assistant/history/clear", {
        method: "POST",
        body: JSON.stringify({ project: state.project }),
      });
      assistantState.messages = [];
      renderAssistantLog();
      setStatus("Assistant history cleared", "success");
    } catch (error) {
      setStatus(error.message, "error");
    }
  });

  if (ui.agentForm) {
    ui.agentForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await startAgentJob();
    });
  }

  if (ui.agentStop) {
    ui.agentStop.addEventListener("click", async () => {
      await stopAgentJob();
    });
  }

  window.addEventListener("beforeunload", (event) => {
    if (state.dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
}

async function refreshProjects(preferred) {
  try {
    const data = await apiRequest("/api/projects");
    const projects = data.projects || [];
    ui.projectSelect.innerHTML = projects
      .map((name) => `<option value="${escapeAttr(name)}">${escapeHtml(name)}</option>`)
      .join("");
    if (preferred && projects.includes(preferred)) {
      state.project = preferred;
    } else if (!projects.includes(state.project)) {
      state.project = projects[0] || "root";
    }
    ui.projectSelect.value = state.project;
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function loadTree() {
  try {
    const data = await apiRequest(`/api/tree?project=${encodeURIComponent(state.project)}`);
    const nodes = data.nodes || [];
    ui.fileTree.innerHTML = buildTree(nodes);
    highlightSelected();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function buildTree(nodes) {
  if (!nodes.length) {
    return "<p class=\"empty\">Project is empty</p>";
  }
  return `<ul>${nodes.map(renderNode).join("")}</ul>`;
}

function renderNode(node) {
  const hasChildren = Array.isArray(node.children) && node.children.length > 0;
  const active = state.selectedPath === node.path ? " active" : "";
  const collapsed = node.type === "dir" && hasChildren ? " collapsed" : "";
  return `
    <li class="${active}${collapsed}" data-path="${escapeAttr(node.path)}" data-type="${node.type}">
      ${escapeHtml(node.name)}
      ${hasChildren ? `<ul>${node.children.map(renderNode).join("")}</ul>` : ""}
    </li>
  `;
}

async function openFile(path) {
  try {
    const data = await apiRequest(
      `/api/file?project=${encodeURIComponent(state.project)}&path=${encodeURIComponent(path)}`
    );
    state.currentPath = path;
    state.selectedPath = path;
    state.selectedType = "file";
    state.originalContent = data.content || "";
    state.dirty = false;
    ui.editor.value = state.originalContent;
    highlightSelected();
    updateEditorState();
    setStatus(`Opened ${path}`);
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function selectTreeItem(path, type) {
  state.selectedPath = path;
  state.selectedType = type;
  highlightSelected();
}

function highlightSelected() {
  ui.fileTree.querySelectorAll("li").forEach((li) => {
    if (li.dataset.path === state.selectedPath) {
      li.classList.add("active");
    } else {
      li.classList.remove("active");
    }
  });
}

function clearEditor() {
  state.currentPath = null;
  state.selectedType = null;
  state.selectedPath = null;
  state.originalContent = "";
  state.dirty = false;
  ui.editor.value = "";
  updateEditorState();
}

function updateEditorState() {
  if (state.currentPath) {
    ui.currentPath.textContent = `${state.project}/${state.currentPath}`;
  } else {
    ui.currentPath.textContent = "Select a file…";
  }
  ui.saveBtn.disabled = !state.currentPath;
  ui.runBtn.disabled = !state.currentPath;
  const includeToggle = ui.assistantIncludeFile;
  if (includeToggle) {
    includeToggle.disabled = !state.currentPath;
    if (!state.currentPath) {
      includeToggle.checked = false;
    }
  }
  if (state.dirty) {
    ui.status.textContent = "Unsaved changes";
    ui.status.className = "status warning";
  }
}

async function saveFile() {
  if (!state.currentPath) {
    const name = prompt("Save as (relative path)", state.selectedPath || "");
    if (!name) {
      return;
    }
    state.currentPath = name.trim();
  }
  try {
    await apiRequest("/api/save", {
      method: "POST",
      body: JSON.stringify({
        project: state.project,
        path: state.currentPath,
        content: ui.editor.value,
      }),
    });
    state.originalContent = ui.editor.value;
    state.dirty = false;
    await loadTree();
    selectTreeItem(state.currentPath, "file");
    updateEditorState();
    setStatus("Saved", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function runFile() {
  if (!state.currentPath) {
    alert("Select a file to run.");
    return;
  }
  await saveFileIfDirty();
  try {
    setStatus("Running…");
    const data = await apiRequest("/api/run", {
      method: "POST",
      body: JSON.stringify({
        project: state.project,
        path: state.currentPath,
      }),
    });
    const output = [];
    if (data.stdout) {
      output.push(data.stdout);
    }
    if (data.stderr) {
      output.push(`stderr:\n${data.stderr}`);
    }
    if (data.timed_out) {
      output.push("\n⏱️ Execution timed out");
    }
    ui.output.textContent = output.join("\n").trim() || "(no output)";
    setStatus("Run finished", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function saveFileIfDirty() {
  if (state.dirty) {
    await saveFile();
  }
}

async function createEntry(type) {
  const defaultPrefix =
    type === "file"
      ? suggestChildPath(".py")
      : suggestChildPath("");
  const promptLabel = type === "file" ? "New file path" : "New folder path";
  const name = prompt(promptLabel, defaultPrefix);
  if (!name) {
    return;
  }
  await apiRequest("/api/new", {
    method: "POST",
    body: JSON.stringify({
      project: state.project,
      path: name.trim(),
      type,
    }),
  });
  await loadTree();
  selectTreeItem(name.trim(), type === "dir" ? "dir" : "file");
  if (type === "file") {
    await openFile(name.trim());
  }
  setStatus(`${type === "dir" ? "Folder" : "File"} created`, "success");
}

async function renameEntry() {
  if (!state.selectedPath) {
    alert("Select a file or folder to rename.");
    return;
  }
  const newName = prompt("Rename to", state.selectedPath);
  if (!newName || newName === state.selectedPath) {
    return;
  }
  await apiRequest("/api/rename", {
    method: "POST",
    body: JSON.stringify({
      project: state.project,
      path: state.selectedPath,
      new_path: newName.trim(),
    }),
  });
  if (state.currentPath === state.selectedPath) {
    state.currentPath = newName.trim();
  }
  state.selectedPath = newName.trim();
  await loadTree();
  highlightSelected();
  updateEditorState();
  setStatus("Renamed", "success");
}

async function deleteEntry() {
  if (!state.selectedPath) {
    alert("Select a file or folder to delete.");
    return;
  }
  const recursive = state.selectedType === "dir";
  const confirmed = confirm(
    `Delete ${state.selectedType} "${state.selectedPath}"? ${
      recursive ? "All children will be removed." : ""
    }`
  );
  if (!confirmed) {
    return;
  }
  await apiRequest("/api/delete", {
    method: "POST",
    body: JSON.stringify({
      project: state.project,
      path: state.selectedPath,
      recursive,
    }),
  });
  if (state.currentPath === state.selectedPath) {
    clearEditor();
  }
  state.selectedPath = null;
  await loadTree();
  setStatus("Deleted", "success");
}

function suggestChildPath(suffix) {
  if (state.selectedPath && state.selectedType === "dir") {
    return `${state.selectedPath}/new${suffix}`;
  }
  return `new${suffix}`;
}

async function loadAssistantHistory() {
  try {
    const data = await apiRequest(
      `/api/assistant/history?project=${encodeURIComponent(state.project)}`
    );
    assistantState.messages = Array.isArray(data.messages) ? data.messages : [];
  } catch (error) {
    assistantState.messages = [];
    setStatus(error.message, "error");
  }
  renderAssistantLog();
}

async function askAssistant(prompt) {
  setAssistantLoading(true);
  try {
    setStatus("Contacting assistant…");
    const body = {
      prompt,
      project: state.project,
    };
    if (
      ui.assistantIncludeFile &&
      ui.assistantIncludeFile.checked &&
      state.currentPath
    ) {
      body.files = [
        {
          path: state.currentPath,
          content: ui.editor.value,
        },
      ];
    }
    const data = await apiRequest("/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (Array.isArray(data.messages)) {
      assistantState.messages = data.messages;
      renderAssistantLog();
    } else if (data.message) {
      appendAssistantMessage("assistant", data.message);
    }
    setStatus("Assistant reply received", "success");
  } catch (error) {
    appendAssistantMessage("assistant", `Error: ${error.message}`);
    setStatus(error.message, "error");
  } finally {
    setAssistantLoading(false);
  }
}

function appendAssistantMessage(role, text) {
  assistantState.messages.push({ role, text });
  renderAssistantLog();
}

function renderAssistantLog() {
  if (!ui.assistantLog) {
    return;
  }
  if (!assistantState.messages.length) {
    ui.assistantLog.innerHTML = '<p class="empty">No messages yet.</p>';
    return;
  }
  const entries = assistantState.messages
    .map(
      (msg) => `
        <div class="assistant-message ${msg.role}">
          <span class="role">${escapeHtml(msg.role)}</span>
          <div class="content">${formatAssistantContent(msg.text)}</div>
        </div>
      `
    )
    .join("");
  ui.assistantLog.innerHTML = entries;
  ui.assistantLog.scrollTop = ui.assistantLog.scrollHeight;
}

function formatAssistantContent(text) {
  return escapeHtml(text).replace(/\n/g, "<br />");
}

function setAssistantLoading(loading) {
  assistantState.loading = loading;
  if (ui.assistantSubmit) {
    ui.assistantSubmit.disabled = loading;
    ui.assistantSubmit.textContent = loading ? "Sending…" : "Send";
  }
  if (ui.assistantInput) {
    ui.assistantInput.disabled = loading;
  }
}

const AGENT_STATUS_LABELS = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  canceled: 'Canceled',
  idle: 'Idle',
};

async function startAgentJob() {
  if (!ui.agentGoal) {
    return;
  }
  const goal = ui.agentGoal.value.trim();
  if (!goal) {
    alert('Add a goal for the agent first.');
    return;
  }
  if (agentState.status === 'running') {
    if (!confirm('An agent run is in progress. Start a new one anyway?')) {
      return;
    }
  }
  const reflections = clampNumber(parseInt(ui.agentReflections?.value ?? '0', 10), 0, 5, 1);
  const timeout = clampNumber(parseInt(ui.agentTimeout?.value ?? '10', 10), 1, 120, 10);
  const payload = {
    goal,
    project: state.project,
    test_command: (ui.agentTestCommand?.value || '').trim() || null,
    max_reflections: reflections,
    timeout_minutes: timeout,
    model: (ui.agentModel?.value || '').trim() || null,
  };
  try {
    setAgentStatusBadge('Starting…', 'running');
    setStatus('Starting agent job…');
    setAgentControls(true);
    clearAgentPoll();
    agentState.events = [];
    agentState.cursor = 0;
    agentState.jobId = null;
    const data = await apiRequest('/api/agent3/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    agentState.jobId = data.job?.id || null;
    agentState.events = Array.isArray(data.events) ? data.events : [];
    agentState.cursor = agentState.events.length ? agentState.events[agentState.events.length - 1].seq : 0;
    agentState.status = 'running';
    renderAgentLog();
    applyAgentJobStatus(data.job);
    scheduleAgentPoll();
    setStatus('Agent job started', 'success');
  } catch (error) {
    setStatus(error.message, 'error');
    setAgentStatusBadge('Error', 'failed');
    agentState.status = 'failed';
    setAgentControls(false);
  }
}

async function stopAgentJob() {
  if (!agentState.jobId) {
    return;
  }
  try {
    await apiRequest('/api/agent3/stop', {
      method: 'POST',
      body: JSON.stringify({ job_id: agentState.jobId }),
    });
    setStatus('Agent cancellation requested', 'info');
    setAgentStatusBadge('Canceling…', 'running');
  } catch (error) {
    setStatus(error.message, 'error');
  }
}

async function fetchAgentStatus() {
  if (!agentState.jobId) {
    return;
  }
  const params = new URLSearchParams({ job_id: agentState.jobId });
  if (agentState.cursor) {
    params.set('cursor', String(agentState.cursor));
  }
  try {
    const data = await apiRequest(/api/agent3/status?);
    const events = Array.isArray(data.events) ? data.events : [];
    if (events.length) {
      mergeAgentEvents(events);
      agentState.cursor = data.next_cursor ?? agentState.cursor;
      renderAgentLog();
    }
    applyAgentJobStatus(data.job);
    if (agentState.status === 'running') {
      scheduleAgentPoll();
    }
  } catch (error) {
    setStatus(error.message, 'error');
    scheduleAgentPoll(2000);
  }
}

function applyAgentJobStatus(job) {
  if (!job) {
    setAgentStatusBadge('Unknown', 'failed');
    agentState.status = 'failed';
    setAgentControls(false);
    return;
  }
  const status = job.status || 'pending';
  agentState.status = status;
  const label = AGENT_STATUS_LABELS[status] || status;
  setAgentStatusBadge(label, status);
  const terminal = status === 'completed' || status === 'failed' || status === 'canceled';
  const controlsRunning = !terminal && (status === 'running' || status === 'pending');
  setAgentControls(controlsRunning);
  if (terminal) {
    clearAgentPoll();
  }
}

function setAgentControls(running) {
  if (ui.agentStart) {
    ui.agentStart.disabled = running;
  }
  if (ui.agentStop) {
    ui.agentStop.disabled = !running;
  }
}

function updateAgentControls() {
  const running = agentState.status === 'running' || agentState.status === 'pending';
  setAgentControls(running);
}

function scheduleAgentPoll(delay = 1000) {
  clearAgentPoll();
  agentState.polling = setTimeout(fetchAgentStatus, delay);
}

function clearAgentPoll() {
  if (agentState.polling) {
    clearTimeout(agentState.polling);
    agentState.polling = null;
  }
}

function renderAgentLog() {
  if (!ui.agentLog) {
    return;
  }
  if (!agentState.events.length) {
    ui.agentLog.innerHTML = '<p class="empty">No events yet.</p>';
    return;
  }
  const entries = agentState.events.map(formatAgentEvent).join('');
  ui.agentLog.innerHTML = entries;
  ui.agentLog.scrollTop = ui.agentLog.scrollHeight;
}

function formatAgentEvent(event) {
  const type = (event.type || 'info').toLowerCase();
  const metaParts = [#, type];
  if (event.created_at) {
    metaParts.push(event.created_at);
  }
  const details = event.data && Object.keys(event.data).length
    ? <pre></pre>
    : '';
  return 
    <div class="agent-event ">
      <span class="meta"></span>
      <div class="content"></div>
    </div>
  ;
}

function mergeAgentEvents(events) {
  for (const event of events) {
    const exists = agentState.events.some((existing) => existing.seq === event.seq);
    if (!exists) {
      agentState.events.push(event);
    }
  }
  agentState.events.sort((a, b) => a.seq - b.seq);
}

function setAgentStatusBadge(label, stateKey) {
  if (!ui.agentStatus) {
    return;
  }
  ui.agentStatus.textContent = label;
  const base = 'agent-status';
  ui.agentStatus.className = ${base} agent-;
}

function clampNumber(value, min, max, fallback) {
  if (Number.isNaN(value)) {
    return fallback;
  }
  return Math.min(Math.max(value, min), max);
}
async function confirmDiscard() {
  if (!state.dirty) {
    return true;
  }
  return confirm("Discard unsaved changes?");
}

function setStatus(message, kind = "info") {
  if (!ui.status) {
    return;
  }
  ui.status.textContent = message;
  ui.status.className = `status ${kind}`;
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  let data = {};
  try {
    data = await response.json();
  } catch (error) {
    // Ignore JSON parse errors for empty responses
  }
  if (!response.ok || data.ok === false) {
    const message = data.error || response.statusText;
    throw new Error(message || "Request failed");
  }
  return data;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}









