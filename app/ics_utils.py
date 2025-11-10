from datetime import datetime, timedelta
import pytz
from typing import List, Dict

TZ_NY = pytz.timezone("America/New_York")

def to_ics_utc(dt_local: datetime) -> str:
    dt_utc = dt_local.astimezone(pytz.utc)
    return dt_utc.strftime("%Y%m%dT%H%M%SZ")

def escape_ics_text(text: str) -> str:
    """
    Escape text according to RFC 5545 section 3.3.11.

    TEXT values must escape:
    - Backslash (\) → \\
    - Newline (\n) → \n (with backslash)
    - Carriage return (\r) → \n (with backslash)
    - Comma (,) → \,
    - Semicolon (;) → \;
    """
    if not text:
        return text

    # Order matters: backslash first, then others
    text = text.replace('\\', '\\\\')  # Escape backslashes
    text = text.replace('\r\n', '\\n')  # Windows line endings
    text = text.replace('\n', '\\n')    # Unix line endings
    text = text.replace('\r', '\\n')    # Mac line endings
    text = text.replace(',', '\\,')     # Escape commas
    text = text.replace(';', '\\;')     # Escape semicolons

    return text

def fold_ics_line(s: str) -> List[str]:
    """
    Fold lines longer than 75 octets according to RFC 5545 section 3.1.
    Continuation lines start with a space.
    """
    out = []
    max_len = 75  # RFC 5545 recommends 75 octets
    while len(s.encode('utf-8')) > max_len:
        # Find safe break point (don't break in middle of UTF-8 character)
        break_at = max_len
        while break_at > 0:
            try:
                s[:break_at].encode('utf-8')
                break
            except UnicodeEncodeError:
                break_at -= 1

        out.append(s[:break_at])
        s = " " + s[break_at:]  # Continuation line starts with space
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
        # Escape summary and description per RFC 5545
        for folded in fold_ics_line(f"SUMMARY:{escape_ics_text(summary)}"):
            lines.append(folded)
        lines.append(f"DTSTART:{to_ics_utc(dt_local)}")
        lines.append(f"DTEND:{to_ics_utc(dt_end_local)}")
        # Escape description before folding
        for folded in fold_ics_line(f"DESCRIPTION:{escape_ics_text(description)}"):
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
