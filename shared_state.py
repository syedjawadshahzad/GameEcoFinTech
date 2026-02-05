"""
Shared state management for Economics Games
Handles data persistence across pages and sessions
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import string

# Data file paths
DATA_DIR = "/tmp/economics_games_data"
GAMES_FILE = os.path.join(DATA_DIR, "games.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

def init_data_dir():
    """Initialize data directory"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(GAMES_FILE):
        save_json(GAMES_FILE, {})
    
    if not os.path.exists(SESSIONS_FILE):
        save_json(SESSIONS_FILE, {})

def save_json(filepath: str, data: dict):
    """Save data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filepath: str) -> dict:
    """Load data from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def generate_code(length: int = 6) -> str:
    """Generate random alphanumeric code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ============================================================================
# GAME SESSION MANAGEMENT
# ============================================================================

def create_game_session(game_type: str, admin_name: str, settings: dict) -> str:
    """Create a new game session and return join code"""
    init_data_dir()

    # Clean up old sessions (older than 4 hours)
    cleanup_old_sessions(hours=4)

    games = load_json(GAMES_FILE)
    join_code = generate_code()
    
    # Ensure unique code
    while join_code in games:
        join_code = generate_code()
    
    games[join_code] = {
        "game_type": game_type,  # "build_country" or "beat_market" or "crypto_crash"
        "admin_name": admin_name,
        "created_at": datetime.now().isoformat(),
        "status": "setup",  # setup, running, finished
        "settings": settings,
        "teams": {},
        "team_codes": {},  # Maps team codes to team slots
        "current_round": 0,
        "round_locked": False,
        "round_timer_end": None,
        "game_state": {}
    }
    
    save_json(GAMES_FILE, games)
    return join_code

def generate_team_codes(join_code: str, num_teams: int) -> dict:
    """Generate unique team codes for a game session"""
    init_data_dir()
    
    games = load_json(GAMES_FILE)
    
    if join_code not in games:
        return {}
    
    team_codes = {}
    used_codes = set()
    
    for i in range(1, num_teams + 1):
        # Generate unique code for each team
        team_code = generate_code()
        while team_code in used_codes or team_code in games:
            team_code = generate_code()
        
        used_codes.add(team_code)
        team_codes[team_code] = {
            "team_slot": i,
            "team_name": None,  # Will be filled when team joins
            "assigned": False
        }
    
    # Store team codes in game session
    games[join_code]["team_codes"] = team_codes
    save_json(GAMES_FILE, games)
    
    return team_codes

def get_game_session(join_code: str) -> Optional[dict]:
    """Get game session by join code"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    return games.get(join_code)

def update_game_session(join_code: str, updates: dict):
    """Update game session"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    
    if join_code in games:
        games[join_code].update(updates)
        save_json(GAMES_FILE, games)

def delete_game_session(join_code: str):
    """Delete a game session"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    
    if join_code in games:
        del games[join_code]
        save_json(GAMES_FILE, games)

def get_all_game_sessions() -> dict:
    """Get all game sessions"""
    init_data_dir()
    return load_json(GAMES_FILE)

# ============================================================================
# TEAM MANAGEMENT
# ============================================================================

def add_team_to_game(join_code: str, team_name: str, team_code: str = None, team_data: dict = None) -> tuple:
    """
    Add a team to a game session using a team code
    Returns: (success: bool, message: str, team_slot: int or None)
    """
    init_data_dir()
    games = load_json(GAMES_FILE)
    
    if join_code not in games:
        return False, "Game not found", None
    
    game = games[join_code]
    
    # Check if using team codes system
    if game.get("team_codes"):
        if not team_code:
            return False, "Team code required for this game", None
        
        # Validate team code
        if team_code not in game["team_codes"]:
            return False, "Invalid team code", None
        
        team_code_info = game["team_codes"][team_code]
        
        # Check if code already used
        if team_code_info["assigned"]:
            return False, "This team code has already been used", None
        
        # Assign team to this code
        team_slot = team_code_info["team_slot"]
        team_code_info["team_name"] = team_name
        team_code_info["assigned"] = True
        
        # Add team to game
        games[join_code]["teams"][team_name] = team_data or {
            "joined_at": datetime.now().isoformat(),
            "ready": False,
            "team_code": team_code,
            "team_slot": team_slot
        }
        
        save_json(GAMES_FILE, games)
        return True, f"Joined as Team {team_slot}", team_slot
    
    else:
        # Old system - direct join without team codes
        if team_name in game["teams"]:
            return False, "Team name already taken", None
        
        games[join_code]["teams"][team_name] = team_data or {
            "joined_at": datetime.now().isoformat(),
            "ready": False
        }
        
        save_json(GAMES_FILE, games)
        return True, "Joined successfully", None

def update_team_data(join_code: str, team_name: str, team_data: dict):
    """Update team data"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    
    if join_code in games and team_name in games[join_code]["teams"]:
        games[join_code]["teams"][team_name].update(team_data)
        save_json(GAMES_FILE, games)

def remove_team_from_game(join_code: str, team_name: str):
    """Remove a team from game"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    
    if join_code in games and team_name in games[join_code]["teams"]:
        del games[join_code]["teams"][team_name]
        save_json(GAMES_FILE, games)

# ============================================================================
# ROUND MANAGEMENT
# ============================================================================

def lock_round(join_code: str):
    """Lock the current round (teams can't edit)"""
    update_game_session(join_code, {"round_locked": True})

def unlock_round(join_code: str):
    """Unlock the current round"""
    update_game_session(join_code, {"round_locked": False})

def start_round_timer(join_code: str, duration_seconds: int):
    """Start a timer for the current round"""
    end_time = datetime.now() + timedelta(seconds=duration_seconds)
    update_game_session(join_code, {
        "round_timer_end": end_time.isoformat()
    })

def check_round_timer(join_code: str) -> tuple[bool, int]:
    """Check if round timer is active and get remaining seconds"""
    game = get_game_session(join_code)
    if not game or not game.get("round_timer_end"):
        return False, 0
    
    end_time = datetime.fromisoformat(game["round_timer_end"])
    now = datetime.now()
    
    if now >= end_time:
        return True, 0  # Timer expired
    
    remaining = int((end_time - now).total_seconds())
    return True, remaining

def clear_round_timer(join_code: str):
    """Clear the round timer"""
    update_game_session(join_code, {"round_timer_end": None})

def advance_round(join_code: str):
    """Advance to next round, process current round outcomes, and generate new scenario/event"""
    game = get_game_session(join_code)
    if not game:
        return

    # ✅ Process the round BEFORE moving on (this updates metrics/performance for scoreboard)
    if game.get("status") == "running" and not game.get("round_locked", False):
        # Optional: you can require lock before processing; simplest is to process anyway.
        pass
    process_current_round(join_code)

    # Reload (because process_current_round persisted changes)
    game = get_game_session(join_code)
    if not game:
        return

    import random

    # Generate new scenario based on game type
    if game['game_type'] == 'build_country':
        scenarios = [
            {"name": "🌪️ Global Recession", "description": "Worldwide economic downturn hits!"},
            {"name": "💡 Tech Boom", "description": "Innovation drives rapid growth!"},
            {"name": "🌋 Natural Disaster", "description": "Major disaster strikes!"},
            {"name": "🌍 Climate Crisis", "description": "Environmental damage increases!"},
            {"name": "📈 Trade Agreement", "description": "New trade opportunities emerge!"},
            {"name": "👥 Social Movement", "description": "Citizens demand equality!"},
        ]
        game.setdefault('game_state', {})
        game['game_state']['current_scenario'] = random.choice(scenarios)

    elif game['game_type'] == 'beat_market':
        events = [
            {"name": "📈 Bull Market Rally", "description": "Investor confidence soars!"},
            {"name": "🏦 Interest Rate Hike", "description": "Central bank raises rates!"},
            {"name": "💥 Company Scandal", "description": "Major fraud discovered!"},
            {"name": "🚀 Tech Breakthrough", "description": "Revolutionary AI announced!"},
            {"name": "📉 Market Correction", "description": "Markets overheated, selling begins!"},
            {"name": "🌍 Climate Regulation", "description": "Strict environmental laws passed!"},
        ]
        game.setdefault('game_state', {})
        game['game_state']['current_event'] = random.choice(events)

    elif game['game_type'] == 'crypto_crash':
        game.setdefault('game_state', {})
        game['game_state']['indicators'] = {
            'sentiment': random.randint(20, 80),
            'volume': random.randint(30, 90),
            'hype': random.randint(25, 95),
            'price': round(random.uniform(8000, 15000), 2),
            'price_change': round(random.uniform(-20, 20), 2)
        }

    update_game_session(join_code, {
        "current_round": game["current_round"] + 1,
        "round_locked": False,
        "round_timer_end": None,
        "game_state": game['game_state']
    })

def is_round_locked(join_code: str) -> bool:
    """Check if current round is locked"""
    game = get_game_session(join_code)
    return game.get("round_locked", False) if game else False

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def process_current_round(join_code: str):
    """
    Applies team decisions for the CURRENT round and writes updated metrics/performance back to storage.
    This is the missing link between team inputs and scoreboard.
    """
    game = get_game_session(join_code)
    if not game:
        return

    # Avoid double-processing the same round
    processed_round = game.get("game_state", {}).get("processed_round")
    if processed_round == game.get("current_round"):
        return

    game_type = game.get("game_type")

    if game_type == "build_country":
        _process_build_country_round(game)
    elif game_type == "beat_market":
        _process_beat_market_round(game)
    elif game_type == "crypto_crash":
        _process_crypto_crash_round(game)

    # Mark this round processed
    game.setdefault("game_state", {})
    game["game_state"]["processed_round"] = game.get("current_round")

    # Persist the full mutated game state
    games = load_json(GAMES_FILE)
    games[join_code] = game
    save_json(GAMES_FILE, games)


def _process_build_country_round(game: dict):
    """
    Simple, explainable mechanics:
    - Infra + edu increases GDP and employment
    - Higher tax reduces inequality but can reduce growth
    - Climate policy has short-run tradeoff but affects approval
    Scenario adds a small shock.
    """
    scenario = game.get("game_state", {}).get("current_scenario", {})
    scenario_name = (scenario.get("name") or "").lower()

    # Scenario shock (small and transparent)
    gdp_shock = 0.0
    emp_shock = 0.0
    appr_shock = 0.0
    ineq_shock = 0.0

    if "recession" in scenario_name:
        gdp_shock -= 2.5
        emp_shock -= 2.0
        appr_shock -= 1.0
    elif "tech" in scenario_name or "boom" in scenario_name:
        gdp_shock += 2.0
        emp_shock += 1.0
        appr_shock += 1.0
    elif "disaster" in scenario_name:
        gdp_shock -= 1.5
        appr_shock -= 2.0
    elif "climate" in scenario_name:
        appr_shock -= 1.0
        ineq_shock += 1.0
    elif "trade" in scenario_name:
        gdp_shock += 1.5
        emp_shock += 1.0
    elif "social" in scenario_name:
        appr_shock -= 0.5
        ineq_shock += 2.0

    for team_name, team_data in game.get("teams", {}).items():
        decisions = team_data.get("decisions", {})

        tax = float(decisions.get("tax_rate", 30))
        edu = float(decisions.get("education_spending", 25))
        infra = float(decisions.get("infrastructure_spending", 25))
        climate = decisions.get("climate_policy", "Moderate")

        metrics = team_data.get("metrics", {
            "gdp": 100.0,
            "employment": 75.0,
            "inequality": 50.0,
            "approval": 50.0
        })

        # Policy effects (designed to show differences quickly)
        gdp_delta = (infra - 25) * 0.25 + (edu - 25) * 0.12 - max(0, tax - 30) * 0.18
        emp_delta = (infra - 25) * 0.30 + (edu - 25) * 0.08 - max(0, tax - 35) * 0.12
        ineq_delta = -(edu - 25) * 0.25 - max(0, tax - 30) * 0.15 + max(0, 25 - tax) * 0.10
        appr_delta = (gdp_delta * 0.5) + (emp_delta * 0.6) - (ineq_delta * 0.3)

        # Climate policy: small short-run GDP tradeoff, approval bump for strong action
        if climate == "Strong":
            gdp_delta -= 0.8
            appr_delta += 1.4
        elif climate == "Weak":
            appr_delta -= 0.8

        new_metrics = {
            "gdp": metrics["gdp"] + gdp_delta + gdp_shock,
            "employment": metrics["employment"] + emp_delta + emp_shock,
            "inequality": metrics["inequality"] + ineq_delta + ineq_shock,
            "approval": metrics["approval"] + appr_delta + appr_shock
        }

        # Clamp to sensible ranges
        new_metrics["gdp"] = _clamp(new_metrics["gdp"], 60, 200)
        new_metrics["employment"] = _clamp(new_metrics["employment"], 40, 100)
        new_metrics["inequality"] = _clamp(new_metrics["inequality"], 0, 100)
        new_metrics["approval"] = _clamp(new_metrics["approval"], 0, 100)

        team_data["metrics"] = new_metrics


def _process_beat_market_round(game: dict):
    """
    Applies portfolio allocation to returns with an event shock.
    Writes team_data["portfolio_value"] used by scoreboard.
    """
    event = game.get("game_state", {}).get("current_event", {})
    event_name = (event.get("name") or "").lower()

    # Baseline expected returns per round (toy model)
    base = {
        "cash": 0.2,
        "bonds": 0.6,
        "shares": 1.2,
        "crypto": 2.0
    }

    # Event shock
    shock = {"cash": 0.0, "bonds": 0.0, "shares": 0.0, "crypto": 0.0}
    if "bull" in event_name or "rally" in event_name:
        shock["shares"] += 1.0
        shock["crypto"] += 1.5
    elif "rate hike" in event_name or "interest" in event_name:
        shock["bonds"] -= 0.7
        shock["shares"] -= 0.6
    elif "scandal" in event_name:
        shock["shares"] -= 1.3
    elif "breakthrough" in event_name or "tech" in event_name:
        shock["shares"] += 1.0
    elif "correction" in event_name:
        shock["shares"] -= 1.0
        shock["crypto"] -= 1.8
    elif "climate" in event_name:
        shock["shares"] -= 0.4
        shock["bonds"] += 0.2

    for team_name, team_data in game.get("teams", {}).items():
        portfolio = team_data.get("portfolio", {
            "cash_pct": 25,
            "shares_pct": 25,
            "crypto_pct": 25,
            "bonds_pct": 25
        })

        cash = float(portfolio.get("cash_pct", 25))
        shares = float(portfolio.get("shares_pct", 25))
        crypto = float(portfolio.get("crypto_pct", 25))
        bonds = float(portfolio.get("bonds_pct", 25))

        total = cash + shares + crypto + bonds
        if total <= 0:
            cash, shares, crypto, bonds = 25, 25, 25, 25
            total = 100

        # Normalize to 100
        cash, shares, crypto, bonds = [x * 100.0 / total for x in (cash, shares, crypto, bonds)]

        prev = team_data.get("portfolio_value", {"value": 1_000_000, "returns": 0.0, "risk": 50.0})
        value = float(prev.get("value", 1_000_000))

        # Round return is weighted
        r_cash = base["cash"] + shock["cash"]
        r_bonds = base["bonds"] + shock["bonds"]
        r_shares = base["shares"] + shock["shares"]
        r_crypto = base["crypto"] + shock["crypto"]

        round_return = (
            (cash / 100.0) * r_cash +
            (bonds / 100.0) * r_bonds +
            (shares / 100.0) * r_shares +
            (crypto / 100.0) * r_crypto
        )

        # Risk score: more crypto/shares = higher risk (simple)
        risk = _clamp(20 + 0.6 * shares + 0.9 * crypto, 0, 100)

        # Update value
        value = value * (1.0 + round_return / 100.0)

        team_data["portfolio_value"] = {
            "value": value,
            "returns": round_return,   # per-round return; you can accumulate if you prefer
            "risk": risk,
            "esg": float(prev.get("esg", 50.0))
        }


def _process_crypto_crash_round(game: dict):
    """
    Uses game indicators as the environment. Teams would need to store a 'position' decision.
    If you don't have that yet, we still create movement so the scoreboard reacts.
    """
    ind = game.get("game_state", {}).get("indicators", {})
    sentiment = float(ind.get("sentiment", 50))
    hype = float(ind.get("hype", 50))
    price_change = float(ind.get("price_change", 0))

    # Market regime proxy
    market_strength = (0.4 * sentiment + 0.4 * hype + 0.2 * (50 + price_change)) / 100.0

    for team_name, team_data in game.get("teams", {}).items():
        # If you later add team decisions like: {"stance": "Long"/"Short"/"Hold"}
        stance = team_data.get("decisions", {}).get("stance", "Hold")

        prev = team_data.get("performance", {
            "profit": 0.0,
            "risk_score": 50.0,
            "decisions_correct": 0,
            "total_decisions": 0
        })

        profit = float(prev.get("profit", 0.0))
        risk_score = float(prev.get("risk_score", 50.0))
        correct = int(prev.get("decisions_correct", 0))
        total = int(prev.get("total_decisions", 0))

        # Simple scoring: long benefits when market_strength is high, short when low
        total += 1
        if stance == "Long":
            delta = (market_strength - 0.5) * 10.0
            risk_score = _clamp(risk_score + 6.0, 0, 100)
        elif stance == "Short":
            delta = (0.5 - market_strength) * 10.0
            risk_score = _clamp(risk_score + 7.0, 0, 100)
        else:  # Hold
            delta = 0.5
            risk_score = _clamp(risk_score - 2.0, 0, 100)

        profit += delta
        if delta > 0:
            correct += 1

        team_data["performance"] = {
            "profit": profit,
            "risk_score": risk_score,
            "decisions_correct": correct,
            "total_decisions": total
        }

# ============================================================================
# USER SESSION MANAGEMENT
# ============================================================================

def init_user_session():
    """Initialize user session state"""
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None  # 'admin' or 'team'
    
    if 'join_code' not in st.session_state:
        st.session_state.join_code = None
    
    if 'team_name' not in st.session_state:
        st.session_state.team_name = None
    
    if 'admin_name' not in st.session_state:
        st.session_state.admin_name = None

def set_user_as_admin(admin_name: str, join_code: str):
    """Set current user as admin"""
    st.session_state.user_type = 'admin'
    st.session_state.admin_name = admin_name
    st.session_state.join_code = join_code

def set_user_as_team(team_name: str, join_code: str):
    """Set current user as team"""
    st.session_state.user_type = 'team'
    st.session_state.team_name = team_name
    st.session_state.join_code = join_code

def clear_user_session():
    """Clear user session"""
    st.session_state.user_type = None
    st.session_state.join_code = None
    st.session_state.team_name = None
    st.session_state.admin_name = None

def is_admin() -> bool:
    """Check if current user is admin"""
    return st.session_state.get('user_type') == 'admin'

def is_team() -> bool:
    """Check if current user is team"""
    return st.session_state.get('user_type') == 'team'

def get_current_game() -> Optional[dict]:
    """Get current user's game session"""
    if st.session_state.get('join_code'):
        return get_game_session(st.session_state.join_code)
    return None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_team_count(join_code: str) -> int:
    """Get number of teams in game"""
    game = get_game_session(join_code)
    return len(game.get("teams", {})) if game else 0

def get_ready_team_count(join_code: str) -> int:
    """Get number of teams marked as ready"""
    game = get_game_session(join_code)
    if not game:
        return 0
    
    return sum(1 for team in game.get("teams", {}).values() 
               if team.get("ready", False))

def are_all_teams_ready(join_code: str) -> bool:
    """Check if all teams are ready"""
    game = get_game_session(join_code)
    if not game or not game.get("teams"):
        return False
    
    return all(team.get("ready", False) 
               for team in game["teams"].values())

def set_team_ready(join_code: str, team_name: str, ready: bool = True):
    """Mark team as ready or not ready"""
    update_team_data(join_code, team_name, {"ready": ready})

def format_time_remaining(seconds: int) -> str:
    """Format seconds into MM:SS"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def cleanup_old_sessions(hours: int = 24):
    """Clean up game sessions older than specified hours"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    cutoff = datetime.now() - timedelta(hours=hours)
    
    to_delete = []
    for code, game in games.items():
        created = datetime.fromisoformat(game["created_at"])
        if created < cutoff:
            to_delete.append(code)
    
    for code in to_delete:
        del games[code]
    
    if to_delete:
        save_json(GAMES_FILE, games)
    
    return len(to_delete)
