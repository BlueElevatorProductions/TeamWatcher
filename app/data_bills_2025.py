from datetime import datetime, timedelta
import pytz

TZ_NY = pytz.timezone("America/New_York")

GAMES = [
    ("Week 10", "2025-11-09", "13:00", "Miami Dolphins", False, "CBS", 10),
    ("Week 11", "2025-11-16", "13:00", "Tampa Bay Buccaneers", True, "CBS", 11),
    ("Week 12", "2025-11-20", "20:15", "Houston Texans", False, "Prime Video", 12),
    ("Week 13", "2025-11-30", "16:25", "Pittsburgh Steelers", False, "CBS", 13),
    ("Week 14", "2025-12-07", "16:25", "Cincinnati Bengals", True, "FOX", 14),
    ("Week 15", "2025-12-14", "13:00", "New England Patriots", False, "CBS", 15),
    ("Week 16", "2025-12-21", "13:00", "Cleveland Browns", False, "CBS", 16),
    ("Week 17", "2025-12-28", "16:25", "Philadelphia Eagles", True, "FOX", 17),
    ("Week 18", "2026-01-04", "13:00", "New York Jets", True, "TBD", 18),
]

def events(zip_code: str):
    evs = []
    for (label, date_str, time_str, opp, home, network, wk_506) in GAMES:
        dt_local = TZ_NY.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
        end_dt = dt_local + timedelta(hours=3)
        city = " ".join(opp.split()[:-1]) if len(opp.split())>=2 else opp
        summary = f"Vs {city}" if home else f"@ {city}"
        map_url = f"https://506sports.com/nfl.php?wk={wk_506}&yr=2025"
        desc = (
            f"{label} — {dt_local.strftime('%a %b %d, %I:%M %p %Z')}\n"
            f"Network: {network}\n"
            f"Market: {zip_code} (NYC area assumptions)\n"
            f"Coverage map (near game day): {map_url}\n"
            "Notes: Listings change due to flex & local carriage rules. Updated Thu + 2h pregame."
        )
        uid = f"bills-2025-{label.lower().replace(' ','')}-{date_str}@teamwatcher.local"
        evs.append({
            "start_dt": dt_local, "end_dt": end_dt, "summary": summary,
            "description": desc, "uid": uid, "network": network
        })
    return evs
