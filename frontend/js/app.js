import { watchUser, logout } from "./auth.js";
import { saveChat, listChats, setFeedback } from "./store.js";
import { sendQuestion } from "./chat.js";
import { faqs } from "./api.js";
import { toggleTheme } from "./theme.js";

const $ = (s) => document.querySelector(s);
const CATS = { orders: "How can I track my order?", payments: "Which payment methods do you accept?",
  delivery: "How long does delivery take?", returns: "What is your return policy?", refunds: "How long does a refund take?" };
const TITLES = { analytics: ["Analytics", "How the assistant is performing, based on your real conversations."], desk: ["Support desk", "Every answer is grounded in your FAQ knowledge base."],
  kb: ["Knowledge base", "The FAQ entries the agents are allowed to answer from."],
  history: ["Chat history", "Your previous questions and the answers given."] };

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

let user, chats = [], kb = null, kbCat = "all";

/* ---------- dashboard numbers: all computed from the real chat history ---------- */
function renderStats() {
  const today = chats.filter((c) => new Date(c.ts).toDateString() === new Date().toDateString());
  const answered = chats.filter((c) => c.status === "answered").length;
  const human = chats.length - answered;
  const avgMs = chats.length ? chats.reduce((s, c) => s + (c.ms || 0), 0) / chats.length : 0;
  const avg = !chats.length ? "–" : avgMs < 1000 ? `${Math.max(1, Math.round(avgMs))} ms` : (avgMs / 1000).toFixed(1) + " s";
  const cards = [
    ["Questions today", today.length, `${chats.length} in total`, "#4338CA"],
    ["Answered from FAQ", chats.length ? Math.round((answered / chats.length) * 100) + "%" : "–", `${answered} answered`, "#1B7A4B"],
    ["Handed to humans", human, chats.length ? `${Math.round((human / chats.length) * 100)}% of questions` : "No questions yet", "#F2674A"],
    ["Avg. reply time", avg, "Agent processing time", "#6D4CE0"],
  ];
  $("#stats").replaceChildren(...cards.map(([k, n, s, color]) => {
    const c = el("div", "card stat");
    c.style.borderTopColor = color;
    c.append(el("div", "k", k), el("div", "n", String(n)), el("small", null, s));
    return c;
  }));

  const counts = Object.fromEntries(Object.keys(CATS).map((k) => [k, chats.filter((c) => c.category === k).length]));
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  $("#cats").replaceChildren(...(total ? Object.entries(counts).sort((a, b) => b[1] - a[1]).flatMap(([k, n]) => {
    const row = el("div", "row"), bar = el("div", "bar"), fill = el("i");
    row.append(el("span", null, cap(k)), el("span", null, Math.round((n / total) * 100) + "%"));
    fill.style.width = (n / total) * 100 + "%";
    bar.append(fill);
    return [row, bar];
  }) : [el("div", "empty", "Categories will appear after the first question.")]));

  renderAnalytics(counts, total);
  const open = chats.filter((c) => c.status !== "answered").slice(0, 4);
  $("#human").replaceChildren(...(open.length ? open.map((c) => el("li", null, c.question))
    : [el("li", null, "No unanswered questions yet.")]));
}

function renderAnalytics(counts, total) {
  const days = [...Array(7)].map((_, i) => { const d = new Date(); d.setDate(d.getDate() - (6 - i)); return d; });
  const perDay = days.map((d) => chats.filter((c) => new Date(c.ts).toDateString() === d.toDateString()).length);
  const max = Math.max(1, ...perDay);
  $("#volume").replaceChildren(...days.map((d, i) => {
    const col = el("div", "v"), bar = el("i");
    bar.style.height = (perDay[i] / max) * 78 + "%";
    col.append(el("span", null, String(perDay[i])), bar, el("span", null, d.toLocaleDateString(undefined, { weekday: "short" })));
    return col;
  }));

  const answered = chats.filter((c) => c.status === "answered").length, human = chats.length - answered;
  const stat = (n, label, color) => { const d = el("div"); const b = el("b", null, String(n)); b.style.color = color; d.append(b, el("span", null, label)); return d; };
  if (!chats.length) $("#resolution").replaceChildren(el("div", "empty", "No questions yet."));
  else {
    const bar = el("div", "split2"), a = el("i"), h = el("i");
    a.style.cssText = `width:${(answered / chats.length) * 100}%;background:var(--ok)`;
    h.style.cssText = `width:${(human / chats.length) * 100}%;background:var(--warn)`;
    bar.append(a, h);
    const legend = el("div", "legend");
    legend.append(stat(answered, "Answered from FAQ", "var(--ok)"), stat(human, "Sent to a human", "var(--warn)"));
    $("#resolution").replaceChildren(bar, legend);
  }

  const up = chats.filter((c) => c.feedback === "up").length, down = chats.filter((c) => c.feedback === "down").length;
  if (!up && !down) $("#feedback").replaceChildren(el("div", "empty", "No feedback yet. Use Helpful / Not helpful under an answer."));
  else {
    const legend = el("div", "legend");
    legend.append(stat(up, "Helpful", "var(--ok)"), stat(down, "Not helpful", "var(--warn)"),
      stat(Math.round((up / (up + down)) * 100) + "%", "Satisfaction", "var(--brand)"));
    $("#feedback").replaceChildren(legend);
  }

  $("#cats2").replaceChildren(...(total ? Object.entries(counts).sort((a, b) => b[1] - a[1]).flatMap(([k, n]) => {
    const row = el("div", "row"), bar = el("div", "bar"), fill = el("i");
    row.append(el("span", null, cap(k)), el("span", null, `${n} (${Math.round((n / total) * 100)}%)`));
    fill.style.width = (n / total) * 100 + "%";
    bar.append(fill);
    return [row, bar];
  }) : [el("div", "empty", "No questions yet.")]));
}

function renderHistory() {
  const list = $("#historyList");
  if (!chats.length) return list.replaceChildren(el("div", "empty", "No conversations yet. Ask your first question on the Support desk."));
  list.replaceChildren(...chats.map((c) => {
    const d = el("details", "card"), s = el("summary", null, c.question);
    s.append(el("span", "tag", cap(c.category || "other")), el("span", `tag ${c.status === "answered" ? "ok" : "warn"}`,
      c.status === "answered" ? "Answered" : "Not in FAQ"), el("span", "tag", new Date(c.ts).toLocaleString()));
    d.append(s, el("p", null, c.answer));
    return d;
  }));
}

/* ---------- knowledge base ---------- */
function renderKb() {
  const term = $("#kbSearch").value.trim().toLowerCase();
  const rows = kb.filter((f) => (kbCat === "all" || f.category === kbCat) &&
    (!term || (f.question + " " + f.answer).toLowerCase().includes(term)));
  $("#kbList").replaceChildren(...(rows.length ? rows.map((f) => {
    const d = el("details", "card"), s = el("summary", null, f.question);
    s.append(el("span", "tag", cap(f.category)), el("span", "tag", f.id));
    d.append(s, el("p", null, f.answer));
    return d;
  }) : [el("div", "empty", "No FAQ entries match your search.")]));
}

async function openKb() {
  if (!kb) {
    try { kb = await faqs(); } catch (e) { return $("#kbList").replaceChildren(el("div", "empty", e.message)); }
    const chips = ["all", ...Object.keys(CATS)].map((c) => {
      const b = el("button", `chip${c === "all" ? " on" : ""}`, cap(c));
      b.type = "button";
      b.addEventListener("click", () => { kbCat = c; chips.forEach((x) => x.classList.toggle("on", x === b)); renderKb(); });
      return b;
    });
    $("#kbChips").replaceChildren(...chips);
  }
  renderKb();
}

/* ---------- chat ---------- */
async function submit(question) {
  const q = question.trim();
  if (!q) return;
  $("#empty")?.remove();
  $("#q").value = "";
  $("#send").disabled = true;
  const result = await sendQuestion(q, $("#msgs"), { onFeedback: (v) => { if (!rec?.id) return; rec.feedback = v; setFeedback(user, rec.id, v); renderStats(); renderHistory(); } });
  let rec;
  if (result) {
    rec = { ts: Date.now(), question: q, category: result.category, status: result.status, answer: result.answer,
      sources: result.sources.map((s) => s.id), ms: result.trace.reduce((s, t) => s + t.duration_ms, 0), feedback: null };
    rec.id = await saveChat(user, rec);
    chats.unshift(rec);
    renderStats();
    renderHistory();
  }
  $("#send").disabled = false;
  $("#q").focus();
}

function setView(view) {
  document.querySelectorAll("[data-view]").forEach((b) => b.classList.toggle("on", b.dataset.view === view));
  ["desk", "analytics", "kb", "history"].forEach((v) => ($(`#view-${v}`).hidden = v !== view));
  [$("#viewTitle").textContent, $("#viewSub").textContent] = TITLES[view];
  if (view === "kb") openKb();
}

function setupVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  const mic = $("#mic"), rec = new SR();
  rec.lang = "en-US";
  mic.hidden = false;
  rec.onresult = (e) => { $("#q").value = e.results[0][0].transcript; };
  rec.onend = () => { mic.textContent = "Mic"; };
  mic.addEventListener("click", () => { mic.textContent = "Listening…"; rec.start(); });
}

function init() {
  $("#avatar").textContent = (user.email || "U")[0];
  $("#avatar").title = user.email || "";
  $("#chips").replaceChildren(...Object.entries(CATS).map(([cat, q]) => {
    const b = el("button", "chip", cap(cat));
    b.type = "button";
    b.addEventListener("click", () => submit(q));
    return b;
  }));
  document.querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => setView(b.dataset.view)));
  $("#kbSearch").addEventListener("input", () => kb && renderKb());
  $("#askForm").addEventListener("submit", (e) => { e.preventDefault(); submit($("#q").value); });
  $("#logout").addEventListener("click", async () => { await logout(); location.replace("index.html"); });
  const themeBtn = $("#theme");
  themeBtn.addEventListener("click", () => { themeBtn.textContent = toggleTheme() === "dark" ? "Light mode" : "Dark mode"; });
  themeBtn.textContent = document.documentElement.dataset.theme === "dark" ? "Light mode" : "Dark mode";
  setupVoice();
}

let started = false;
watchUser(async (u) => {
  if (!u) return location.replace("index.html");
  if (started) return;
  started = true;
  user = u;
  init();
  try { chats = await listChats(user); } catch { chats = []; }
  renderStats();
  renderHistory();
});
