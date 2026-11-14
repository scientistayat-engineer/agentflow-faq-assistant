import { firebaseEnabled } from "./config.js";
import { fb } from "./firebase.js";

const KEY = "agentflow_user";
export const demoMode = !firebaseEnabled;
const norm = (u) => (u ? { uid: u.uid, email: u.email } : null);
const demoLogin = (email) => localStorage.setItem(KEY, JSON.stringify({ uid: "demo", email: email || "demo@agentflow.app" }));

export async function signIn(email, password) {
  const f = await fb();
  return f ? f.auth.signInWithEmailAndPassword(f.A, email, password) : demoLogin(email);
}
export async function signUp(email, password) {
  const f = await fb();
  return f ? f.auth.createUserWithEmailAndPassword(f.A, email, password) : demoLogin(email);
}
export async function googleSignIn() {
  const f = await fb();
  return f ? f.auth.signInWithPopup(f.A, new f.auth.GoogleAuthProvider()) : demoLogin("demo@agentflow.app");
}
export async function logout() {
  const f = await fb();
  if (f) await f.auth.signOut(f.A);
  localStorage.removeItem(KEY);
}
export async function watchUser(cb) {
  const f = await fb();
  if (f) return f.auth.onAuthStateChanged(f.A, (u) => cb(norm(u)));
  cb(JSON.parse(localStorage.getItem(KEY) || "null"));
}

const MESSAGES = {
  "auth/invalid-credential": "Incorrect email or password.",
  "auth/user-not-found": "No account found with this email.",
  "auth/wrong-password": "Incorrect email or password.",
  "auth/email-already-in-use": "An account with this email already exists.",
  "auth/weak-password": "Password must be at least 6 characters.",
  "auth/invalid-email": "Please enter a valid email address.",
  "auth/popup-closed-by-user": "Google sign-in was cancelled.",
  "auth/too-many-requests": "Too many attempts. Please try again later.",
};
export const friendly = (err) => MESSAGES[err?.code] || "Something went wrong. Please try again.";
