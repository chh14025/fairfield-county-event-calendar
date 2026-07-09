import { Link, Route, Routes } from "react-router-dom";
import AdminPage from "./pages/AdminPage";
import EventDetailPage from "./pages/EventDetailPage";
import EventsPage from "./pages/EventsPage";
import SubmitPage from "./pages/SubmitPage";
import TipsPage from "./pages/TipsPage";

export default function App() {
  return (
    <>
      <nav>
        <Link className="brand" to="/">Fairfield County Events</Link>
        <Link to="/">Events</Link>
        <Link to="/submit">Submit an event</Link>
        <Link to="/tips">Suggest an improvement</Link>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<EventsPage />} />
          <Route path="/events/:id" element={<EventDetailPage />} />
          <Route path="/submit" element={<SubmitPage />} />
          <Route path="/tips" element={<TipsPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </>
  );
}
