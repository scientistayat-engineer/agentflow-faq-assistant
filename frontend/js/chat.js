import { ask } from "./api.js";

const AGENTS = ["FAQ Classifier", "Knowledge Agent", "Response Agent"];
const MARK = { done: "✓", warn: "!", skipped: "–", running: "…", pending: "" };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function pipeline() {
  const box = el("div", "pipe");
  const steps = AGENTS.map((name) => {
    const s = el("div", "step pending");
    const dot = el("div", "dot", "");
    s.append(dot, el("b", null, name), el("span", null, "Waiting"));
    return s;
  });
  steps.forEach((s, i) => { box.append(s); if (i < steps.length - 1) box.append(el("div", "line")); });
  const set = (i, state, text) => {
    steps[i].className = `step ${state}`;
    steps[i].querySelector(".dot").textContent = MARK[state] ?? "";
    steps[i].querySelector("span").textContent = text;
  };
  return { box, set };
}

const stateFor = (status) => (status === "done" ? "done" : status === "skipped" ? "skipped" : "warn");

export async function sendQuestion(question, box, { onFeedback }) {
  box.append(el("div", "msg user", question));
  const pipe = pipeline();
  box.append(pipe.box);
  pipe.set(0, "running", "Working…");
  box.scrollTop = box.scrollHeight;

  let result;
  try {
    result = await ask(question);
  } catch (err) {
    AGENTS.forEach((_, i) => pipe.set(i, "warn", "Stopped"));
    box.append(el("div", "msg bot", err.message));
    return null;
  }

  for (let i = 0; i < result.trace.length; i++) {
    await sleep(200);
    const t = result.trace[i];
    pipe.set(i, stateFor(t.status), t.summary);
    if (i + 1 < AGENTS.length) pipe.set(i + 1, "running", "Working…");
  }

  const bubble = el("div", "msg bot", result.answer);
  const meta = el("div", "meta");
  const grounded = result.status === "answered";
  meta.append(el("span", `tag ${grounded ? "ok" : "warn"}`, grounded ? "Grounded in FAQ" : "Not in FAQ"));
  result.sources.forEach((s) => meta.append(el("span", "tag", `Source: FAQ ${s.id}`)));
  const fb = el("div", "fb");
  [["up", "Helpful"], ["down", "Not helpful"]].forEach(([value, label]) => {
    const b = el("button", null, label);
    b.type = "button";
    b.addEventListener("click", () => {
      fb.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
      onFeedback(value);
    });
    fb.append(b);
  });
  meta.append(fb);
  bubble.append(meta);
  box.append(bubble);
  box.scrollTop = box.scrollHeight;
  return result;
}
