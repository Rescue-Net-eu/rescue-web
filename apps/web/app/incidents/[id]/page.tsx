"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type Incident,
  type ResponderCandidate,
} from "../../lib/api";
import { useAuth } from "../../lib/auth";
import {
  ErrorText,
  PriorityBadge,
  Spinner,
  StatusBadge,
} from "../../components/ui";
import { MiniMap } from "../../components/mini-map";

export default function IncidentDetailPage() {
  const { token } = useAuth();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [candidates, setCandidates] = useState<ResponderCandidate[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [sent, setSent] = useState<number | null>(null);

  const refresh = useCallback(() => {
    if (!token) return;
    api.getIncident(token, id).then(setIncident).catch(setError);
  }, [token, id]);

  useEffect(refresh, [refresh]);

  const loadCandidates = useCallback(() => {
    if (!token) return;
    setError(null);
    api
      .candidates(token, id)
      .then(setCandidates)
      .catch((e) => {
        setCandidates([]);
        setError(e);
      });
  }, [token, id]);

  if (!incident) {
    return (
      <div>
        <ErrorText error={error} />
        <Spinner />
      </div>
    );
  }

  const hasArea =
    incident.latitude != null &&
    incident.longitude != null &&
    incident.radius_m != null;
  const terminal = ["closed", "cancelled"].includes(incident.status);

  async function sendAlert() {
    if (!token) return;
    setBusy("alert");
    setError(null);
    try {
      const result = await api.sendAlert(token, id, {
        reason: reason || undefined,
      });
      setSent(result.recipients);
      refresh();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  }

  async function createMission() {
    if (!token) return;
    setBusy("mission");
    setError(null);
    try {
      const mission = await api.createMission(token, id);
      router.push(`/missions/${mission.id}`);
    } catch (e) {
      setError(e);
      setBusy(null);
    }
  }

  async function close() {
    if (!token) return;
    setBusy("close");
    try {
      await api.closeIncident(token, id);
      refresh();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "1rem",
        }}
      >
        <div>
          <h1 style={{ margin: 0 }}>{incident.title}</h1>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.4rem" }}>
            <PriorityBadge priority={incident.priority} />
            <StatusBadge status={incident.status} />
            {incident.type && (
              <span style={{ color: "var(--muted)" }}>{incident.type}</span>
            )}
          </div>
        </div>
        {!terminal && (
          <button
            className="btn secondary"
            onClick={close}
            disabled={busy === "close"}
          >
            Close incident
          </button>
        )}
      </div>

      {incident.description && (
        <p style={{ color: "#33383d" }}>{incident.description}</p>
      )}

      <ErrorText error={error} />

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: "1.25rem" }}>
        <section className="panel">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <h2 style={{ margin: 0 }}>Nearby responders</h2>
            <button
              className="btn secondary"
              onClick={loadCandidates}
              disabled={!hasArea}
              title={hasArea ? "" : "Set location and radius first"}
            >
              Preview candidates
            </button>
          </div>
          {!hasArea && (
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              This incident has no location/radius, so responders can&apos;t be
              matched.
            </p>
          )}
          {candidates && (
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              {candidates.length} verified responder(s) within{" "}
              {incident.radius_m} m.
            </p>
          )}
          {candidates && candidates.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Responder</th>
                  <th>Skills</th>
                  <th>Distance</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => (
                  <tr key={c.id}>
                    <td>{c.display_name ?? c.user_id.slice(0, 8)}</td>
                    <td>{c.skills.join(", ") || "—"}</td>
                    <td>{(c.distance_m / 1000).toFixed(1)} km</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Location</h2>
          {hasArea ? (
            <MiniMap
              center={{ lat: incident.latitude!, lng: incident.longitude! }}
              points={(candidates ?? [])
                .filter((c) => c.latitude != null && c.longitude != null)
                .map((c) => ({ lat: c.latitude!, lng: c.longitude! }))}
            />
          ) : (
            <p style={{ color: "var(--muted)" }}>No coordinates set.</p>
          )}
        </section>
      </div>

      {!terminal && (
        <section className="panel" style={{ marginTop: "1.25rem" }}>
          <h2 style={{ marginTop: 0 }}>Dispatch</h2>
          <div className="field">
            <label htmlFor="reason">
              Reason{" "}
              <span style={{ fontWeight: 400 }}>
                (required for high-priority alerts)
              </span>
            </label>
            <input
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why are you alerting these responders?"
            />
          </div>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <button
              className="btn"
              onClick={sendAlert}
              disabled={!hasArea || busy === "alert"}
            >
              {busy === "alert" ? "Sending…" : "Send alert"}
            </button>
            <button
              className="btn secondary"
              onClick={createMission}
              disabled={busy === "mission"}
            >
              {busy === "mission" ? "Creating…" : "Create mission"}
            </button>
            {sent != null && (
              <span style={{ color: "var(--ok)", fontWeight: 600 }}>
                Alerted {sent} responder(s).
              </span>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
