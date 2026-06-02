"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Incident } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ErrorText, Spinner, StatusBadge, PriorityBadge } from "../components/ui";

export default function IncidentsPage() {
  const { token } = useAuth();
  const [incidents, setIncidents] = useState<Incident[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (!token) return;
    api.listIncidents(token).then(setIncidents).catch(setError);
  }, [token]);

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h1 style={{ margin: 0 }}>Incidents</h1>
        <Link href="/incidents/new" className="btn">
          + New incident
        </Link>
      </div>

      <ErrorText error={error} />

      <section className="panel">
        {!incidents ? (
          <Spinner />
        ) : incidents.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No incidents yet. Create one to begin.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((i) => (
                <tr key={i.id}>
                  <td>
                    <Link href={`/incidents/${i.id}`}>{i.title}</Link>
                  </td>
                  <td>{i.type ?? "—"}</td>
                  <td>
                    <PriorityBadge priority={i.priority} />
                  </td>
                  <td>
                    <StatusBadge status={i.status} />
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {new Date(i.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
