from datetime import datetime, timedelta
import pytz
from typing import List, Dict

TZ_NY = pytz.timezone("America/New_York")

def to_ics_utc(dt_local: datetime) -> str:
    dt_utc = dt_local.astimezone(pytz.utc)
    return dt_utc.strftime("%Y%m%dT%H%M%SZ")

def fold_ics_line(s: str) -> List[str]:
    out = []
    max_len = 70
    while len(s) > max_len:
        out.append(s[:max_len])
        s = " " + s[max_len:]
    out.append(s)
    return out

def city_from_opp(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return " ".join(parts[:-1])
    return name

def generate_ics(calendar_name: str, calendar_color: str, events: List[Dict]) -> str:
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append(f"PRODID:-//TeamWatcher//{calendar_name}//EN")
    lines.append("CALSCALE:GREGORIAN")
    lines.append("METHOD:PUBLISH")
    lines.append(f"NAME:{calendar_name}")
    lines.append(f"X-WR-CALNAME:{calendar_name}")
    lines.append(f"COLOR:{calendar_color}")
    lines.append(f"X-APPLE-CALENDAR-COLOR:{calendar_color}")
    lines.append("REFRESH-INTERVAL;VALUE=DURATION:PT4H")
    lines.append("X-PUBLISHED-TTL:PT4H")

    for ev in events:
        dt_local = ev["start_dt"]
        dt_end_local = ev["end_dt"]
        summary = ev["summary"]
        description = ev["description"]
        uid = ev["uid"]

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now_utc}")
        lines.append(f"SUMMARY:{summary}")
        lines.append(f"DTSTART:{to_ics_utc(dt_local)}")
        lines.append(f"DTEND:{to_ics_utc(dt_end_local)}")
        for folded in fold_ics_line(f"DESCRIPTION:{description}"):
            lines.append(folded)
        lines.append("BEGIN:VALARM")
        lines.append("TRIGGER:-PT60M")
        lines.append("ACTION:DISPLAY")
        lines.append("DESCRIPTION:Event in 60 minutes")
        lines.append("END:VALARM")
        lines.append("BEGIN:VALARM")
        lines.append("TRIGGER:-PT10M")
        lines.append("ACTION:DISPLAY")
        lines.append("DESCRIPTION:Event in 10 minutes")
        lines.append("END:VALARM")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
