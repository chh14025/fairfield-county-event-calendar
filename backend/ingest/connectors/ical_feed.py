"""Generic iCal connector: town government calendars (CivicPlus etc.) and LibCal feeds."""
import html as html_lib
import re
from datetime import timedelta

import icalendar
import httpx

from app.utils import to_utc_naive

from .base import USER_AGENT, RawEvent

_TAG_RE = re.compile(r"<[^>]+>")
_TRAILING_URL_RE = re.compile(r"(https?://\S+)\s*$")


def clean_text(value) -> str | None:
    """Strip HTML tags/entities and collapse whitespace (CivicPlus feeds embed
    styled HTML inside LOCATION and DESCRIPTION)."""
    if value is None:
        return None
    text = _TAG_RE.sub(" ", str(value))
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip(" - \t\n")
    return text or None

# The Events Calendar (WordPress) exports season-long series as ONE all-day event
# spanning months (e.g. "Farmers Market, Jun 13 - Oct 10") in addition to per-date
# occurrence VEVENTs. Skip the placeholders; keep the real occurrences.
MAX_ALL_DAY_SPAN = timedelta(days=14)


def parse_ical(data: bytes, town: str, base_url: str | None = None) -> list[RawEvent]:
    cal = icalendar.Calendar.from_ical(data)
    events: list[RawEvent] = []
    for comp in cal.walk("VEVENT"):
        summary = clean_text(comp.get("SUMMARY")) or ""
        uid = str(comp.get("UID", "")).strip()
        dtstart = comp.get("DTSTART")
        if not summary or not uid or dtstart is None:
            continue
        start_raw = dtstart.dt
        all_day = not hasattr(start_raw, "hour")
        dtend = comp.get("DTEND")
        url = comp.get("URL")
        starts_at = to_utc_naive(start_raw)
        ends_at = to_utc_naive(dtend.dt) if dtend is not None else None
        if all_day and ends_at is not None and (ends_at - starts_at) > MAX_ALL_DAY_SPAN:
            continue  # season-long placeholder, not a real single event
        url_str = str(url).strip() if url else None
        if url_str and not url_str.startswith("http"):
            url_str = None  # CivicPlus puts a relative feed path in URL — useless
        description = clean_text(comp.get("DESCRIPTION"))
        if not url_str and description:
            # CivicPlus appends the real event-page link at the end of DESCRIPTION.
            m = _TRAILING_URL_RE.search(description)
            if m:
                url_str = m.group(1).rstrip(".,);")
                description = description[: m.start()].strip(" -") or None
        events.append(
            RawEvent(
                external_id=uid,
                title=summary,
                description=description,
                starts_at=starts_at,
                ends_at=ends_at,
                all_day=all_day,
                venue_name=clean_text(comp.get("LOCATION")),
                town=town,
                url=url_str,
            )
        )
    return events


# Some WordPress WAFs (e.g. westportlibrary.org) 403 unfamiliar user agents even on
# public calendar-subscribe feeds. Identify honestly first; retry once as a browser.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class ICalConnector:
    def __init__(self, source_id: str, url: str, town: str):
        self.source_id = source_id
        self.url = url
        self.town = town

    def _get(self, user_agent: str, browserlike: bool = False) -> httpx.Response:
        headers = {"User-Agent": user_agent, "Accept": "text/calendar, */*"}
        if browserlike:
            headers.update(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
        return httpx.get(self.url, headers=headers, timeout=30, follow_redirects=True)

    def fetch(self) -> list[RawEvent]:
        resp = self._get(USER_AGENT)
        if resp.status_code == 403:
            resp = self._get(BROWSER_UA, browserlike=True)
        resp.raise_for_status()
        return parse_ical(resp.content, self.town, base_url=self.url)
