from datetime import datetime, timedelta
import pytz

TZ_NY = pytz.timezone("America/New_York")

# Best-known UNC men's basketball schedule (Nov 2025–Jan 2026), times in ET.
# (date, time, opponent, home)
GAMES = [
    ("2025-11-11", "19:00", "Radford Highlanders", True),
    ("2025-11-14", "21:00", "North Carolina Central Eagles", True),
    ("2025-11-18", "19:00", "Navy Midshipmen", True),
    ("2025-11-25", "18:00", "St. Bonaventure Bonnies", True),
    ("2025-11-27", "16:30", "Michigan State Spartans", False),
    ("2025-12-02", "21:30", "Kentucky Wildcats", False),
    ("2025-12-07", "17:00", "Georgetown Hoyas", True),
    ("2025-12-13", "14:00", "USC Upstate Spartans", True),
    ("2025-12-16", "20:00", "East Tennessee State Buccaneers", True),
    ("2025-12-20", "15:00", "Ohio State Buckeyes", False),
    ("2025-12-22", "20:00", "East Carolina Pirates", True),
    ("2025-12-30", "19:00", "Florida State Seminoles", True),
    ("2026-01-03", "14:15", "SMU Mustangs", False),
    ("2026-01-10", "18:00", "Wake Forest Demon Deacons", True),
    ("2026-01-14", "21:00", "Stanford Cardinal", False),
]

def events():
    evs = []
    for (date_str, time_str, opp, home) in GAMES:
        dt_local = TZ_NY.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
        end_dt = dt_local + timedelta(hours=2)
        parts = opp.split()
        city = " ".join(parts[:-1]) if len(parts)>=2 else opp
        summary = f"Vs {city}" if home else f"@ {city}"
        uid = f"unc-2025-{date_str}-{opp.replace(' ','').lower()}@teamwatcher.local"
        desc = (
            f"{dt_local.strftime('%a %b %d, %I:%M %p %Z')}\n"
            "TV: TBD — assignments often finalize closer to tip.\n"
            "Notes: Times/TV subject to change; feed updates automatically."
        )
        evs.append({
            "start_dt": dt_local, "end_dt": end_dt, "summary": summary,
            "description": desc, "uid": uid, "network": "TBD"
        })
    return evs
