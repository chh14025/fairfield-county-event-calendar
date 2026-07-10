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
  moderate: (id: string, action: "approve" | "reject", reason?: string) =>
    fetch(`${BASE}/admin/events/${id}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reason ? { reason } : {}),
    }),
  removeEvent: (id: string) => fetch(`${BASE}/admin/events/${id}`, { method: "DELETE" }),
  submitTip: (body: { message: string; email?: string | null }) =>
    fetch(`${BASE}/tips`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  tips: () => get<{ id: string; message: string; email: string | null; created_at: string }[]>("/admin/tips"),
};

function allDayDate(iso: string): Date {
  // all-day events: use the calendar date as-is; never timezone-shift it
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function fmtDate(iso: string, allDay: boolean): string {
  return allDay
    ? allDayDate(iso).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
    : new Date(iso).toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function eventDayKey(e: { starts_at: string; all_day: boolean }): string {
  if (e.all_day) return e.starts_at.slice(0, 10);
  const d = new Date(e.starts_at);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// --- "Add to my calendar" links ---
function compact(iso: string): string {
  return new Date(iso).toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
}

function allDayCompact(iso: string, plusDays = 0): string {
  const d = allDayDate(iso);
  d.setDate(d.getDate() + plusDays);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
}

export function calendarLinks(e: EventItem): { google: string; outlook: string; ics: string } {
  const endIso = e.ends_at ?? new Date(new Date(e.starts_at).getTime() + 3600_000).toISOString();
  const dates = e.all_day
    ? `${allDayCompact(e.starts_at)}/${allDayCompact(e.starts_at, 1)}`
    : `${compact(e.starts_at)}/${compact(endIso)}`;
  const location = [e.venue_name, e.address, e.town, "CT"].filter(Boolean).join(", ");
  const details = (e.description ? e.description.slice(0, 500) + "\n\n" : "") + (e.url ?? "");
  const google =
    "https://calendar.google.com/calendar/render?action=TEMPLATE" +
    `&text=${encodeURIComponent(e.title)}&dates=${dates}` +
    `&details=${encodeURIComponent(details)}&location=${encodeURIComponent(location)}`;
  const outlook =
    "https://outlook.live.com/calendar/0/deeplink/compose?path=/calendar/action/compose&rru=addevent" +
    `&subject=${encodeURIComponent(e.title)}` +
    `&startdt=${encodeURIComponent(e.starts_at)}&enddt=${encodeURIComponent(endIso)}` +
    (e.all_day ? "&allday=true" : "") +
    `&body=${encodeURIComponent(details)}&location=${encodeURIComponent(location)}`;
  return { google, outlook, ics: `/api/v1/events/${e.id}.ics` };
}
