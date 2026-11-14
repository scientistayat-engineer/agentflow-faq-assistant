const KEY = "agentflow_theme";
const apply = (t) => document.documentElement.setAttribute("data-theme", t);
apply(localStorage.getItem(KEY) || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
export function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  localStorage.setItem(KEY, next);
  apply(next);
  return next;
}
