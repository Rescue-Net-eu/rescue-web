"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Mission } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ErrorText, Spinner, StatusBadge } from "../components/ui";

export default function MissionsPage() {
  const { token } = useAuth();
  const [missions, setMissions] = useState<Mission[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (!token) return;
    api.listMissions(token).then(setMissions).catch(setError);
  }, [token]);

  return (
    <div>
      <h1>Missions</h1>
      <ErrorText error={error} />
      <section className="panel">
        {!missions ? (
          <Spinner />
        ) : missions.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No missions yet. Create one from an incident.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Mission</th>
                <th>Status</th>
                <th>Members</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {missions.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link href={`/missions/${m.id}`}>{m.id.slice(0, 8)}</Link>
                  </td>
                  <td>
                    <StatusBadge status={m.status} />
                  </td>
                  <td>{m.members.filter((mm) => !mm.left_at).length}</td>
                  <td style={{ color: "var(--muted)" }}>
                    {m.started_at
                      ? new Date(m.started_at).toLocaleString()
                      : "—"}
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
