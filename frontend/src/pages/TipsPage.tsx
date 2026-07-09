import { FormEvent, useState } from "react";
import { api } from "../api";

export default function TipsPage() {
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const resp = await api.submitTip({
      message: String(form.get("message") ?? ""),
      email: String(form.get("email") ?? "") || null,
    });
    if (resp.ok) {
      setStatus("sent");
    } else {
      const detail = await resp.json().catch(() => ({}));
      setStatus("error");
      setMessage(typeof detail.detail === "string" ? detail.detail : "Please write at least a few words.");
    }
  }

  if (status === "sent") return <p>Thank you! Every suggestion gets read.</p>;

  return (
    <>
      <h2>Suggest an improvement</h2>
      <p className="meta">
        Missing events? A feature you wish existed? Something broken? Tell us — this site
        is built for the community and shaped by these tips.
      </p>
      <form className="stack" onSubmit={onSubmit}>
        <textarea name="message" placeholder="Your suggestion… *" rows={5} required minLength={5} maxLength={2000} />
        <input name="email" type="email" placeholder="Email (optional — only if you'd like a reply)" />
        <button type="submit">Send suggestion</button>
        {status === "error" && <p className="meta">Could not send: {message}</p>}
      </form>
    </>
  );
}
