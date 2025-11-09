from typing import List

def watch_notes_nfl(network: str, zip_code: str) -> List[str]:
    lines = []
    if network == "CBS":
        lines += [
            "NYC carriage depends on Jets/Giants conflicts; check 506 coverage map near game day.",
            "If airing on WCBS-2 (NYC), Paramount+ will stream it; otherwise use NFL Sunday Ticket (out-of-market).",
        ]
    elif network == "FOX":
        lines += [
            "NYC carriage depends on Jets/Giants conflicts; check 506 coverage map near game day.",
            "If airing on WNYW-5 (NYC), watch via pay-TV/vMVPD; otherwise use NFL Sunday Ticket (out-of-market).",
        ]
    elif network == "Prime Video":
        lines += ["National exclusive: Watch on Prime Video."]
    elif network in ("NBC", "ESPN/ABC", "ESPN"):
        lines += [f"National window: {network}. Use the network app or your vMVPD."]
    else:
        lines += ["Time/Network TBD. Placeholder assignment; check back later."]
    return lines

def watch_notes_ncaamb(network: str) -> List[str]:
    if not network or network == "TBD":
        return ["Network TBD. Times and TV assignments often finalize closer to game day."]
    if network in ("ESPN", "ESPN2", "ESPNU", "ACCN"):
        return [f"TV: {network}. Stream via ESPN app with a participating provider."]
    if network == "ESPN+":
        return ["Streaming exclusive on ESPN+ (no cable login required)."]
    return [f"TV/Stream: {network}"]
