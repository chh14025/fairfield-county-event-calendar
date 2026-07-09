import { Link, Route, Routes } from "react-router-dom";
import AdminPage from "./pages/AdminPage";
import EventDetailPage from "./pages/EventDetailPage";
import EventsPage from "./pages/EventsPage";
import SubmitPage from "./pages/SubmitPage";

export default function App() {
  return (
    <>
      <nav>
        <Link className="brand" to="/">Fairfield County Events</Link>
        <Link to="/">Events</Link>
        <Link to="/submit">Submit an event</Link>
        <a href="/api/v1/events.ics">Subscribe (.ics)</a>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<EventsPage />} />
          <Route path="/events/:id" element={<EventDetailPage />} />
          <Route path="/submit" element={<SubmitPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </>
  );
}
