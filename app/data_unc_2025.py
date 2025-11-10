from datetime import datetime, timedelta
import pytz

TZ_NY = pytz.timezone("America/New_York")

# Best-known UNC men's basketball schedule (Nov 2025–Jan 2026), times in ET.
# (date, time, opponent, home, network)
GAMES = [
    # Past games
    ("2025-11-03", "19:00", "Central Arkansas Bears", True, "ACCN"),
    ("2025-11-07", "19:00", "Kansas Jayhawks", True, "ESPN"),
    # Future games
    ("2025-11-11", "19:00", "Radford Highlanders", True, "ACCN"),
    ("2025-11-14", "21:00", "North Carolina Central Eagles", True, "ACCN"),
    ("2025-11-18", "19:00", "Navy Midshipmen", True, "ACCN"),
    ("2025-11-25", "18:00", "St. Bonaventure Bonnies", False, "FS1"),  # Fort Myers Tip-Off
    ("2025-11-27", "16:30", "Michigan State Spartans", False, "FOX"),  # Fort Myers Tip-Off
    ("2025-12-02", "21:30", "Kentucky Wildcats", False, "ESPN"),
    ("2025-12-07", "17:00", "Georgetown Hoyas", True, "ESPN"),
    ("2025-12-13", "14:00", "USC Upstate Spartans", True, "The CW"),
    ("2025-12-16", "20:00", "East Tennessee State Buccaneers", True, "ACCN"),
    ("2025-12-20", "15:00", "Ohio State Buckeyes", False, "CBS"),  # Holiday Hoopsgiving
    ("2025-12-22", "20:00", "East Carolina Pirates", True, "ACCN"),
    ("2025-12-30", "19:00", "Florida State Seminoles", True, "ESPN2"),
    ("2026-01-03", "14:15", "SMU Mustangs", False, "The CW"),
    ("2026-01-10", "18:00", "Wake Forest Demon Deacons", True, "ACCN"),
    ("2026-01-14", "21:00", "Stanford Cardinal", False, "ACCN"),
]

def events():
    evs = []
    for (date_str, time_str, opp, home, network) in GAMES:
        dt_local = TZ_NY.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
        end_dt = dt_local + timedelta(hours=2)
        parts = opp.split()
        city = " ".join(parts[:-1]) if len(parts)>=2 else opp
        summary = f"Vs {city}" if home else f"@ {city}"
        uid = f"unc-2025-{date_str}-{opp.replace(' ','').lower()}@teamwatcher.local"
        desc = (
            f"{dt_local.strftime('%a %b %d, %I:%M %p %Z')}\n"
            f"TV: {network}\n"
            "Notes: Times/TV subject to change; feed updates automatically."
        )
        evs.append({
            "start_dt": dt_local, "end_dt": end_dt, "summary": summary,
            "description": desc, "uid": uid, "network": network,
            "opponent": opp, "home": home
        })
    return evs
