import { firebaseEnabled } from "./config.js";
import { fb } from "./firebase.js";

// Chats live in Firestore (users/{uid}/chats) when Firebase is configured, else in localStorage.
const key = (u) => `agentflow_chats_${u.uid}`;
const local = (u) => JSON.parse(localStorage.getItem(key(u)) || "[]");

export async function saveChat(user, rec) {
  if (firebaseEnabled) {
    const f = await fb();
    return (await f.fs.addDoc(f.fs.collection(f.db, "users", user.uid, "chats"), rec)).id;
  }
  const all = local(user);
  rec.id = String(rec.ts);
  all.unshift(rec);
  localStorage.setItem(key(user), JSON.stringify(all.slice(0, 200)));
  return rec.id;
}

export async function listChats(user) {
  if (firebaseEnabled) {
    const f = await fb();
    const q = f.fs.query(f.fs.collection(f.db, "users", user.uid, "chats"), f.fs.orderBy("ts", "desc"), f.fs.limit(200));
    return (await f.fs.getDocs(q)).docs.map((d) => ({ ...d.data(), id: d.id }));
  }
  return local(user);
}

export async function setFeedback(user, id, value) {
  if (firebaseEnabled) {
    const f = await fb();
    return f.fs.updateDoc(f.fs.doc(f.db, "users", user.uid, "chats", id), { feedback: value });
  }
  localStorage.setItem(key(user), JSON.stringify(local(user).map((c) => (c.id === id ? { ...c, feedback: value } : c))));
}
