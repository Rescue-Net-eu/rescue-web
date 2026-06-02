// Typed client for the rescue-net.eu API (see packages/shared/openapi.yaml).
// Browser-side: the bearer token is held by the auth context and passed in.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Role =
  | "platform_admin"
  | "org_admin"
  | "dispatcher"
  | "team_lead"
  | "responder"
  | "auditor";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: Role;
  status: string;
}

export type IncidentStatus =
  | "draft"
  | "open"
  | "alerting"
  | "mission_created"
  | "active"
  | "suspended"
  | "closed"
  | "cancelled";

export interface Incident {
  id: string;
  title: string;
  description: string | null;
  type: string | null;
  priority: "low" | "medium" | "high";
  status: IncidentStatus;
  created_by: string;
  latitude: number | null;
  longitude: number | null;
  radius_m: number | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface ResponderCandidate {
  id: string;
  user_id: string;
  display_name: string | null;
  verification_status: string;
  skills: string[];
  latitude: number | null;
  longitude: number | null;
  distance_m: number;
}

export interface AlertSendResult {
  incident_id: string;
  alert_type: string;
  expiry_at: string;
  recipients: number;
  alert_ids: string[];
}

export type MissionStatus =
  | "pending"
  | "mobilizing"
  | "active"
  | "waiting"
  | "returning"
  | "closed"
  | "cancelled";

export interface MissionMember {
  user_id: string;
  role_in_mission: string;
  joined_at: string;
  left_at: string | null;
  live_location_enabled: boolean;
}

export interface Mission {
  id: string;
  incident_id: string;
  lead_user_id: string | null;
  status: MissionStatus;
  started_at: string | null;
  closed_at: string | null;
  created_at: string;
  members: MissionMember[];
}

export interface ChatMessage {
  id: string;
  mission_id: string;
  user_id: string;
  message: string;
  created_at: string;
}

export interface LiveLocation {
  user_id: string;
  latitude: number;
  longitude: number;
  accuracy_m: number | null;
  speed: number | null;
  heading: number | null;
  timestamp: string;
}

export interface Task {
  id: string;
  mission_id: string;
  assigned_to: string | null;
  created_by: string;
  title: string;
  description: string | null;
  status: "open" | "in_progress" | "blocked" | "done" | "cancelled";
  priority: "low" | "medium" | "high";
  due_at: string | null;
  completed_at: string | null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  token: string | null,
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  devLogin: (email: string, role: Role) =>
    request<{ access_token: string }>(null, "POST", "/auth/dev/login", {
      email,
      role,
    }),
  me: (token: string) => request<User>(token, "GET", "/me"),

  listIncidents: (token: string) =>
    request<Incident[]>(token, "GET", "/incidents"),
  getIncident: (token: string, id: string) =>
    request<Incident>(token, "GET", `/incidents/${id}`),
  createIncident: (
    token: string,
    payload: {
      title: string;
      description?: string;
      type?: string;
      priority: "low" | "medium" | "high";
      latitude?: number;
      longitude?: number;
      radius_m?: number;
    },
  ) => request<Incident>(token, "POST", "/incidents", payload),
  candidates: (
    token: string,
    id: string,
    params: { verified_only?: boolean; skills?: string[] } = {},
  ) => {
    const q = new URLSearchParams();
    if (params.verified_only === false) q.set("verified_only", "false");
    (params.skills ?? []).forEach((s) => q.append("skills", s));
    const qs = q.toString();
    return request<ResponderCandidate[]>(
      token,
      "GET",
      `/incidents/${id}/candidates${qs ? `?${qs}` : ""}`,
    );
  },
  sendAlert: (
    token: string,
    id: string,
    payload: { alert_type?: string; reason?: string; skills?: string[] },
  ) => request<AlertSendResult>(token, "POST", `/incidents/${id}/alerts`, payload),
  createMission: (token: string, id: string, lead_user_id?: string) =>
    request<Mission>(token, "POST", `/incidents/${id}/create-mission`, {
      lead_user_id: lead_user_id ?? null,
    }),
  closeIncident: (token: string, id: string) =>
    request<Incident>(token, "POST", `/incidents/${id}/close`, {}),

  listMissions: (token: string) =>
    request<Mission[]>(token, "GET", "/missions"),
  getMission: (token: string, id: string) =>
    request<Mission>(token, "GET", `/missions/${id}`),
  updateMissionStatus: (token: string, id: string, status: MissionStatus) =>
    request<Mission>(token, "PATCH", `/missions/${id}`, { status }),
  closeMission: (token: string, id: string, closure_summary?: string) =>
    request<Mission>(token, "POST", `/missions/${id}/close`, {
      closure_summary: closure_summary ?? null,
    }),
  listMessages: (token: string, id: string) =>
    request<ChatMessage[]>(token, "GET", `/missions/${id}/messages`),
  postMessage: (token: string, id: string, message: string) =>
    request<ChatMessage>(token, "POST", `/missions/${id}/messages`, { message }),
  liveLocations: (token: string, id: string) =>
    request<LiveLocation[]>(token, "GET", `/missions/${id}/locations/live`),
  listTasks: (token: string, id: string) =>
    request<Task[]>(token, "GET", `/missions/${id}/tasks`),
  createTask: (
    token: string,
    id: string,
    payload: { title: string; assigned_to?: string; priority?: string },
  ) => request<Task>(token, "POST", `/missions/${id}/tasks`, payload),
  updateTask: (
    token: string,
    missionId: string,
    taskId: string,
    payload: Partial<{ status: string; title: string; assigned_to: string }>,
  ) =>
    request<Task>(
      token,
      "PATCH",
      `/missions/${missionId}/tasks/${taskId}`,
      payload,
    ),
};

export function missionSocketUrl(missionId: string, token: string): string {
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/ws/missions/${missionId}?token=${encodeURIComponent(token)}`;
}
