// Paste your Firebase web app config here (Firebase console -> Project settings -> Your apps).
// While apiKey starts with "YOUR_", the app runs in demo mode (local login + browser storage).
export const firebaseConfig = {
  apiKey: "AIzaSyDYZiCJw55oYAK8ATv_B8EXcLD3bD6Y0cQ",
  authDomain: "agentflow-faq-assistant.firebaseapp.com",
  projectId: "agentflow-faq-assistant",
  appId: "1:799319398210:web:6b54a31d49e6be9d8bdadb",
};
export const firebaseEnabled = !firebaseConfig.apiKey.startsWith("YOUR_");
export const API_BASE = "/api";
