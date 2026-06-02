"use client";

import type { ReactNode } from "react";

export function Badge({
  children,
  kind,
}: {
  children: ReactNode;
  kind?: string;
}) {
  return <span className={`badge ${kind ?? ""}`}>{children}</span>;
}

export function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof Error ? error.message : String(error);
  return <p className="error">{msg}</p>;
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return <p style={{ color: "var(--muted)" }}>{label}</p>;
}

export function PriorityBadge({ priority }: { priority: string }) {
  return <Badge kind={priority}>{priority}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge kind={status}>{status.replace(/_/g, " ")}</Badge>;
}
