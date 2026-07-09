import { FormEvent, useState } from "react";

const TOWNS = [
  "Bethel", "Bridgeport", "Brookfield", "Danbury", "Darien", "Easton",
  "Fairfield", "Greenwich", "Monroe", "New Canaan", "New Fairfield",
  "Newtown", "Norwalk", "Redding", "Ridgefield", "Shelton", "Sherman",
  "Stamford", "Stratford", "Trumbull", "Weston", "Westport", "Wilton", "Other",
];

export default function SubmitPage() {
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const body = {
      title: form.get("title"),
      starts_at: form.get("starts_at"),
      town: form.get("town"),
      venue_name: form.get("venue_name") || null,
      description: form.get("description") || null,
      url: form.get("url") || null,
      submitter_email: form.get("submitter_email"),
      // No rendered honeypot input: browser autofill/extensions fill even hidden
      // fields, silently eating real submissions. The API still rejects any bot
      // that blindly posts hp_field; humans are protected by moderation + rate limit.
      hp_field: "",
    };
    const resp = await fetch("/api/v1/submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (resp.ok) {
      setStatus("sent");
    } else {
      const detail = await resp.json().catch(() => ({}));
      setStatus("error");
      setMessage(JSON.stringify(detail.detail ?? resp.statusText));
    }
  }

  if (status === "sent")
    return <p>Thanks! Your event was submitted and will appear once approved.</p>;

  return (
    <>
      <h2>Submit an event</h2>
      <p className="meta">Car shows, meetups, markets, fundraisers — all welcome. Reviewed before publishing.</p>
      <form className="stack" onSubmit={onSubmit}>
        <input name="title" placeholder="Event title *" required minLength={3} />
        <input name="starts_at" type="datetime-local" required />
        <select name="town" required defaultValue="">
          <option value="" disabled>Town *</option>
          {TOWNS.map((t) => <option key={t}>{t}</option>)}
        </select>
        <input name="venue_name" placeholder="Venue / location" />
        <textarea name="description" placeholder="Description" rows={4} />
        <input name="url" type="url" placeholder="Link (event page, Instagram post…)" />
        <input name="submitter_email" type="email" placeholder="Your email * (not published)" required />
        <button type="submit">Submit for review</button>
        {status === "error" && <p className="meta">Submission failed: {message}</p>}
      </form>
    </>
  );
}
