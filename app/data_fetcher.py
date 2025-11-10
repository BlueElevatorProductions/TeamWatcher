"""
Data fetcher for live game results and schedules from ESPN.
Implements caching to minimize API calls.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cachetools import TTLCache
import pytz


# Cache: 1 hour TTL, max 200 items
result_cache = TTLCache(maxsize=200, ttl=3600)
schedule_cache = TTLCache(maxsize=100, ttl=7200)


def _fetch_espn_scoreboard(sport: str, league: str, date: datetime) -> Dict[str, Any]:
    """
    Fetch ESPN scoreboard for a specific date.

    Args:
        sport: 'football' or 'basketball'
        league: 'nfl', 'college-football', 'mens-college-basketball'
        date: Date to fetch scores for

    Returns:
        Dictionary with scoreboard data
    """
    date_str = date.strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"

    cache_key = f"{sport}_{league}_{date_str}"
    if cache_key in result_cache:
        return result_cache[cache_key]

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params={'dates': date_str})
            response.raise_for_status()
            data = response.json()
            result_cache[cache_key] = data
            return data
    except Exception as e:
        print(f"Error fetching ESPN scoreboard: {e}")
        return {'events': []}


def fetch_nfl_game_result(opponent: str, game_date: datetime, home: bool) -> Optional[Dict[str, Any]]:
    """
    Fetch NFL game result for Buffalo Bills.

    Args:
        opponent: Opponent team name (e.g., "Miami Dolphins")
        game_date: Date of the game
        home: True if Bills are home team

    Returns:
        Dictionary with:
        - result: 'W' or 'L'
        - score: e.g., "Bills 24, Dolphins 21"
        - summary: Brief game summary
        - box_score_url: Link to full stats
        Or None if game hasn't been played yet
    """
    # Only fetch if game is in the past
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)

    if game_date > now:
        return None

    scoreboard = _fetch_espn_scoreboard('football', 'nfl', game_date)

    # Find the Bills game
    for event in scoreboard.get('events', []):
        competitions = event.get('competitions', [])
        if not competitions:
            continue

        competition = competitions[0]
        competitors = competition.get('competitors', [])

        # Check if Bills are in this game
        bills_competitor = None
        opponent_competitor = None

        for comp in competitors:
            team_name = comp.get('team', {}).get('displayName', '')
            if 'Buffalo' in team_name or 'Bills' in team_name:
                bills_competitor = comp
            elif any(word in team_name for word in opponent.split()):
                opponent_competitor = comp

        if bills_competitor and opponent_competitor:
            # Found the game!
            bills_score = int(bills_competitor.get('score', 0))
            opp_score = int(opponent_competitor.get('score', 0))

            result = 'W' if bills_score > opp_score else 'L'

            opp_short_name = opponent_competitor.get('team', {}).get('shortDisplayName', opponent)
            score_text = f"Bills {bills_score}, {opp_short_name} {opp_score}"

            # Get game summary from headlines
            summary = "Final score"
            headlines = competition.get('headlines', [])
            if headlines:
                summary = headlines[0].get('shortLinkText', summary)

            # Build box score URL
            event_id = event.get('id', '')
            box_score_url = f"https://www.espn.com/nfl/game/_/gameId/{event_id}"

            return {
                'result': result,
                'score': score_text,
                'summary': summary,
                'box_score_url': box_score_url
            }

    return None


def fetch_ncaamb_game_result(opponent: str, game_date: datetime, home: bool) -> Optional[Dict[str, Any]]:
    """
    Fetch Men's College Basketball game result for UNC.

    Args:
        opponent: Opponent team name
        game_date: Date of the game
        home: True if UNC is home team

    Returns:
        Dictionary with result data, or None if not played yet
    """
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)

    if game_date > now:
        return None

    scoreboard = _fetch_espn_scoreboard('basketball', 'mens-college-basketball', game_date)

    # Find the UNC game
    for event in scoreboard.get('events', []):
        competitions = event.get('competitions', [])
        if not competitions:
            continue

        competition = competitions[0]
        competitors = competition.get('competitors', [])

        # Check if UNC is in this game
        unc_competitor = None
        opponent_competitor = None

        for comp in competitors:
            team_name = comp.get('team', {}).get('displayName', '')
            if 'North Carolina' in team_name or 'UNC' in team_name:
                unc_competitor = comp
            elif any(word in team_name for word in opponent.split()):
                opponent_competitor = comp

        if unc_competitor and opponent_competitor:
            # Found the game!
            unc_score = int(unc_competitor.get('score', 0))
            opp_score = int(opponent_competitor.get('score', 0))

            result = 'W' if unc_score > opp_score else 'L'

            opp_short_name = opponent_competitor.get('team', {}).get('shortDisplayName', opponent)
            score_text = f"UNC {unc_score}, {opp_short_name} {opp_score}"

            # Get game summary
            summary = "Final score"
            headlines = competition.get('headlines', [])
            if headlines:
                summary = headlines[0].get('shortLinkText', summary)

            # Build box score URL
            event_id = event.get('id', '')
            box_score_url = f"https://www.espn.com/mens-college-basketball/game/_/gameId/{event_id}"

            return {
                'result': result,
                'score': score_text,
                'summary': summary,
                'box_score_url': box_score_url
            }

    return None


def fetch_nfl_week_schedule(week: int, season: int = 2025) -> List[Dict[str, Any]]:
    """
    Fetch all NFL games for a specific week.
    Used for local coverage conflict detection.

    Args:
        week: NFL week number (1-18)
        season: NFL season year

    Returns:
        List of game dictionaries with team names, networks, time
    """
    cache_key = f"nfl_week_{season}_{week}"
    if cache_key in schedule_cache:
        return schedule_cache[cache_key]

    try:
        # ESPN's scoreboard endpoint can give us the week's games
        # We'll fetch a few days worth to catch the whole week
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params={
                'seasontype': 2,  # Regular season
                'week': week
            })
            response.raise_for_status()
            data = response.json()

            games = []
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) >= 2:
                    away_team = competitors[0].get('team', {}).get('displayName', '')
                    home_team = competitors[1].get('team', {}).get('displayName', '')

                    # Get broadcast info
                    broadcasts = competition.get('broadcasts', [])
                    network = 'TBD'
                    if broadcasts:
                        network = broadcasts[0].get('names', ['TBD'])[0]

                    # Get game time
                    game_time_str = event.get('date', '')
                    game_time = None
                    if game_time_str:
                        try:
                            game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
                        except:
                            pass

                    games.append({
                        'away_team': away_team,
                        'home_team': home_team,
                        'network': network,
                        'time': game_time
                    })

            schedule_cache[cache_key] = games
            return games

    except Exception as e:
        print(f"Error fetching NFL week schedule: {e}")
        return []


def detect_nfl_coverage_conflict(bills_game: Dict[str, Any], week: int, zip_code: str) -> Dict[str, Any]:
    """
    Detect if Bills game will be pre-empted by local team (Jets/Giants in NYC area).

    Args:
        bills_game: Bills game info (network, time, opponent)
        week: NFL week number
        zip_code: User's ZIP code

    Returns:
        Dictionary with:
        - is_local: True if Bills game should air locally
        - conflict_game: Game that might conflict, if any
        - guidance: Text explaining the situation
    """
    # NYC area ZIP codes where Jets/Giants games take priority
    nyc_zipcodes = ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                    '110', '111', '112', '113', '114', '115', '116', '117', '118',
                    '070', '071', '072', '073', '074', '075', '076', '077', '078', '079']

    zip_prefix = zip_code[:3]
    is_nyc_area = zip_prefix in nyc_zipcodes

    if not is_nyc_area:
        return {
            'is_local': True,
            'conflict_game': None,
            'guidance': "This game should air in the Buffalo market."
        }

    # Get all games this week
    week_games = fetch_nfl_week_schedule(week)

    bills_network = bills_game.get('network', '').upper()
    bills_time = bills_game.get('time')

    # Check for Jets or Giants games at the same time on the same network
    for game in week_games:
        if 'Jets' in game['home_team'] or 'Jets' in game['away_team'] or \
           'Giants' in game['home_team'] or 'Giants' in game['away_team']:

            game_network = game['network'].upper()

            # Same network and same time window = conflict
            if bills_network in game_network or game_network in bills_network:
                if bills_time and game['time']:
                    time_diff = abs((bills_time - game['time']).total_seconds())
                    if time_diff < 7200:  # Within 2 hours = same window
                        local_team = 'Jets' if 'Jets' in (game['home_team'] + game['away_team']) else 'Giants'
                        return {
                            'is_local': False,
                            'conflict_game': game,
                            'guidance': f"⚠️ The {local_team} game may take precedence in the NYC market. Check 506sports.com for your exact coverage."
                        }

    return {
        'is_local': True,
        'conflict_game': None,
        'guidance': "No local conflicts detected. Game should air in your market. Verify at 506sports.com."
    }
