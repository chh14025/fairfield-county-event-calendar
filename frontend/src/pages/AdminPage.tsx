import { FormEvent, useEffect, useState } from "react";
import { api, EventItem, fmtDate } from "../api";

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);
  const [pending, setPending] = useState<(EventItem & { submitter_email?: string | null })[]>([]);
  const [error, setError] = useState("");
  const [pubQuery, setPubQuery] = useState("");
  const [tips, setTips] = useState<{ id: string; message: string; email: string | null; created_at: string }[]>([]);
  const [published, setPublished] = useState<EventItem[]>([]);

  async function load() {
    try {
      setPending(await api.pending());
      setAuthed(true);
    } catch {
      setAuthed(false);
    }
  }

  async function loadPublished(q: string) {
    const params: Record<string, string> = { limit: "30" };
    if (q) params.q = q;
    try {
      setPublished((await api.events(params)).items);
    } catch {
      setPublished([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (authed) loadPublished(pubQuery);
  }, [authed, pubQuery]);

  useEffect(() => {
    if (authed) api.tips().then(setTips).catch(() => setTips([]));
  }, [authed]);

  async function onLogin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const password = String(new FormData(e.currentTarget).get("password"));
    const resp = await api.adminLogin(password);
    if (resp.ok) {
      setError("");
      load();
    } else {
      setError("Wrong password");
    }
  }

  async function act(id: string, action: "approve" | "reject") {
    await api.moderate(id, action);
    load();
  }

  async function rejectWithReason(e: EventItem & { submitter_email?: string | null }) {
    const reason = window.prompt(
      "Reason for rejection (optional — used in the email draft to the submitter):"
    );
    if (reason === null) return; // cancelled
    await api.moderate(e.id, "reject", reason || undefined);
    load();
    if (reason && e.submitter_email) {
      const subject = encodeURIComponent(`Your event submission: ${e.title}`);
      const body = encodeURIComponent(
        `Hi,\n\nThanks for submitting "${e.title}" to Fairfield County Events. ` +
          `Unfortunately we couldn't publish it this time.\n\nReason: ${reason}\n\n` +
          `Feel free to resubmit with updates!\n`
      );
      window.open(`mailto:${e.submitter_email}?subject=${subject}&body=${body}`);
    }
  }

  async function removePublished(id: string, title: string) {
    if (!window.confirm(`Remove "${title}" from the site? Ingestion will not re-add it.`)) return;
    await api.removeEvent(id);
    loadPublished(pubQuery);
  }

  if (!authed)
    return (
      <form className="stack" onSubmit={onLogin}>
        <h2>Admin login</h2>
        <input name="password" type="password" placeholder="Password" required />
        <button type="submit">Log in</button>
        {error && <p className="meta">{error}</p>}
      </form>
    );

  return (
    <>
      <h2>Pending submissions ({pending.length})</h2>
      {pending.length === 0 && <p className="meta">Queue is empty.</p>}
      {pending.map((e) => (
        <div className="card" key={e.id}>
          <h3>
            {e.title} <span className="badge">{e.town}</span>
          </h3>
          <div className="meta">
            {fmtDate(e.starts_at, e.all_day)}
            {e.venue_name ? ` · ${e.venue_name}` : ""}
          </div>
          {e.description && <p>{e.description}</p>}
          <div style={{ display: "flex", gap: ".5rem" }}>
            <button onClick={() => act(e.id, "approve")}>Approve</button>
            <button className="secondary" onClick={() => rejectWithReason(e)}>Reject…</button>
          </div>
        </div>
      ))}

      <h2 style={{ marginTop: "2.5rem" }}>Remove published events</h2>
      <p className="meta">
        Removing hides an event permanently — ingestion will not re-add it.
      </p>
      <div className="filters">
        <input
          placeholder="Search published events…"
          value={pubQuery}
          onChange={(e) => setPubQuery(e.target.value)}
        />
      </div>
      {published.length === 0 && <p className="meta">No matching upcoming events.</p>}
      {published.map((e) => (
        <div className="card" key={e.id}>
          <h3>
            {e.title} <span className="badge">{e.town}</span>
          </h3>
          <div className="meta">
            {fmtDate(e.starts_at, e.all_day)}
            {e.venue_name ? ` · ${e.venue_name}` : ""}
          </div>
          <button className="secondary" onClick={() => removePublished(e.id, e.title)}>
            Remove from site
          </button>
        </div>
      ))}
      <h2 style={{ marginTop: "2.5rem" }}>Improvement tips ({tips.length})</h2>
      {tips.length === 0 && <p className="meta">No tips yet.</p>}
      {tips.map((t) => (
        <div className="card" key={t.id}>
          <p style={{ margin: 0 }}>{t.message}</p>
          <div className="meta">
            {new Date(t.created_at).toLocaleString()}
            {t.email ? ` · ${t.email}` : ""}
          </div>
        </div>
      ))}

    </>
  );
}
