export interface EventItem {
  id: string;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string | null;
  all_day: boolean;
  venue_name: string | null;
  address: string | null;
  town: string;
  url: string | null;
  image_url: string | null;
  price_text: string | null;
}

export interface EventDetail extends EventItem {
  sources: { source_id: string; external_id: string }[];
}

export interface EventList {
  items: EventItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface TownCount {
  town: string;
  upcoming_events: number;
}

const BASE = "/api/v1";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  const resp = await fetch(`${BASE}${path}${qs}`);
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

export const api = {
  events: (params?: Record<string, string>) => get<EventList>("/events", params),
  event: (id: string) => get<EventDetail>(`/events/${id}`),
  towns: () => get<TownCount[]>("/towns"),
  submit: (body: unknown) =>
    fetch(`${BASE}/submissions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  adminLogin: (password: string) =>
    fetch(`${BASE}/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    }),
  pending: () => get<EventItem[]>("/admin/pending"),
  moderate: (id: string, action: "approve" | "reject") =>
    fetch(`${BASE}/admin/events/${id}/${action}`, { method: "POST" }),
};

export function fmtDate(iso: string, allDay: boolean): string {
  const d = new Date(iso);
  return allDay
    ? d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
    : d.toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
