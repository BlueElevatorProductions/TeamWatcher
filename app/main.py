from fastapi import FastAPI, Query, Response
from .ics_utils import generate_ics
from .watch_rules import watch_notes_nfl
from . import data_bills_2025 as bills_data
from . import data_unc_2025 as unc_data

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
    for ev in events:
        lines = ev["description"].split("\n")
        lines.insert(3, f"Subscriptions: {subs}")
        lines.insert(4, "How to watch (guidance):")
        for note in watch_notes_nfl(ev.get("network",""), zip):
            lines.insert(5, f"- {note}")
        ev2 = dict(ev)
        ev2["description"] = "\n".join(lines)
        evs.append(ev2)

    ics = generate_ics(f"Bills — {zip}", BILLS_COLOR, evs)
    return Response(content=ics, media_type="text/calendar; charset=utf-8")

@app.get("/ics/unc")
def ics_unc():
    events = unc_data.events()
    ics = generate_ics("UNC Men's Basketball", UNC_COLOR, events)
    return Response(content=ics, media_type="text/calendar; charset=utf-8")
