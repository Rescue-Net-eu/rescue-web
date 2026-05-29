"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Status = "checking" | "online" | "offline";

export function ApiStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/healthz`)
      .then((res) => {
        if (!res.ok) throw new Error("unhealthy");
        return res.json();
      })
      .then(() => !cancelled && setStatus("online"))
      .catch(() => !cancelled && setStatus("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  const colors: Record<Status, string> = {
    checking: "#888",
    online: "#1b7f3b",
    offline: "#b00020",
  };
  const labels: Record<Status, string> = {
    checking: "Checking backend status…",
    online: "Backend API: online",
    offline: "Backend API: unreachable",
  };

  return (
    <p style={{ fontWeight: 600, color: colors[status] }}>{labels[status]}</p>
  );
}
