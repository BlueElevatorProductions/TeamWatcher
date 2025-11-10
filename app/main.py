from fastapi import FastAPI, Query, Response
from datetime import datetime
import pytz
from .ics_utils import generate_ics
from .watch_rules import watch_notes_nfl, watch_notes_ncaamb
from . import data_bills_2025 as bills_data
from . import data_unc_2025 as unc_data
from .data_fetcher import (
    fetch_nfl_game_result,
    fetch_ncaamb_game_result,
    detect_nfl_coverage_conflict
)

app = FastAPI(title="TeamWatcher Feed")

BILLS_COLOR = "#00338D"  # Bills blue
UNC_COLOR = "#7BAFD4"    # Carolina blue

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ics/bills")
def ics_bills(zip: str = Query("11218", alias="zip"),
              subs: str = Query("paramount,youtubetv")):
    events = bills_data.events(zip)
    evs = []
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)

    for ev in events:
        ev2 = dict(ev)
        game_time = ev["start_dt"]
        opponent = ev.get("opponent", "")
        home = ev.get("home", True)
        week = ev.get("week", 0)

        # Check if game is in the past
        is_past = game_time < now

        if is_past:
            # Fetch game result
            result_data = fetch_nfl_game_result(opponent, game_time, home)

            if result_data:
                # Add W/L to title
                result_indicator = result_data['result']
                ev2["summary"] = f"{ev['summary']} ({result_indicator})"

                # Replace description with game summary
                summary_lines = [
                    f"FINAL: {result_data['score']}",
                    "",
                    f"📊 {result_data['summary']}",
                    "",
                    f"🔗 Box Score: {result_data['box_score_url']}",
                ]
                ev2["description"] = "\n".join(summary_lines)
            else:
                # Game was played but result not available yet
                ev2["summary"] = f"{ev['summary']} (Result pending)"
                ev2["description"] = "Game completed. Results will be updated shortly."
        else:
            # Future game - show watch guidance
            lines = ev["description"].split("\n")
            lines.insert(3, f"Subscriptions: {subs}")
            lines.insert(4, "")
            lines.insert(5, "How to watch:")

            # Add coverage conflict detection
            conflict_info = detect_nfl_coverage_conflict({
                'network': ev.get("network", ""),
                'time': game_time,
                'opponent': opponent
            }, week, zip)

            if not conflict_info['is_local']:
                lines.insert(6, conflict_info['guidance'])
                lines.insert(7, "")

            # Add watch notes
            for note in watch_notes_nfl(ev.get("network",""), zip):
                lines.append(f"• {note}")

            ev2["description"] = "\n".join(lines)

        evs.append(ev2)

    ics = generate_ics(f"Bills — {zip}", BILLS_COLOR, evs)
    return Response(content=ics, media_type="text/calendar; charset=utf-8")

@app.get("/ics/unc")
def ics_unc():
    events = unc_data.events()
    evs = []
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)

    for ev in events:
        ev2 = dict(ev)
        game_time = ev["start_dt"]
        opponent = ev.get("opponent", "")
        home = ev.get("home", True)
        network = ev.get("network", "TBD")

        # Check if game is in the past
        is_past = game_time < now

        if is_past:
            # Fetch game result
            result_data = fetch_ncaamb_game_result(opponent, game_time, home)

            if result_data:
                # Add W/L to title
                result_indicator = result_data['result']
                ev2["summary"] = f"{ev['summary']} ({result_indicator})"

                # Replace description with game summary
                summary_lines = [
                    f"FINAL: {result_data['score']}",
                    "",
                    f"📊 {result_data['summary']}",
                    "",
                    f"🔗 Box Score: {result_data['box_score_url']}",
                ]
                ev2["description"] = "\n".join(summary_lines)
            else:
                # Game was played but result not available yet
                ev2["summary"] = f"{ev['summary']} (Result pending)"
                ev2["description"] = "Game completed. Results will be updated shortly."
        else:
            # Future game - add watch guidance
            lines = ev["description"].split("\n")
            lines.append("")
            lines.append("How to watch:")

            # Add network-specific watch notes
            for note in watch_notes_ncaamb(network):
                lines.append(f"• {note}")

            ev2["description"] = "\n".join(lines)

        evs.append(ev2)

    ics = generate_ics("UNC Men's Basketball", UNC_COLOR, evs)
    return Response(content=ics, media_type="text/calendar; charset=utf-8")
