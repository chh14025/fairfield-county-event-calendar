import { FormEvent, useEffect, useState } from "react";
import { api, EventItem, fmtDate } from "../api";

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);
  const [pending, setPending] = useState<EventItem[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setPending(await api.pending());
      setAuthed(true);
    } catch {
      setAuthed(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

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
            <button className="secondary" onClick={() => act(e.id, "reject")}>Reject</button>
          </div>
        </div>
      ))}
    </>
  );
}
