"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "../lib/auth";
import { Login } from "./login";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/incidents", label: "Incidents" },
  { href: "/missions", label: "Missions" },
];

export function Shell({ children }: { children: ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();

  if (loading) {
    return (
      <main style={{ padding: "2rem", color: "var(--muted)" }}>Loading…</main>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          background: "#1a1d21",
          color: "#fff",
          padding: "0.7rem 1.25rem",
          display: "flex",
          alignItems: "center",
          gap: "1.5rem",
        }}
      >
        <strong style={{ fontSize: "1.05rem" }}>
          rescue-net<span style={{ color: "var(--brand)" }}>.eu</span>
        </strong>
        <nav style={{ display: "flex", gap: "1rem", flex: 1 }}>
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  color: active ? "#fff" : "#aab2bd",
                  fontWeight: active ? 700 : 500,
                  borderBottom: active ? "2px solid var(--brand)" : "2px solid transparent",
                  paddingBottom: 2,
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <span style={{ fontSize: "0.85rem", color: "#aab2bd" }}>
          {user.email} · {user.role}
        </span>
        <button className="btn secondary" onClick={logout} style={{ padding: "0.35rem 0.7rem" }}>
          Sign out
        </button>
      </header>
      <main
        style={{
          flex: 1,
          maxWidth: 1100,
          width: "100%",
          margin: "0 auto",
          padding: "1.5rem 1.25rem",
        }}
      >
        {children}
      </main>
    </div>
  );
}
