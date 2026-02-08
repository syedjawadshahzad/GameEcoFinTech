"""
Shared state management for Economics Games
Handles data persistence across pages and sessions
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import random
import string

# Data file paths
DATA_DIR = "/tmp/economics_games_data"
GAMES_FILE = os.path.join(DATA_DIR, "games.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")


# ============================================================================
# FILE I/O
# ============================================================================

def init_data_dir():
    """Initialize data directory"""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(GAMES_FILE):
        save_json(GAMES_FILE, {})

    if not os.path.exists(SESSIONS_FILE):
        save_json(SESSIONS_FILE, {})


def save_json(filepath: str, data: dict):
    """Save data to JSON file"""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load_json(filepath: str) -> dict:
    """Load data from JSON file"""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def generate_code(length: int = 6) -> str:
    """Generate random alphanumeric code"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


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
    update_game_session(join_code, {"round_timer_end": end_time.isoformat()})


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


def is_round_locked(join_code: str) -> bool:
    """Check if current round is locked"""
    game = get_game_session(join_code)
    return game.get("round_locked", False) if game else False


def advance_round(join_code: str):
    """
    Advance to next round:
    1) Process current round outcomes (scoreboard metrics)
    2) Generate next scenario/event/indicators (player-facing narrative + hints)
    3) Persist updated state
    """
    game = get_game_session(join_code)
    if not game:
        return

    # 1) Process the current round BEFORE moving on (updates metrics/performance for scoreboard)
    process_current_round(join_code)

    # Reload after processing (since it persisted changes)
    game = get_game_session(join_code)
    if not game:
        return

    # 2) Generate new scenario/event based on game type
    game.setdefault("game_state", {})

    if game["game_type"] == "build_country":
        scenarios = [
            {
                "name": "🌪️ Global Recession",
                "description": (
                    "A worldwide recession hits. Exports fall, unemployment rises, and investors pull back. "
                    "Tax revenue shrinks while public pressure for support grows. "
                    "Hint: cut wasteful spending, boost safety nets, and invest in job programs."
                )
            },
            {
                "name": "💡 Tech Boom",
                "description": (
                    "A wave of innovation boosts productivity and attracts foreign investment. "
                    "New industries emerge and wages rise, but inequality may grow. "
                    "Hint: invest in education, infrastructure, and ensure fair access to opportunities."
                )
            },
            {
                "name": "🌋 Natural Disaster",
                "description": (
                    "A major disaster destroys infrastructure and disrupts production. "
                    "Housing shortages and supply chain issues cause prices to rise. "
                    "Hint: prioritize emergency spending, rebuild infrastructure, and stabilize food/energy supply."
                )
            },
            {
                "name": "🌍 Climate Crisis",
                "description": (
                    "Rising pollution and extreme weather damage crops, health, and long-term growth. "
                    "International pressure increases and investors demand sustainability reforms. "
                    "Hint: invest in clean energy, enforce regulations, and improve resilience planning."
                )
            },
            {
                "name": "📈 Trade Agreement",
                "description": (
                    "A new trade deal opens foreign markets and lowers tariffs. "
                    "Exports surge, but local industries face tougher competition. "
                    "Hint: support key industries, invest in logistics, and encourage competitive innovation."
                )
            },
            {
                "name": "👥 Social Movement",
                "description": (
                    "Large protests demand fair wages, equality, and better public services. "
                    "Public trust drops, but reforms could strengthen stability long-term. "
                    "Hint: increase social investment, reduce inequality, and improve governance transparency."
                )
            },
        ]
        game["game_state"]["current_scenario"] = random.choice(scenarios)

    elif game["game_type"] == "beat_market":
        events = [
            {
                "name": "📈 Bull Market Rally",
                "description": (
                    "Markets surge as optimism spreads. Stocks rise rapidly and speculative trading increases. "
                    "Valuations may become inflated. "
                    "Hint: ride momentum, but diversify and set stop-losses in case of reversal."
                )
            },
            {
                "name": "🏦 Interest Rate Hike",
                "description": (
                    "The central bank raises interest rates to fight inflation. Borrowing becomes expensive, "
                    "slowing consumer spending and business expansion. "
                    "Hint: shift toward defensive sectors (banks, utilities) and avoid highly leveraged companies."
                )
            },
            {
                "name": "💥 Company Scandal",
                "description": (
                    "A major firm is caught in fraud and accounting manipulation. Confidence drops and investors panic-sell. "
                    "The whole sector may suffer. "
                    "Hint: avoid risky firms, increase diversification, and consider safer assets temporarily."
                )
            },
            {
                "name": "🚀 Tech Breakthrough",
                "description": (
                    "A revolutionary AI breakthrough reshapes the tech landscape. "
                    "Tech stocks rally, but competition increases and older firms risk becoming obsolete. "
                    "Hint: invest in innovators, but avoid chasing hype without fundamentals."
                )
            },
            {
                "name": "📉 Market Correction",
                "description": (
                    "After a long rally, markets drop sharply as traders take profits. "
                    "Panic spreads, but strong companies remain valuable. "
                    "Hint: hold quality assets, buy undervalued stocks cautiously, and avoid emotional selling."
                )
            },
            {
                "name": "🌍 Climate Regulation",
                "description": (
                    "Governments introduce strict climate laws. Polluting industries face higher costs, "
                    "while renewable energy gains momentum. "
                    "Hint: reduce exposure to fossil-heavy firms and consider clean energy or ESG leaders."
                )
            },
        ]
        game["game_state"]["current_event"] = random.choice(events)

    elif game["game_type"] == "crypto_crash":
        indicators = {
            "sentiment": random.randint(20, 80),
            "volume": random.randint(30, 90),
            "hype": random.randint(25, 95),
            "price": round(random.uniform(8000, 15000), 2),
            "price_change": round(random.uniform(-20, 20), 2),
        }

        # Player-facing story + hints
        if indicators["sentiment"] < 35:
            mood = "Fear dominates the market. Traders are pessimistic and selling pressure is rising."
            hint1 = "Hint: reduce risk exposure or wait for stability."
        elif indicators["sentiment"] > 65:
            mood = "Market optimism is high. Traders believe prices will keep rising."
            hint1 = "Hint: consider profit-taking or set protection against sudden reversals."
        else:
            mood = "Market sentiment is mixed. Traders are uncertain and waiting for direction."
            hint1 = "Hint: diversify and avoid all-in moves."

        if indicators["volume"] > 75:
            activity = "Trading volume is extremely high, signaling major whales and institutions moving funds."
            hint2 = "Hint: high volume can mean a breakout or a crash—watch price trend carefully."
        elif indicators["volume"] < 40:
            activity = "Trading volume is weak, meaning low conviction and thin liquidity."
            hint2 = "Hint: avoid large trades—small moves can trigger sharp drops."
        else:
            activity = "Trading volume is normal, suggesting steady but cautious activity."
            hint2 = "Hint: follow trends but remain prepared for volatility."

        if indicators["hype"] > 75:
            hype_text = "Social media hype is exploding. Meme-driven buying is pushing prices irrationally."
            hint3 = "Hint: hype bubbles often crash—be cautious."
        elif indicators["hype"] < 40:
            hype_text = "Hype is low. The market is quiet and attention is fading."
            hint3 = "Hint: low hype can mean undervaluation, but also weak demand."
        else:
            hype_text = "Hype is moderate. Speculation exists but hasn’t reached mania levels."
            hint3 = "Hint: balanced conditions—focus on fundamentals."

        story = f"{mood} {activity} {hype_text} {hint1} {hint2} {hint3}"

        game["game_state"]["indicators"] = indicators
        game["game_state"]["market_story"] = story

    # 3) Persist round advance and unlock for next round
    update_game_session(join_code, {
        "current_round": game.get("current_round", 0) + 1,
        "round_locked": False,
        "round_timer_end": None,
        "game_state": game["game_state"]
    })


# ============================================================================
# ROUND PROCESSING (SCOREBOARD MECHANICS)
# ============================================================================

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def process_current_round(join_code: str):
    """
    Applies team decisions for the CURRENT round and writes updated metrics/performance back to storage.
    Prevents double-processing via game_state["processed_round"].
    """
    game = get_game_session(join_code)
    if not game:
        return

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

    game.setdefault("game_state", {})
    game["game_state"]["processed_round"] = game.get("current_round")

    games = load_json(GAMES_FILE)
    games[join_code] = game
    save_json(GAMES_FILE, games)


def _process_build_country_round(game: dict):
    """
    Explainable toy mechanics:
    - Infra + education increase GDP and employment
    - Higher tax reduces inequality but can reduce growth
    - Climate policy has short-run tradeoff but affects approval
    Scenario adds a transparent shock.
    """
    scenario = game.get("game_state", {}).get("current_scenario", {})
    scenario_name = (scenario.get("name") or "").lower()

    # Scenario shock
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

    for _, team_data in game.get("teams", {}).items():
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

        gdp_delta = (infra - 25) * 0.25 + (edu - 25) * 0.12 - max(0, tax - 30) * 0.18
        emp_delta = (infra - 25) * 0.30 + (edu - 25) * 0.08 - max(0, tax - 35) * 0.12
        ineq_delta = -(edu - 25) * 0.25 - max(0, tax - 30) * 0.15 + max(0, 25 - tax) * 0.10
        appr_delta = (gdp_delta * 0.5) + (emp_delta * 0.6) - (ineq_delta * 0.3)

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

    base = {"cash": 0.2, "bonds": 0.6, "shares": 1.2, "crypto": 2.0}

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

    for _, team_data in game.get("teams", {}).items():
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

        prev = team_data.get("portfolio_value", {"value": 1_000_000, "returns": 0.0, "risk": 50.0, "esg": 50.0})
        value = float(prev.get("value", 1_000_000))

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

        risk = _clamp(20 + 0.6 * shares + 0.9 * crypto, 0, 100)
        value = value * (1.0 + round_return / 100.0)

        team_data["portfolio_value"] = {
            "value": value,
            "returns": round_return,
            "risk": risk,
            "esg": float(prev.get("esg", 50.0))
        }


def _process_crypto_crash_round(game: dict):
    """
    Uses game indicators as the environment. Teams can store a stance decision: Long/Short/Hold.
    Even if they don't, it still updates a performance object so the scoreboard reacts.
    """
    ind = game.get("game_state", {}).get("indicators", {})
    sentiment = float(ind.get("sentiment", 50))
    hype = float(ind.get("hype", 50))
    price_change = float(ind.get("price_change", 0))

    market_strength = (0.4 * sentiment + 0.4 * hype + 0.2 * (50 + price_change)) / 100.0

    for _, team_data in game.get("teams", {}).items():
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

        total += 1
        if stance == "Long":
            delta = (market_strength - 0.5) * 10.0
            risk_score = _clamp(risk_score + 6.0, 0, 100)
        elif stance == "Short":
            delta = (0.5 - market_strength) * 10.0
            risk_score = _clamp(risk_score + 7.0, 0, 100)
        else:
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
    if "user_type" not in st.session_state:
        st.session_state.user_type = None  # 'admin' or 'team'

    if "join_code" not in st.session_state:
        st.session_state.join_code = None

    if "team_name" not in st.session_state:
        st.session_state.team_name = None

    if "admin_name" not in st.session_state:
        st.session_state.admin_name = None


def set_user_as_admin(admin_name: str, join_code: str):
    """Set current user as admin"""
    st.session_state.user_type = "admin"
    st.session_state.admin_name = admin_name
    st.session_state.join_code = join_code


def set_user_as_team(team_name: str, join_code: str):
    """Set current user as team"""
    st.session_state.user_type = "team"
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
    return st.session_state.get("user_type") == "admin"


def is_team() -> bool:
    """Check if current user is team"""
    return st.session_state.get("user_type") == "team"


def get_current_game() -> Optional[dict]:
    """Get current user's game session"""
    if st.session_state.get("join_code"):
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

    return sum(1 for team in game.get("teams", {}).values() if team.get("ready", False))


def are_all_teams_ready(join_code: str) -> bool:
    """Check if all teams are ready"""
    game = get_game_session(join_code)
    if not game or not game.get("teams"):
        return False

    return all(team.get("ready", False) for team in game["teams"].values())


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
