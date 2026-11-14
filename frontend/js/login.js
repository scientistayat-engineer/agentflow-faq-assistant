import { signIn, signUp, googleSignIn, watchUser, demoMode, friendly } from "./auth.js";

const $ = (s) => document.querySelector(s);
let mode = "signin";

watchUser((user) => { if (user) location.replace("app.html"); });
$("#demo").hidden = !demoMode;

const setError = (msg) => { $("#error").textContent = msg || ""; $("#error").hidden = !msg; };
const busy = (on) => { $("#submit").disabled = on; $("#google").disabled = on; };

document.querySelectorAll("[data-mode]").forEach((btn) => btn.addEventListener("click", () => {
  mode = btn.dataset.mode;
  document.querySelectorAll("[data-mode]").forEach((b) => b.classList.toggle("on", b === btn));
  const up = mode === "signup";
  $("#title").textContent = up ? "Create your account" : "Welcome back";
  $("#sub").textContent = up ? "Start answering customers in minutes." : "Sign in to the support desk.";
  $("#submit").textContent = up ? "Create account" : "Sign in";
  $("#password").autocomplete = up ? "new-password" : "current-password";
  setError("");
}));

$("#authForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = $("#email").value.trim(), password = $("#password").value;
  if (!email || !email.includes("@")) return setError("Please enter a valid email address.");
  if (password.length < 6) return setError("Password must be at least 6 characters.");
  setError(""); busy(true);
  try { await (mode === "signup" ? signUp : signIn)(email, password); location.replace("app.html"); }
  catch (err) { setError(friendly(err)); busy(false); }
});

$("#google").addEventListener("click", async () => {
  setError(""); busy(true);
  try { await googleSignIn(); location.replace("app.html"); }
  catch (err) { setError(friendly(err)); busy(false); }
});
