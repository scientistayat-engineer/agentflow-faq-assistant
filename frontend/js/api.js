import { API_BASE } from "./config.js";

async function call(path, options) {
  let res;
  try { res = await fetch(API_BASE + path, options); }
  catch { throw new Error("Cannot reach the assistant backend. Please check your connection."); }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "The assistant is temporarily unavailable.");
  return data;
}

export const ask = (question) =>
  call("/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
export const faqs = () => call("/faqs");
