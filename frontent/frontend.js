// ─── Constants & State ───────────────────────────────────────────────────────
const BASE_URL = "http://localhost:8000";

const BOTS = {
    bot1: { name: "Travel Agent",    icon: "✈️",  endpoint: "/chat/bot1" },
    bot2: { name: "Expense Tracker", icon: "💰",  endpoint: "/chat/bot2" },
    bot3: { name: "Info RAG",        icon: "📚",  endpoint: "/chat/bot3" },
    bot4: { name: "Multi Bot",       icon: "🤖",  endpoint: "/chat/bot4" },
};

let authHeader   = "";
let currentUserId = "";
let currentBot   = "bot1";

// Per-bot state — completely isolated
const botState = {
    bot1: { thread: null, streaming: false },
    bot2: { thread: null, streaming: false },
    bot3: { thread: null, streaming: false },
    bot4: { thread: null, streaming: false },
};

// ─── View helpers ─────────────────────────────────────────────────────────────
const views = {
    landing: document.getElementById("landing-view"),
    auth:    document.getElementById("auth-view"),
    app:     document.getElementById("app-view"),
};

function showView(id) {
    Object.values(views).forEach(v => { v.classList.remove("active"); v.classList.add("hidden"); });
    views[id].classList.remove("hidden");
    views[id].classList.add("active");
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
function showAuth(mode) {
    const login = mode === "login";
    document.getElementById("auth-title").innerText  = login ? "Login" : "Sign Up";
    document.getElementById("auth-sub").innerText    = login ? "Welcome back! Enter your credentials." : "Create a new account.";
    document.getElementById("auth-submit").innerText = login ? "Login" : "Sign Up";
    document.getElementById("auth-error").classList.add("hidden");
    window._authMode = mode;
    showView("auth");
}

function backToLanding() { showView("landing"); }

async function handleAuth(e) {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const errEl    = document.getElementById("auth-error");
    const btn      = document.getElementById("auth-submit");
    const mode     = window._authMode || "login";

    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.innerText = "Please wait…";

    try {
        if (mode === "signup") {
            const res  = await fetch(`${BASE_URL}/auth/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();
            if (res.ok) {
                showAlert(errEl, "Signup successful! Please login.", "ok");
                window._authMode = "login";
                document.getElementById("auth-title").innerText  = "Login";
                document.getElementById("auth-sub").innerText    = "Welcome back!";
                document.getElementById("auth-submit").innerText = "Login";
                document.getElementById("password").value = "";
            } else {
                showAlert(errEl, data.detail || "Signup failed.", "err");
            }
        } else {
            authHeader = "Basic " + btoa(username + ":" + password);
            const res  = await fetch(`${BASE_URL}/auth/login`, {
                method: "GET",
                headers: { Authorization: authHeader },
            });
            if (!res.ok) { authHeader = ""; showAlert(errEl, "Wrong username or password.", "err"); return; }
            
            const data = await res.json();
            currentUserId = data.username || username;
            
            // This line crashed previously because the old JS looked for "user-badge".
            document.getElementById("user-chip").innerText = currentUserId;
            
            showView("app");
            loadAllBotChats();   // pre-load all bots in background
        }
    } catch (error) {
        console.error("Auth exception:", error);
        showAlert(errEl, "System error: " + error.message, "err");
    } finally {
        btn.disabled = false;
        btn.innerText = (window._authMode === "login") ? "Login" : "Sign Up";
    }
}

function showAlert(el, msg, type) {
    el.innerText  = msg;
    el.className  = "alert " + (type === "ok" ? "alert-ok" : "alert-err");
    el.classList.remove("hidden");
}

function logout() {
    authHeader = "";
    currentUserId = "";
    Object.keys(botState).forEach(b => { botState[b].thread = null; botState[b].streaming = false; });
    document.getElementById("username").value = "";
    document.getElementById("password").value = "";
    // Reset all pages
    ["bot1","bot2","bot3","bot4"].forEach(b => {
        document.getElementById(`msgs-${b}`).innerHTML = emptyHTML(b);
        document.getElementById(`list-${b}`).innerHTML = "";
        setInput(b, false);
    });
    showView("landing");
}

// ─── Bot switching ────────────────────────────────────────────────────────────
function switchBot(botId) {
    if (currentBot === botId) return;
    currentBot = botId;

    // Tabs
    document.querySelectorAll(".bot-tab").forEach(t => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
    });
    const tab = document.getElementById("tab-" + botId);
    if(tab) {
        tab.classList.add("active");
        tab.setAttribute("aria-selected", "true");
    }

    // Pages — show only the selected one
    document.querySelectorAll(".bot-page").forEach(p => p.classList.remove("active"));
    const page = document.getElementById("page-" + botId);
    if(page) page.classList.add("active");
}

// ─── Load chat history ────────────────────────────────────────────────────────
function loadAllBotChats() {
    ["bot1","bot2","bot3","bot4"].forEach(b => loadChats(b));
}

async function loadChats(botId) {
    const list = document.getElementById(`list-${botId}`);
    list.innerHTML = `<div class="list-loading"><span></span><span></span><span></span></div>`;
    try {
        const res = await fetch(`${BASE_URL}/get_chats?bot_id=${botId}`, {
            headers: { Authorization: authHeader },
        });
        list.innerHTML = "";
        if (!res.ok) return;
        const chats = await res.json();
        if (!chats.length) {
            list.innerHTML = `<div class="list-empty">No chats yet.</div>`;
            return;
        }
        // Ordered newest-first from backend
        chats.forEach(chat => addChatItem(botId, chat, false));
    } catch {
        list.innerHTML = `<div class="list-empty">Failed to load.</div>`;
    }
}

function addChatItem(botId, chat, prepend = true) {
    const list  = document.getElementById(`list-${botId}`);
    const empty = list.querySelector(".list-empty");
    if (empty) empty.remove();

    const div        = document.createElement("div");
    div.className    = "chat-item";
    div.id           = `ci-${chat.thread_id.replace(/[^a-zA-Z0-9]/g, "_")}`;
    div.dataset.tid  = chat.thread_id;

    div.innerHTML = `<span class="ci-icon">💬</span><span class="ci-title">${escHtml(chat.title || "New Chat")}</span>`;

    if (chat.thread_id === botState[botId].thread) div.classList.add("active");

    div.addEventListener("click", () => selectChat(botId, chat.thread_id));

    if (prepend) list.prepend(div);
    else list.appendChild(div);
}

function escHtml(s) {
    const d = document.createElement("div");
    d.innerText = s;
    return d.innerHTML;
}

// ─── Select a chat ────────────────────────────────────────────────────────────
function selectChat(botId, threadId) {
    botState[botId].thread = threadId;

    // Highlight
    document.querySelectorAll(`#list-${botId} .chat-item`).forEach(el => el.classList.remove("active"));
    const item = document.querySelector(`#list-${botId} [data-tid="${CSS.escape(threadId)}"]`);
    if (item) item.classList.add("active");

    // Enable input
    setInput(botId, true);

    // Clear messages for the selected chat (history could be fetched here)
    const msgs = document.getElementById(`msgs-${botId}`);
    msgs.innerHTML = "";
}

// ─── Create new chat ──────────────────────────────────────────────────────────
async function createNewChat(botId) {
    const btn = document.querySelector(`#page-${botId} .new-chat-btn`);
    btn.disabled = true;
    try {
        const res = await fetch(`${BASE_URL}/create_chat?bot_id=${botId}`, {
            method: "POST",
            headers: { Authorization: authHeader },
        });
        if (!res.ok) { console.error("create_chat failed"); return; }
        const data = await res.json();

        // Set as selected thread
        botState[botId].thread = data.thread_id;

        // Add to top of list
        addChatItem(botId, { thread_id: data.thread_id, title: data.title }, true);

        // Deselect all others, select new
        document.querySelectorAll(`#list-${botId} .chat-item`).forEach(el => el.classList.remove("active"));
        const newEl = document.getElementById(`ci-${data.thread_id.replace(/[^a-zA-Z0-9]/g, "_")}`);
        if (newEl) newEl.classList.add("active");

        // Clear messages
        document.getElementById(`msgs-${botId}`).innerHTML = "";
        setInput(botId, true);
    } catch (err) {
        console.error("createNewChat error:", err);
    } finally {
        btn.disabled = false;
    }
}

// ─── Input helpers ────────────────────────────────────────────────────────────
function setInput(botId, enabled) {
    const input = document.getElementById(`input-${botId}`);
    const btn   = document.getElementById(`send-${botId}`);
    input.disabled = !enabled;
    btn.disabled   = !enabled;
    if (enabled) { input.focus(); }
}

function grow(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

function handleKey(e, botId) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(botId); }
}

function emptyHTML(botId) {
    const b = BOTS[botId];
    return `<div class="empty-state"><div class="e-icon">${b.icon}</div><h3>${b.name}</h3><p>Create a new chat or pick one from the sidebar.</p></div>`;
}

// ─── Send message + SSE stream ────────────────────────────────────────────────
async function sendMessage(botId) {
    const state  = botState[botId];
    if (state.streaming || !state.thread) return;

    const inputEl = document.getElementById(`input-${botId}`);
    const msg     = inputEl.value.trim();
    if (!msg) return;

    const msgs = document.getElementById(`msgs-${botId}`);

    // Clear empty state
    const es = msgs.querySelector(".empty-state");
    if (es) es.remove();

    // User bubble
    appendBubble(msgs, msg, "user", botId);
    inputEl.value = "";
    inputEl.style.height = "auto";
    msgs.scrollTop = msgs.scrollHeight;

    // Lock
    state.streaming = true;
    setInput(botId, false);

    // Typing
    const typingEl = document.getElementById(`typing-${botId}`);
    typingEl.classList.remove("hidden");
    msgs.scrollTop = msgs.scrollHeight;

    // Bot bubble (stream into it)
    const botBubble = createStreamBubble(msgs, botId);

    try {
        const res = await fetch(`${BASE_URL}${BOTS[botId].endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: authHeader },
            body: JSON.stringify({ text: msg, thread_id: state.thread, user_id: currentUserId }),
        });

        typingEl.classList.add("hidden");

        if (!res.ok) {
            botBubble.innerText = `Error ${res.status}: could not get a response.`;
            botBubble.classList.add("bubble-err");
            return;
        }

        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let   buffer  = "";
        let   hasContent = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const data = line.slice(6).trim();
                if (!data) continue;

                if (data === "[DONE]") { botBubble.classList.remove("streaming"); break; }
                if (data.startsWith("[ERROR]")) {
                    botBubble.innerText = "Server error: " + data.slice(7);
                    botBubble.classList.add("bubble-err");
                    break;
                }

                // Try JSON (bot4 format and updated bot1/2/3 format)
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.type === "token" && parsed.content) {
                        botBubble.classList.remove("streaming");
                        // Support both full string payloads (bot1/2/4) and delta payloads (bot3)
                        if (parsed.is_delta) {
                            botBubble.innerText += parsed.content;
                        } else {
                            botBubble.innerText = parsed.content;
                        }
                        hasContent = true;
                    } else if (parsed.type === "final" && parsed.content) {
                        botBubble.classList.remove("streaming");
                        botBubble.innerText = parsed.content;
                        hasContent = true;
                        break;
                    } else if (parsed.type === "tool_call" && parsed.tools) {
                        botBubble.classList.remove("streaming");
                        let toolText = "\n[Running tools: " + parsed.tools.map(t => t.name).join(", ") + "]\n";
                        if (!botBubble.innerText.includes(toolText)) {
                            botBubble.innerText += toolText;
                        }
                        hasContent = true;
                    } else if (parsed.type === "tool_result" && parsed.content) {
                        botBubble.classList.remove("streaming");
                        hasContent = true;
                    }
                } catch {
                    // Plain text fallback
                    botBubble.classList.remove("streaming");
                    botBubble.innerText += data;
                    hasContent = true;
                }
                msgs.scrollTop = msgs.scrollHeight;
            }
        }

        if (!hasContent) botBubble.innerText = "(No response)";
        botBubble.classList.remove("streaming");

    } catch (err) {
        typingEl.classList.add("hidden");
        botBubble.innerText = "Network error: " + err.message;
        botBubble.classList.add("bubble-err");
        botBubble.classList.remove("streaming");
    } finally {
        state.streaming = false;
        typingEl.classList.add("hidden");
        setInput(botId, true);
        msgs.scrollTop = msgs.scrollHeight;
    }
}

// ─── Bubble helpers ───────────────────────────────────────────────────────────
function appendBubble(container, text, role, botId) {
    const wrap       = document.createElement("div");
    wrap.className   = `bubble-wrap ${role}`;

    if (role === "bot") {
        const av = document.createElement("div");
        av.className = "avatar";
        av.innerText = BOTS[botId].icon;
        wrap.appendChild(av);
    }

    const bub      = document.createElement("div");
    bub.className  = `bubble ${role}`;
    bub.innerText  = text;
    wrap.appendChild(bub);
    container.appendChild(wrap);
    requestAnimationFrame(() => wrap.classList.add("visible"));
    return bub;
}

function createStreamBubble(container, botId) {
    const wrap     = document.createElement("div");
    wrap.className = "bubble-wrap bot";

    const av = document.createElement("div");
    av.className = "avatar";
    av.innerText = BOTS[botId].icon;

    const bub      = document.createElement("div");
    bub.className  = "bubble bot streaming";

    wrap.appendChild(av);
    wrap.appendChild(bub);
    container.appendChild(wrap);
    requestAnimationFrame(() => wrap.classList.add("visible"));
    return bub;
}