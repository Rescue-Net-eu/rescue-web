"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type ChatMessage,
  type LiveLocation,
  type Mission,
  type MissionStatus,
  type Task,
} from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useMissionSocket, type MissionEvent } from "../../lib/useMissionSocket";
import { ErrorText, Spinner, StatusBadge } from "../../components/ui";
import { MiniMap } from "../../components/mini-map";

const STATUSES: MissionStatus[] = [
  "pending",
  "mobilizing",
  "active",
  "waiting",
  "returning",
];

export default function MissionDetailPage() {
  const { token, user } = useAuth();
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [mission, setMission] = useState<Mission | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [locations, setLocations] = useState<LiveLocation[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [draft, setDraft] = useState("");

  const refreshMission = useCallback(() => {
    if (!token) return;
    api.getMission(token, id).then(setMission).catch(setError);
  }, [token, id]);

  const refreshLocations = useCallback(() => {
    if (!token) return;
    api.liveLocations(token, id).then(setLocations).catch(() => {});
  }, [token, id]);

  useEffect(() => {
    if (!token) return;
    refreshMission();
    api.listMessages(token, id).then(setMessages).catch(setError);
    api.listTasks(token, id).then(setTasks).catch(() => {});
    refreshLocations();
  }, [token, id, refreshMission, refreshLocations]);

  // Realtime: react to mission events without refetching everything.
  const onEvent = useCallback(
    (e: MissionEvent) => {
      switch (e.type) {
        case "mission.chat_message":
          setMessages((m) => [...m, e.data as unknown as ChatMessage]);
          break;
        case "mission.location_updated":
          refreshLocations();
          break;
        case "mission.task_created":
        case "mission.task_updated":
          if (token) api.listTasks(token, id).then(setTasks).catch(() => {});
          break;
        case "mission.status_changed":
        case "mission.member_joined":
        case "mission.member_left":
        case "mission.closed":
          refreshMission();
          break;
      }
    },
    [token, id, refreshLocations, refreshMission],
  );

  const conn = useMissionSocket(id, token, onEvent);

  if (!mission) {
    return (
      <div>
        <ErrorText error={error} />
        <Spinner />
      </div>
    );
  }

  const terminal = ["closed", "cancelled"].includes(mission.status);

  async function setStatus(status: MissionStatus) {
    if (!token) return;
    try {
      await api.updateMissionStatus(token, id, status);
      refreshMission();
    } catch (e) {
      setError(e);
    }
  }

  async function close() {
    if (!token) return;
    try {
      await api.closeMission(token, id);
      refreshMission();
    } catch (e) {
      setError(e);
    }
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !draft.trim()) return;
    const text = draft;
    setDraft("");
    try {
      await api.postMessage(token, id, text);
      // The echoed event will append it; no optimistic insert needed.
    } catch (err) {
      setError(err);
    }
  }

  const activeMembers = mission.members.filter((m) => !m.left_at);
  const center =
    locations.length > 0
      ? { lat: locations[0].latitude, lng: locations[0].longitude }
      : null;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.75rem",
        }}
      >
        <div>
          <h1 style={{ margin: 0 }}>Mission {id.slice(0, 8)}</h1>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.4rem" }}>
            <StatusBadge status={mission.status} />
            <ConnDot state={conn} />
          </div>
        </div>
        {!terminal && (
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <select
              value={mission.status}
              onChange={(e) => setStatus(e.target.value as MissionStatus)}
              style={{ width: "auto" }}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button className="btn secondary" onClick={close}>
              Close mission
            </button>
          </div>
        )}
      </div>

      <ErrorText error={error} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Live map</h2>
          {center ? (
            <MiniMap
              center={center}
              selfPoints={locations.map((l) => ({
                lat: l.latitude,
                lng: l.longitude,
              }))}
            />
          ) : (
            <p style={{ color: "var(--muted)" }}>
              No live locations yet. Responders share location after joining
              with consent.
            </p>
          )}
          <h3>Members ({activeMembers.length})</h3>
          <ul style={{ paddingLeft: "1.1rem", margin: 0 }}>
            {activeMembers.map((m) => (
              <li key={m.user_id}>
                {m.user_id.slice(0, 8)} · {m.role_in_mission}
                {m.live_location_enabled && (
                  <span style={{ color: "var(--ok)" }}> · sharing</span>
                )}
              </li>
            ))}
            {activeMembers.length === 0 && (
              <li style={{ color: "var(--muted)", listStyle: "none" }}>
                No active members.
              </li>
            )}
          </ul>
        </section>

        <section className="panel" style={{ display: "flex", flexDirection: "column" }}>
          <h2 style={{ marginTop: 0 }}>Chat</h2>
          <ChatLog messages={messages} selfId={user?.id} />
          {!terminal && (
            <form onSubmit={send} style={{ display: "flex", gap: "0.5rem", marginTop: "0.6rem" }}>
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Message the mission room…"
              />
              <button className="btn" type="submit" disabled={!draft.trim()}>
                Send
              </button>
            </form>
          )}
        </section>
      </div>

      <TasksPanel
        tasks={tasks}
        terminal={terminal}
        members={activeMembers.map((m) => m.user_id)}
        onCreate={async (title) => {
          if (!token) return;
          try {
            await api.createTask(token, id, { title });
          } catch (e) {
            setError(e);
          }
        }}
        onToggle={async (task) => {
          if (!token) return;
          const next = task.status === "done" ? "open" : "done";
          try {
            await api.updateTask(token, id, task.id, { status: next });
          } catch (e) {
            setError(e);
          }
        }}
      />
    </div>
  );
}

function ConnDot({ state }: { state: string }) {
  const color =
    state === "open" ? "var(--ok)" : state === "connecting" ? "var(--warn)" : "var(--brand)";
  return (
    <span style={{ fontSize: "0.78rem", color: "var(--muted)" }}>
      <span style={{ color }}>●</span> {state === "open" ? "live" : state}
    </span>
  );
}

function ChatLog({
  messages,
  selfId,
}: {
  messages: ChatMessage[];
  selfId?: string;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div
      style={{
        flex: 1,
        minHeight: 200,
        maxHeight: 280,
        overflowY: "auto",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "0.6rem",
        background: "#fbfcfd",
      }}
    >
      {messages.length === 0 && (
        <p style={{ color: "var(--muted)" }}>No messages yet.</p>
      )}
      {messages.map((m) => (
        <div key={m.id} style={{ marginBottom: "0.5rem" }}>
          <span
            style={{
              fontWeight: 700,
              color: m.user_id === selfId ? "var(--brand)" : "var(--text)",
              fontSize: "0.82rem",
            }}
          >
            {m.user_id === selfId ? "You" : m.user_id.slice(0, 8)}
          </span>{" "}
          <span style={{ color: "var(--muted)", fontSize: "0.72rem" }}>
            {new Date(m.created_at).toLocaleTimeString()}
          </span>
          <div>{m.message}</div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}

function TasksPanel({
  tasks,
  terminal,
  onCreate,
  onToggle,
}: {
  tasks: Task[];
  terminal: boolean;
  members: string[];
  onCreate: (title: string) => Promise<void>;
  onToggle: (task: Task) => Promise<void>;
}) {
  const [title, setTitle] = useState("");

  return (
    <section className="panel" style={{ marginTop: "1.25rem" }}>
      <h2 style={{ marginTop: 0 }}>Tasks</h2>
      {tasks.length === 0 && (
        <p style={{ color: "var(--muted)" }}>No tasks yet.</p>
      )}
      {tasks.map((t) => (
        <div
          key={t.id}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            padding: "0.3rem 0",
          }}
        >
          <input
            type="checkbox"
            checked={t.status === "done"}
            onChange={() => onToggle(t)}
            disabled={terminal}
            style={{ width: "auto" }}
          />
          <span
            style={{
              textDecoration: t.status === "done" ? "line-through" : "none",
              color: t.status === "done" ? "var(--muted)" : "var(--text)",
              flex: 1,
            }}
          >
            {t.title}
          </span>
          <StatusBadge status={t.status} />
        </div>
      ))}
      {!terminal && (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!title.trim()) return;
            await onCreate(title);
            setTitle("");
          }}
          style={{ display: "flex", gap: "0.5rem", marginTop: "0.7rem" }}
        >
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a task…"
          />
          <button className="btn" type="submit" disabled={!title.trim()}>
            Add
          </button>
        </form>
      )}
    </section>
  );
}
