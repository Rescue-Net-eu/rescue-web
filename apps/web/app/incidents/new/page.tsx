"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { ErrorText } from "../../components/ui";

export default function NewIncidentPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    type: "",
    description: "",
    priority: "medium" as "low" | "medium" | "high",
    latitude: "",
    longitude: "",
    radius_m: "",
  });
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const hasLat = form.latitude.trim() !== "";
      const hasLng = form.longitude.trim() !== "";
      const incident = await api.createIncident(token, {
        title: form.title,
        type: form.type || undefined,
        description: form.description || undefined,
        priority: form.priority,
        latitude: hasLat ? Number(form.latitude) : undefined,
        longitude: hasLng ? Number(form.longitude) : undefined,
        radius_m: form.radius_m ? Number(form.radius_m) : undefined,
      });
      router.push(`/incidents/${incident.id}`);
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h1>New incident</h1>
      <form className="panel" onSubmit={submit}>
        <div className="field">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            value={form.title}
            onChange={(e) => set("title", e.target.value)}
            required
          />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div className="field">
            <label htmlFor="type">Type</label>
            <input
              id="type"
              placeholder="flood, search, road…"
              value={form.type}
              onChange={(e) => set("type", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              value={form.priority}
              onChange={(e) => set("priority", e.target.value)}
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            rows={3}
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0.5rem 0" }}>
          Location and radius are required to alert nearby responders.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
          <div className="field">
            <label htmlFor="lat">Latitude</label>
            <input
              id="lat"
              type="number"
              step="any"
              value={form.latitude}
              onChange={(e) => set("latitude", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="lng">Longitude</label>
            <input
              id="lng"
              type="number"
              step="any"
              value={form.longitude}
              onChange={(e) => set("longitude", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="radius">Radius (m)</label>
            <input
              id="radius"
              type="number"
              value={form.radius_m}
              onChange={(e) => set("radius_m", e.target.value)}
            />
          </div>
        </div>
        <ErrorText error={error} />
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create incident"}
        </button>
      </form>
    </div>
  );
}
