import { firebaseConfig, firebaseEnabled } from "./config.js";

const CDN = "https://www.gstatic.com/firebasejs/10.12.2/";
let cached;

// Lazy-loads Firebase only when configured, so demo mode needs no network access to Google.
export async function fb() {
  if (!firebaseEnabled) return null;
  if (!cached) {
    const [app, auth, fs] = await Promise.all([
      import(CDN + "firebase-app.js"), import(CDN + "firebase-auth.js"), import(CDN + "firebase-firestore.js"),
    ]);
    const a = app.initializeApp(firebaseConfig);
    cached = { auth, fs, A: auth.getAuth(a), db: fs.getFirestore(a) };
  }
  return cached;
}
