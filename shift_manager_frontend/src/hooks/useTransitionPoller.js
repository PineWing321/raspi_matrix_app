import { useEffect } from "react";

export function useTransitionPoller() {
  useEffect(() => {
    window.isReactActive = true;

    const host = window.location.hostname;
    const url = `http://${host}:5000/api/next_transition`;

    const interval = setInterval(async () => {
      try {
        console.log("Polling..."); // 🔍 Confirm it's firing
        const res = await fetch(url);
        const data = await res.json();

        if (data.next_path) {
          const nextPath = data.next_path.startsWith("/") ? data.next_path : "/" + data.next_path;
          console.log("Redirecting to:", nextPath);
          window.location.href = nextPath; // ✅ Works on iPad
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1500);

    return () => {
      window.isReactActive = false;
      clearInterval(interval);
    };
  }, []);
}
