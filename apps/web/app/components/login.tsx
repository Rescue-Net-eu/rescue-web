"use client";

import { useState } from "react";
import { useAuth } from "../lib/auth";
import { type Role } from "../lib/api";
import { ErrorText } from "./ui";

const ROLES: Role[] = ["dispatcher", "team_lead", "platform_admin", "responder"];

export function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("dispatcher@example.org");
  const [role, setRole] = useState<Role>("dispatcher");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, role);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "1.5rem",
      }}
    >
      <div className="panel" style={{ width: "100%", maxWidth: 380 }}>
        <h1 style={{ marginTop: 0 }}>
          rescue-net<span style={{ color: "var(--brand)" }}>.eu</span>
        </h1>
        <p style={{ color: "var(--muted)", marginTop: "-0.5rem" }}>
          Dispatcher console
        </p>
        <form onSubmit={submit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="role">Role</label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <ErrorText error={error} />
          <button className="btn" type="submit" disabled={busy} style={{ width: "100%" }}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="disclaimer" style={{ marginTop: "1rem" }}>
          Development sign-in. Production uses OIDC (Authentik) with MFA for
          dispatchers and admins.
        </p>
      </div>
    </main>
  );
}
