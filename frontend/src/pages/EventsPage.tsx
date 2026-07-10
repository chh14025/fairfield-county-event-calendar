import { TouchEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, eventDayKey, EventItem, TownCount } from "../api";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function dateKey(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

export default function EventsPage() {
  const today = new Date();
  const [monthStart, setMonthStart] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [events, setEvents] = useState<EventItem[]>([]);
  const [towns, setTowns] = useState<TownCount[]>([]);
  const [town, setTown] = useState("Stamford"); // default to Stamford (densest sources)
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState("");
  const touchStartX = useRef<number | null>(null);

  // 6-week grid surrounding the month
  const gridDays = useMemo(() => {
    const start = new Date(monthStart);
    start.setDate(1 - start.getDay());
    return Array.from({ length: 42 }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [monthStart]);

  useEffect(() => {
    api.towns().then(setTowns).catch(() => {});
  }, []);

  useEffect(() => {
    const from = gridDays[0];
    const to = new Date(gridDays[41]);
    to.setHours(23, 59, 59);
    const params: Record<string, string> = {
      from: from.toISOString(),
      to: to.toISOString(),
      limit: "200",
    };
    if (town) params.town = town;
    if (q) params.q = q;
    api
      .events(params)
      .then((r) => {
        setEvents(r.items);
        setError("");
      })
      .catch((e) => setError(String(e)));
  }, [gridDays, town, q]);

  const byDay = useMemo(() => {
    const m = new Map<string, EventItem[]>();
    for (const e of events) {
      const k = eventDayKey(e);
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(e);
    }
    return m;
  }, [events]);

  const monthLabel = monthStart.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const selectedEvents = selected ? byDay.get(selected) ?? [] : [];
  const selectedLabel = selected
    ? new Date(`${selected}T12:00:00`).toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
      })
    : "";

  function shiftMonth(delta: number) {
    setSelected(null);
    setMonthStart(new Date(monthStart.getFullYear(), monthStart.getMonth() + delta, 1));
  }

  // swipe right on the panel closes it
  function onTouchStart(e: TouchEvent) {
    touchStartX.current = e.touches[0].clientX;
  }
  function onTouchEnd(e: TouchEvent) {
    if (touchStartX.current !== null && e.changedTouches[0].clientX - touchStartX.current > 60) {
      setSelected(null);
    }
    touchStartX.current = null;
  }

  return (
    <>
      <div className="filters">
        <button className="secondary" onClick={() => shiftMonth(-1)} aria-label="Previous month">‹</button>
        <strong className="month-label">{monthLabel}</strong>
        <button className="secondary" onClick={() => shiftMonth(1)} aria-label="Next month">›</button>
        <input placeholder="Search events…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={town} onChange={(e) => setTown(e.target.value)}>
          <option value="">All towns</option>
          {towns.map((t) => (
            <option key={t.town} value={t.town}>
              {t.town} ({t.upcoming_events})
            </option>
          ))}
        </select>
      </div>
      {error && <p className="meta">Could not load events: {error}</p>}

      <div className="cal-grid" role="grid" aria-label={monthLabel}>
        {WEEKDAYS.map((w) => (
          <div className="cal-weekday" key={w}>{w}</div>
        ))}
        {gridDays.map((d) => {
          const k = dateKey(d);
          const dayEvents = byDay.get(k) ?? [];
          const outside = d.getMonth() !== monthStart.getMonth();
          const isToday = k === dateKey(today);
          return (
            <button
              key={k}
              className={
                "cal-cell" +
                (outside ? " outside" : "") +
                (isToday ? " today" : "") +
                (dayEvents.length ? " has-events" : "") +
                (selected === k ? " selected" : "")
              }
              onClick={() => setSelected(selected === k ? null : k)}
            >
              <span className="cal-daynum">{d.getDate()}</span>
              {dayEvents.slice(0, 3).map((e) => (
                <span className="cal-event" key={e.id} title={e.title}>
                  {e.title}
                </span>
              ))}
              {dayEvents.length > 3 && <span className="cal-more">+{dayEvents.length - 3} more</span>}
            </button>
          );
        })}
      </div>

      <div
        className={"day-panel" + (selected ? " open" : "")}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
        aria-hidden={!selected}
      >
        <div className="day-panel-head">
          <h3>{selectedLabel}</h3>
          <button className="secondary" onClick={() => setSelected(null)} aria-label="Close">✕</button>
        </div>
        {selectedEvents.length === 0 && <p className="meta">No events this day.</p>}
        {selectedEvents.map((e) => (
          <Link to={`/events/${e.id}`} className="card panel-card" key={e.id}>
            <h4>{e.title}</h4>
            <div className="meta">
              {e.all_day ? "All day" : fmtTime(e.starts_at)}
              {" · "}
              {e.town}
              {e.venue_name ? ` · ${e.venue_name}` : ""}
              {e.price_text ? ` · ${e.price_text}` : ""}
            </div>
          </Link>
        ))}
      </div>
      {selected && <div className="panel-backdrop" onClick={() => setSelected(null)} />}
    </>
  );
}
