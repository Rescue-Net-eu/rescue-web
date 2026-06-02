"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Incident, type Mission } from "./lib/api";
import { useAuth } from "./lib/auth";
import { ErrorText, Spinner, StatusBadge, PriorityBadge } from "./components/ui";

export default function OverviewPage() {
  const { token } = useAuth();
  const [incidents, setIncidents] = useState<Incident[] | null>(null);
  const [missions, setMissions] = useState<Mission[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (!token) return;
    Promise.all([api.listIncidents(token), api.listMissions(token)])
      .then(([inc, mis]) => {
        setIncidents(inc);
        setMissions(mis);
      })
      .catch(setError);
  }, [token]);

  const openIncidents = (incidents ?? []).filter(
    (i) => !["closed", "cancelled"].includes(i.status),
  );
  const activeMissions = (missions ?? []).filter(
    (m) => !["closed", "cancelled"].includes(m.status),
  );

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
        <h1 style={{ margin: 0 }}>Overview</h1>
        <Link href="/incidents/new" className="btn">
          + New incident
        </Link>
      </div>

      <p className="disclaimer" style={{ marginBottom: "1.25rem" }}>
        rescue-net.eu coordinates volunteer response. In life-threatening
        emergencies, contact the official emergency number (e.g. 112) first.
      </p>

      <ErrorText error={error} />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <Stat label="Open incidents" value={openIncidents.length} />
        <Stat label="Active missions" value={activeMissions.length} />
        <Stat label="Total incidents" value={incidents?.length ?? 0} />
      </div>

      <section className="panel" style={{ marginBottom: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>Open incidents</h2>
        {!incidents ? (
          <Spinner />
        ) : openIncidents.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>No open incidents.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {openIncidents.map((i) => (
                <tr key={i.id}>
                  <td>
                    <Link href={`/incidents/${i.id}`}>{i.title}</Link>
                  </td>
                  <td>
                    <PriorityBadge priority={i.priority} />
                  </td>
                  <td>
                    <StatusBadge status={i.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Active missions</h2>
        {!missions ? (
          <Spinner />
        ) : activeMissions.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>No active missions.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Mission</th>
                <th>Status</th>
                <th>Members</th>
              </tr>
            </thead>
            <tbody>
              {activeMissions.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link href={`/missions/${m.id}`}>{m.id.slice(0, 8)}</Link>
                  </td>
                  <td>
                    <StatusBadge status={m.status} />
                  </td>
                  <td>{m.members.filter((mm) => !mm.left_at).length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel" style={{ textAlign: "center" }}>
      <div style={{ fontSize: "2rem", fontWeight: 800 }}>{value}</div>
      <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{label}</div>
    </div>
  );
}
