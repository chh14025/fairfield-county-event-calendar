import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, EventDetail, fmtDate } from "../api";

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (id) api.event(id).then(setEvent).catch((e) => setError(String(e)));
  }, [id]);

  if (error) return <p className="meta">Event not found.</p>;
  if (!event) return <p className="meta">Loading…</p>;

  const mapsQuery = encodeURIComponent(
    [event.venue_name, event.address, event.town, "CT"].filter(Boolean).join(", ")
  );

  return (
    <div>
      <h2>
        {event.title} <span className="badge">{event.town}</span>
      </h2>
      <p className="meta">
        {fmtDate(event.starts_at, event.all_day)}
        {event.ends_at ? ` – ${fmtDate(event.ends_at, event.all_day)}` : ""}
        {event.price_text ? ` · ${event.price_text}` : ""}
      </p>
      {event.venue_name && (
        <p>
          {event.venue_name}
          {event.address ? `, ${event.address}` : ""} ·{" "}
          <a href={`https://www.google.com/maps/search/?api=1&query=${mapsQuery}`} target="_blank" rel="noreferrer">
            Map
          </a>
        </p>
      )}
      {event.description && <p>{event.description}</p>}
      {event.url && (
        <p>
          <a href={event.url} target="_blank" rel="noreferrer">Original event page →</a>
        </p>
      )}
      {event.sources.length > 0 && (
        <p className="meta">Seen on: {event.sources.map((s) => s.source_id).join(", ")}</p>
      )}
    </div>
  );
}
