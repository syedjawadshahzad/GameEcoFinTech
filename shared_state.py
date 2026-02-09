"""
Shared state management for Economics Games
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import random
import string
import math

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
        "game_type": game_type,
        "admin_name": admin_name,
        "created_at": datetime.now().isoformat(),
        "status": "setup",
        "settings": settings,
        "teams": {},
        "team_codes": {},
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
        team_code = generate_code()
        while team_code in used_codes or team_code in games:
            team_code = generate_code()

        used_codes.add(team_code)
        team_codes[team_code] = {
            "team_slot": i,
            "team_name": None,
            "assigned": False
        }

    games[join_code]["team_codes"] = team_codes
    save_json(GAMES_FILE, games)

    return team_codes


def get_game_session(join_code: str) -> Optional[dict]:
    """Get game session by join code"""
    init_data_dir()
    games = load_json(GAMES_FILE)
    return games.get(join_code.upper() if join_code else "")


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

    if game.get("team_codes"):
        if not team_code:
            return False, "Team code required for this game", None

        if team_code not in game["team_codes"]:
            return False, "Invalid team code", None

        team_code_info = game["team_codes"][team_code]

        if team_code_info["assigned"]:
            return False, "This team code has already been used", None

        team_slot = team_code_info["team_slot"]
        team_code_info["team_name"] = team_name
        team_code_info["assigned"] = True

        games[join_code]["teams"][team_name] = team_data or {
            "joined_at": datetime.now().isoformat(),
            "ready": False,
            "team_code": team_code,
            "team_slot": team_slot
        }

        save_json(GAMES_FILE, games)
        return True, f"Joined as Team {team_slot}", team_slot

    # Old system
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
        return True, 0

    remaining = int((end_time - now).total_seconds())
    return True, remaining


def clear_round_timer(join_code: str):
    """Clear the round timer"""
    update_game_session(join_code, {"round_timer_end": None})


def is_round_locked(join_code: str) -> bool:
    """Check if current round is locked"""
    game = get_game_session(join_code)
    return game.get("round_locked", False) if game else False


# ============================================================================
# ROUND PROCESSING (SCOREBOARD MECHANICS)
# ============================================================================

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _gauss_score(x: float, mu: float, sigma: float) -> float:
    """
    Returns 0..1, peaks at x=mu, penalizes both low and high values.
    """
    sigma = float(sigma)
    if sigma <= 0:
        return 0.0
    z = (float(x) - float(mu)) / sigma
    return float(math.exp(-0.5 * z * z))


def compute_build_country_score(team_data: dict) -> float:
    """
    Goldilocks score:
    - Extremes (very low or very high tax/spending sliders) score poorly.
    - Best scores come from "reasonable middle" policy + good macro outcomes.
    - Sustainability penalty: deficit & debt reduce score.

    Returns score in 0..100 range (clamped).
    """
    decisions = team_data.get("decisions", {}) or {}
    metrics = team_data.get("metrics", {
        "gdp": 100.0,
        "employment": 75.0,
        "inequality": 50.0,
        "approval": 50.0,
        "debt": 0.0,
    })
    fiscal = team_data.get("fiscal", {}) or {}

    tax = float(decisions.get("tax_rate", 30.0))
    edu = float(decisions.get("education_spending", 25.0))
    infra = float(decisions.get("infrastructure_spending", 25.0))

    # 1) Policy "Goldilocks" fits (0..1)
    tax_fit = _gauss_score(tax, mu=30.0, sigma=25.0)
    edu_fit = _gauss_score(edu, mu=25.0, sigma=25.0)
    infra_fit = _gauss_score(infra, mu=25.0, sigma=25.0)

    policy_fit = (tax_fit + edu_fit + infra_fit) / 3.0

    # 2) Outcomes (0..1) from metrics
    gdp = float(metrics.get("gdp", 100.0))
    emp = float(metrics.get("employment", 75.0))
    ineq = float(metrics.get("inequality", 50.0))
    appr = float(metrics.get("approval", 50.0))

    gdp_s = _clamp((gdp - 60.0) / 140.0, 0.0, 1.0)           # 60..200
    emp_s = _clamp((emp - 40.0) / 60.0, 0.0, 1.0)            # 40..100
    ineq_s = _clamp((100.0 - ineq) / 100.0, 0.0, 1.0)        # lower inequality better
    appr_s = _clamp(appr / 100.0, 0.0, 1.0)

    outcomes = 0.30 * gdp_s + 0.25 * emp_s + 0.25 * ineq_s + 0.20 * appr_s

    # 3) Sustainability penalty (0..1)
    debt = float(metrics.get("debt", 0.0))  # % of GDP (toy)
    deficit = float(fiscal.get("deficit_pct_gdp", 0.0))

    debt_pen = _clamp(debt / 120.0, 0.0, 1.0)               # 120% debt is "very bad"
    deficit_pen = _clamp(max(0.0, deficit) / 8.0, 0.0, 1.0) # 8% deficit "very bad"
    sustainability_pen = 0.40 * debt_pen + 0.20 * deficit_pen

    # Final score: reward outcomes + calibrated policy, penalize fiscal stress
    policy_multiplier = 0.90 + 0.20 * policy_fit   # range: 0.90 .. 1.10
    raw = 100.0 * outcomes * policy_multiplier * (1.0 - 0.05 * sustainability_pen)

    return float(_clamp(raw, 0.0, 100.0))


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
    Realistic-ish build-country engine + fiscal constraint.

    Interpretation:
    - tax_rate: 0..50 (tax effort proxy)
    - education_spending slider 0..50 maps to edu_pct_gdp: 0..10% of GDP
    - infrastructure_spending slider 0..50 maps to infra_pct_gdp: 0..8% of GDP
    - baseline "other" spending (% GDP) represents welfare/health/admin obligations
    - deficit adds to debt (% GDP)
    """
    scenario = game.get("game_state", {}).get("current_scenario", {})
    scenario_name = (scenario.get("name") or "").lower()

    # Scenario shocks (small)
    gdp_shock = 0.0
    emp_shock = 0.0
    appr_shock = 0.0
    ineq_shock = 0.0

    if "recession" in scenario_name:
        gdp_shock -= 1.8
        emp_shock -= 1.4
        appr_shock -= 0.8
    elif "tech" in scenario_name or "boom" in scenario_name:
        gdp_shock += 1.4
        emp_shock += 0.8
        appr_shock += 0.7
        ineq_shock += 0.6
    elif "disaster" in scenario_name:
        gdp_shock -= 1.2
        appr_shock -= 1.5
    elif "climate" in scenario_name:
        appr_shock -= 0.6
        ineq_shock += 0.6
    elif "trade" in scenario_name:
        gdp_shock += 1.1
        emp_shock += 0.6
    elif "social" in scenario_name:
        appr_shock -= 0.4
        ineq_shock += 1.2

    for _, team_data in game.get("teams", {}).items():
        decisions = team_data.get("decisions", {}) or {}

        tax = float(decisions.get("tax_rate", 30))
        edu_slider = float(decisions.get("education_spending", 25))
        infra_slider = float(decisions.get("infrastructure_spending", 25))
        climate = decisions.get("climate_policy", "Moderate")

        metrics = team_data.get("metrics", {
            "gdp": 100.0,
            "employment": 75.0,
            "inequality": 50.0,
            "approval": 50.0,
            "debt": 0.0,   # %GDP
        })

        # Map sliders to realistic % of GDP
        edu_pct_gdp = _clamp(edu_slider * 0.20, 0.0, 10.0)     # 0..10% GDP
        infra_pct_gdp = _clamp(infra_slider * 0.16, 0.0, 8.0)  # 0..8% GDP

        # Baseline obligations (% GDP)
        other_spend_pct_gdp = 18.0

        # Climate policy: small fiscal add-on + credibility
        climate_cost_pct_gdp = 0.0
        climate_growth_bonus = 0.0
        climate_approval_bonus = 0.0
        if climate == "Strong":
            climate_cost_pct_gdp = 1.0
            climate_growth_bonus = 0.25
            climate_approval_bonus = 0.6
        elif climate == "Weak":
            climate_growth_bonus = -0.15
            climate_approval_bonus = -0.4

        total_spend_pct_gdp = other_spend_pct_gdp + edu_pct_gdp + infra_pct_gdp + climate_cost_pct_gdp

        # Revenue as % of GDP (toy calibration)
        # tax=30 -> ~25.5%; tax=50 -> ~34.5%; tax=10 -> ~16.5%
        revenue_pct_gdp = 12.0 + 0.45 * tax
        revenue_pct_gdp *= (1.0 - 0.0025 * max(0.0, tax - 40.0))  # mild high-tax drag
        revenue_pct_gdp = _clamp(revenue_pct_gdp, 0.0, 45.0)

        deficit_pct_gdp = total_spend_pct_gdp - revenue_pct_gdp  # + = deficit, - = surplus

        # Debt dynamics (%GDP)
        debt = float(metrics.get("debt", 0.0))
        interest = 0.04
        debt = max(0.0, debt * (1.0 + interest) + deficit_pct_gdp)

        deficit_stress = max(0.0, deficit_pct_gdp)
        debt_burden = _clamp(debt / 2.0, 0.0, 100.0)  # 200% debt -> 100

        # Investment effects (anchored near typical levels)
        infra_effect = (infra_pct_gdp - 3.0) * 0.55   # ~3% GDP typical
        edu_effect = (edu_pct_gdp - 5.0) * 0.35       # ~5% GDP typical

        # Tax distortion above ~30
        tax_drag = max(0.0, tax - 20.0) * 0.10

        # >>> Stronger fiscal drags so extremes don't dominate (key)
        gdp_delta = (
            infra_effect + edu_effect
            - tax_drag
            - (0.010 * debt_burden)
            - (0.050 * deficit_stress)
            + climate_growth_bonus
        )
        emp_delta = (
            (infra_effect * 0.90) + (edu_effect * 0.55)
            - (tax_drag * 0.70)
            - (0.007 * debt_burden)
            - (0.020 * deficit_stress)
        )

        ineq_delta = (
            -0.50 * (edu_pct_gdp - 5.0)
            -0.05 * max(0.0, tax - 25.0)
            +0.10 * max(0.0, 20.0 - tax)
        )

        appr_delta = (
            0.45 * gdp_delta +
            0.55 * emp_delta -
            0.25 * ineq_delta +
            climate_approval_bonus
            - 0.20 * deficit_stress
            - 0.12 * (debt_burden / 10.0)
        )

        new_metrics = {
            "gdp": float(metrics["gdp"]) + gdp_delta + gdp_shock,
            "employment": float(metrics["employment"]) + emp_delta + emp_shock,
            "inequality": float(metrics["inequality"]) + ineq_delta + ineq_sh_toggle(ineq_shock),
            "approval": float(metrics["approval"]) + appr_delta + appr_shock,
            "debt": float(debt),
        }

        new_metrics["gdp"] = _clamp(new_metrics["gdp"], 60, 200)
        new_metrics["employment"] = _clamp(new_metrics["employment"], 40, 100)
        new_metrics["inequality"] = _clamp(new_metrics["inequality"], 0, 100)
        new_metrics["approval"] = _clamp(new_metrics["approval"], 0, 100)
        new_metrics["debt"] = _clamp(new_metrics["debt"], 0, 250)

        # Fiscal diagnostics (used by scoring + can be shown in UI)
        team_data["fiscal"] = {
            "edu_pct_gdp": round(edu_pct_gdp, 2),
            "infra_pct_gdp": round(infra_pct_gdp, 2),
            "other_spend_pct_gdp": round(other_spend_pct_gdp, 2),
            "total_spend_pct_gdp": round(total_spend_pct_gdp, 2),
            "revenue_pct_gdp": round(revenue_pct_gdp, 2),
            "deficit_pct_gdp": round(deficit_pct_gdp, 2),
            "debt_pct_gdp": round(new_metrics["debt"], 2),
        }

        team_data["metrics"] = new_metrics


def ineq_sh_toggle(x: float) -> float:
    # Kept as a simple hook in case you want later scenario-specific inequality amplification.
    return float(x)


def _process_beat_market_round(game: dict):
    """Beat-market toy mechanics with event shock."""
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
    Student-friendly crypto game:
    - 4 assets: BTC, ETH, DOGE, STABLE
    - Teams choose allocations (%) + leverage (1x..5x)
    - Uses indicators to generate asset returns each round
    - Applies leverage + liquidation rule
    - Updates team_data["crypto_portfolio"] for scoreboard
    """

    def _normalize_allocations(a: dict) -> dict:
        keys = ["btc", "eth", "doge", "stable"]
        cleaned = {k: float(a.get(k, 0.0)) for k in keys}
        total = sum(cleaned.values())

        if total <= 0:
            cleaned = {"btc": 50.0, "eth": 20.0, "doge": 10.0, "stable": 20.0}
            total = 100.0

        for k in cleaned:
            cleaned[k] = cleaned[k] * 100.0 / total

        return cleaned

    def _compute_market_risk(indicators: dict) -> float:
        hype = float(indicators.get("hype", 50))
        sentiment = float(indicators.get("sentiment", 50))
        volume = float(indicators.get("volume", 60))
        pc = float(indicators.get("price_change", 0))

        divergence = max(0.0, hype - sentiment)
        trend_down = max(0.0, -pc)
        thin_liq = max(0.0, 40.0 - volume)

        risk = 0.45 * divergence + 0.35 * (trend_down * 3.0) + 0.20 * thin_liq
        return _clamp(risk, 0.0, 100.0)

    def _asset_returns(indicators: dict) -> dict:
        sentiment = float(indicators.get("sentiment", 50))
        hype = float(indicators.get("hype", 50))
        volume = float(indicators.get("volume", 60))
        pc = float(indicators.get("price_change", 0))

        s = (sentiment - 50.0) / 50.0
        h = (hype - 50.0) / 50.0
        v = (volume - 60.0) / 40.0

        drift = pc * 0.25

        r_btc = drift + (s * 3.0) + (v * 0.8)
        r_eth = drift + (s * 3.5) + (h * 1.5) + (v * 1.0)
        r_doge = drift + (h * 7.0) + (s * 1.5) + (v * 1.2)
        r_stable = random.uniform(-0.05, 0.08)

        return {
            "btc": _clamp(r_btc, -12.0, 12.0),
            "eth": _clamp(r_eth, -18.0, 18.0),
            "doge": _clamp(r_doge, -30.0, 30.0),
            "stable": _clamp(r_stable, -0.2, 0.2),
        }

    def _liquidation_threshold(leverage: float) -> float:
        lev = _clamp(leverage, 1.0, 5.0)
        mapping = {1.0: 60.0, 2.0: 35.0, 3.0: 22.0, 4.0: 15.0, 5.0: 12.0}
        return mapping.get(float(int(lev)), 22.0)

    gs = game.setdefault("game_state", {})
    indicators = gs.get("indicators", {})
    if not indicators:
        indicators = {
            "sentiment": random.randint(20, 80),
            "volume": random.randint(30, 90),
            "hype": random.randint(25, 95),
            "price": round(random.uniform(8000, 15000), 2),
            "price_change": round(random.uniform(-20, 20), 2),
        }
        gs["indicators"] = indicators

    market_risk = _compute_market_risk(indicators)
    asset_r = _asset_returns(indicators)

    gs["asset_returns"] = asset_r
    gs["market_risk"] = round(market_risk, 1)

    for _, team_data in game.get("teams", {}).items():
        decisions = team_data.get("decisions", {}) if isinstance(team_data.get("decisions", {}), dict) else {}

        allocations = _normalize_allocations(
            decisions.get("allocations", {}) if isinstance(decisions.get("allocations", {}), dict) else {}
        )
        leverage = _clamp(float(decisions.get("leverage", 1)), 1.0, 5.0)

        prev = team_data.get("crypto_portfolio", {
            "equity": 1000.0,
            "last_return_pct": 0.0,
            "total_return_pct": 0.0,
            "risk_exposure": 0.0,
            "liquidations": 0,
        })

        equity = float(prev.get("equity", 1000.0))
        total_return = float(prev.get("total_return_pct", 0.0))
        liquidations = int(prev.get("liquidations", 0))

        unlev_return = (
            (allocations["btc"] / 100.0) * asset_r["btc"] +
            (allocations["eth"] / 100.0) * asset_r["eth"] +
            (allocations["doge"] / 100.0) * asset_r["doge"] +
            (allocations["stable"] / 100.0) * asset_r["stable"]
        )

        lev_return = unlev_return * leverage

        risky_fraction = (allocations["btc"] + allocations["eth"] + allocations["doge"]) / 100.0
        risk_exposure = risky_fraction * (leverage / 5.0) * (market_risk / 100.0) * 100.0
        risk_exposure = _clamp(risk_exposure, 0.0, 100.0)

        thresh = _liquidation_threshold(leverage)
        liquidated = False

        if lev_return <= -thresh:
            liquidated = True
            liquidations += 1
            equity *= 0.35
            lev_return = -thresh
        else:
            equity *= (1.0 + lev_return / 100.0)

        total_return += lev_return

        exposure_label = (
            "Low" if risk_exposure < 25 else
            "Medium" if risk_exposure < 55 else
            "High" if risk_exposure < 80 else
            "Extreme"
        )

        simple_explain = (
            f"You invested {int(risky_fraction*100)}% in crypto coins and used {leverage:.0f}x leverage. "
            f"Market risk is {gs['market_risk']}/100, so your risk exposure is {exposure_label} "
            f"({risk_exposure:.0f}/100)."
        )

        if liquidated:
            outcome_text = (
                f"🚨 Liquidation! Your leveraged loss hit {thresh:.0f}% or worse in one round, "
                "so your position was automatically closed with a big penalty. "
                "Hint: reduce leverage or move more into Stablecoin when risk is high."
            )
        else:
            outcome_text = (
                f"Round return: {lev_return:+.2f}% (after leverage). "
                "Hint: if risk is High/Extreme, consider lowering leverage or increasing Stablecoin."
            )

        team_data["crypto_portfolio"] = {
            "equity": float(equity),
            "last_return_pct": float(lev_return),
            "total_return_pct": float(total_return),
            "allocations": allocations,
            "leverage": float(leverage),
            "risk_exposure": float(risk_exposure),
            "risk_label": exposure_label,
            "liquidations": int(liquidations),
            "explain": simple_explain,
            "outcome": outcome_text,
        }


# ============================================================================
# ROUND HISTORY SNAPSHOTS
# ============================================================================

def _store_round_snapshot(join_code: str, round_num: int):
    """
    Store a snapshot of current round data for history tracking.
    Called AFTER round processing but BEFORE advancing to next round.
    IMPORTANT: Only stores if round_num >= 1 (skips Round 0)
    """
    if round_num == 0:
        return

    game = get_game_session(join_code)
    if not game:
        return

    for _, team_data in game.get("teams", {}).items():
        team_data.setdefault("round_history", {})

        if str(round_num) in team_data["round_history"]:
            continue

        decisions = team_data.get("decisions", {}) or {}

        if game["game_type"] == "build_country":
            metrics = team_data.get("metrics", {
                "gdp": 100.0,
                "employment": 75.0,
                "inequality": 50.0,
                "approval": 50.0,
                "debt": 0.0,
            })

            score = compute_build_country_score(team_data)

            team_data["round_history"][str(round_num)] = {
                "decisions": {
                    "tax_rate": decisions.get("tax_rate", 30),
                    "education_spending": decisions.get("education_spending", 25),
                    "infrastructure_spending": decisions.get("infrastructure_spending", 25),
                    "climate_policy": decisions.get("climate_policy", "Moderate"),
                },
                "metrics": {
                    "gdp": float(metrics.get("gdp", 100.0)),
                    "employment": float(metrics.get("employment", 75.0)),
                    "inequality": float(metrics.get("inequality", 50.0)),
                    "approval": float(metrics.get("approval", 50.0)),
                    "debt": float(metrics.get("debt", 0.0)),
                },
                "fiscal": dict(team_data.get("fiscal", {}) or {}),
                "score": float(score),
            }

        elif game["game_type"] == "beat_market":
            portfolio = team_data.get("portfolio", {})
            portfolio_value = team_data.get("portfolio_value", {})
            returns = float(portfolio_value.get("returns", 0.0))
            risk = float(portfolio_value.get("risk", 50.0))
            score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns

            team_data["round_history"][str(round_num)] = {
                "decisions": {
                    "cash_pct": portfolio.get("cash_pct", 25),
                    "shares_pct": portfolio.get("shares_pct", 25),
                    "crypto_pct": portfolio.get("crypto_pct", 25),
                    "bonds_pct": portfolio.get("bonds_pct", 25)
                },
                "portfolio_value": {
                    "value": portfolio_value.get("value", 1000000),
                    "returns": returns,
                    "risk": risk,
                    "esg": portfolio_value.get("esg", 50.0)
                },
                "score": score
            }

        elif game["game_type"] == "crypto_crash":
            cp = team_data.get("crypto_portfolio", {})
            alloc = decisions.get("allocations", {}) if isinstance(decisions.get("allocations", {}), dict) else {}

            team_data["round_history"][str(round_num)] = {
                "decisions": {
                    "allocations": {
                        "btc": alloc.get("btc", 40),
                        "eth": alloc.get("eth", 30),
                        "doge": alloc.get("doge", 20),
                        "stable": alloc.get("stable", 10)
                    },
                    "leverage": decisions.get("leverage", 1)
                },
                "crypto_portfolio": {
                    "equity": cp.get("equity", 1000.0),
                    "last_return_pct": cp.get("last_return_pct", 0.0),
                    "total_return_pct": cp.get("total_return_pct", 0.0),
                    "risk_exposure": cp.get("risk_exposure", 0.0),
                    "risk_label": cp.get("risk_label", "Low"),
                    "liquidations": cp.get("liquidations", 0)
                },
                "score": float(cp.get("equity", 1000.0))
            }

    games = load_json(GAMES_FILE)
    games[join_code] = game
    save_json(GAMES_FILE, games)


def advance_round(join_code: str):
    """
    Advance to next round:
    1) Auto-submit missing decisions (use previous round's choices)
    2) Process current round outcomes
    3) Store round history snapshot (only if round >= 1)
    4) Generate next scenario/event/indicators + narrative hints
    5) Persist updated state
    """
    game = get_game_session(join_code)
    if not game:
        return

    current_round = game.get("current_round", 1)

    # Auto-submit missing decisions before processing
    for _, team_data in game.get("teams", {}).items():
        decision_saved_round = team_data.get("decision_saved_round", 0)

        if decision_saved_round != current_round:
            game_type = game.get("game_type")

            if game_type == "build_country":
                prev = team_data.get("decisions", {}) or {}
                team_data["decisions"] = {
                    "tax_rate": prev.get("tax_rate", 30),
                    "education_spending": prev.get("education_spending", 25),
                    "infrastructure_spending": prev.get("infrastructure_spending", 25),
                    "climate_policy": prev.get("climate_policy", "Moderate")
                }
                team_data["decision_saved_round"] = current_round
                team_data["auto_submitted"] = True

            elif game_type == "beat_market":
                prev = team_data.get("portfolio", {}) or {}
                team_data["portfolio"] = {
                    "cash_pct": prev.get("cash_pct", 25),
                    "shares_pct": prev.get("shares_pct", 25),
                    "crypto_pct": prev.get("crypto_pct", 25),
                    "bonds_pct": prev.get("bonds_pct", 25)
                }
                team_data["decision_saved_round"] = current_round
                team_data["auto_submitted"] = True

            elif game_type == "crypto_crash":
                prev = team_data.get("decisions", {}) or {}
                prev_alloc = prev.get("allocations", {}) if isinstance(prev.get("allocations", {}), dict) else {}
                team_data["decisions"] = {
                    "allocations": {
                        "btc": prev_alloc.get("btc", 40),
                        "eth": prev_alloc.get("eth", 30),
                        "doge": prev_alloc.get("doge", 20),
                        "stable": prev_alloc.get("stable", 10)
                    },
                    "leverage": prev.get("leverage", 1)
                }
                team_data["decision_saved_round"] = current_round
                team_data["auto_submitted"] = True

    # Save auto-submitted decisions
    games = load_json(GAMES_FILE)
    games[join_code] = game
    save_json(GAMES_FILE, games)

    # Process current round
    process_current_round(join_code)

    # Store snapshot after processing
    _store_round_snapshot(join_code, current_round)

    # Reload after processing
    game = get_game_session(join_code)
    if not game:
        return

    game.setdefault("game_state", {})

    if game["game_type"] == "build_country":
        scenarios = [
            {
                "name": "🌪️ Global Recession",
                "description": (
                    "A worldwide recession hits. Exports fall, unemployment rises, and investors pull back. "
                    "Tax revenue shrinks while pressure for support grows. "
                    "Hint: protect jobs, prioritize targeted relief, keep debt sustainable."
                )
            },
            {
                "name": "💡 Tech Boom",
                "description": (
                    "Innovation boosts productivity and attracts investment. "
                    "Wages rise, but inequality may grow. "
                    "Hint: invest in education/infrastructure; watch inequality and fiscal balance."
                )
            },
            {
                "name": "🌋 Natural Disaster",
                "description": (
                    "Infrastructure is damaged and production disrupted. "
                    "Hint: rebuild, but deficits can surge—manage debt carefully."
                )
            },
            {
                "name": "🌍 Climate Crisis",
                "description": (
                    "Extreme weather harms health, crops, and long-term growth. "
                    "Hint: climate action helps credibility but has fiscal costs."
                )
            },
            {
                "name": "📈 Trade Agreement",
                "description": (
                    "New trade deal opens markets. Exports surge, local firms face competition. "
                    "Hint: invest in logistics and workforce skills."
                )
            },
            {
                "name": "👥 Social Movement",
                "description": (
                    "Protests demand equality and better services. Trust falls, but reforms can help long-term. "
                    "Hint: reduce inequality without exploding the deficit."
                )
            },
        ]
        game["game_state"]["current_scenario"] = random.choice(scenarios)

    elif game["game_type"] == "beat_market":
        events = [
            {
                "name": "📈 Bull Market Rally",
                "description": (
                    "Markets surge with optimism. Stocks rise fast, speculation increases. "
                    "Hint: ride momentum, diversify, manage risk."
                )
            },
            {
                "name": "🏦 Interest Rate Hike",
                "description": (
                    "Rates rise to fight inflation. Borrowing costs increase, slowing demand. "
                    "Hint: tilt defensive and reduce risk."
                )
            },
            {
                "name": "💥 Company Scandal",
                "description": (
                    "A major firm is caught in fraud. Confidence drops and investors panic-sell. "
                    "Hint: diversify and avoid concentration."
                )
            },
            {
                "name": "🚀 Tech Breakthrough",
                "description": (
                    "AI breakthrough reshapes the tech landscape. Tech rallies but disruption risk rises. "
                    "Hint: avoid hype without fundamentals."
                )
            },
            {
                "name": "📉 Market Correction",
                "description": (
                    "Markets drop sharply as traders take profits. "
                    "Hint: avoid emotional selling; manage drawdowns."
                )
            },
            {
                "name": "🌍 Climate Regulation",
                "description": (
                    "Strict climate laws raise costs for polluters and boost renewables. "
                    "Hint: rebalance toward transition winners."
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

        # Sentiment
        if indicators["sentiment"] < 35:
            sentiment_text = "Fear dominates the market. Traders are pessimistic and selling pressure is rising."
            sentiment_hint = "Reduce risk: more Stablecoin, less leverage, or wait for stability."
        elif indicators["sentiment"] > 65:
            sentiment_text = "Optimism is high. Traders believe prices will keep rising."
            sentiment_hint = "Enjoy gains, but consider taking profits and avoid extreme leverage."
        else:
            sentiment_text = "Sentiment is mixed. Traders are uncertain and waiting for direction."
            sentiment_hint = "Diversify across BTC/ETH and keep some Stablecoin."

        # Volume
        if indicators["volume"] > 75:
            volume_text = "Trading volume is extremely high — big players may be moving money."
            volume_hint = "High volume can mean breakout OR crash. Use lower leverage if unsure."
        elif indicators["volume"] < 40:
            volume_text = "Trading volume is weak — the market is thin and jumpy."
            volume_hint = "Thin markets crash easily. Hold more Stablecoin and avoid leverage."
        else:
            volume_text = "Trading volume is normal — steady but cautious activity."
            volume_hint = "Follow the trend, but keep protection (some Stablecoin)."

        # Hype
        if indicators["hype"] > 75:
            hype_text = "Social media hype is exploding. Meme coins can spike — and crash — fast."
            hype_hint = "Be careful with DOGE + leverage. That combo is highest risk."
        elif indicators["hype"] < 40:
            hype_text = "Hype is low. The market is quiet and attention is fading."
            hype_hint = "Low hype means fewer pumps, but also less buying demand."
        else:
            hype_text = "Hype is moderate. Speculation exists, but it hasn't reached mania levels."
            hype_hint = "Balanced conditions: focus on BTC/ETH and manage leverage."

        market_story = f"{sentiment_text} {volume_text} {hype_text}"

        game["game_state"]["indicators"] = indicators
        game["game_state"]["market_story"] = market_story
        game["game_state"]["indicator_notes"] = {
            "sentiment": {"text": sentiment_text, "hint": sentiment_hint},
            "volume": {"text": volume_text, "hint": volume_hint},
            "hype": {"text": hype_text, "hint": hype_hint},
        }

    update_game_session(join_code, {
        "current_round": game.get("current_round", 0) + 1,
        "round_locked": False,
        "round_timer_end": None,
        "game_state": game["game_state"]
    })


# ============================================================================
# EXCEL EXPORT
# ============================================================================

def export_game_results_to_excel(join_code: str):
    """
    Export complete game results to Excel format with multiple sheets.
    Returns: BytesIO object containing Excel file
    """
    import pandas as pd
    from io import BytesIO

    game = get_game_session(join_code)
    if not game:
        return None

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        # Sheet 1: Game Summary
        game_summary = {
            "Game Type": [game.get("game_type", "Unknown")],
            "Admin": [game.get("admin_name", "Unknown")],
            "Created At": [game.get("created_at", "Unknown")],
            "Status": [game.get("status", "Unknown")],
            "Total Rounds": [game.get("settings", {}).get("num_rounds", 0)],
            "Current Round": [game.get("current_round", 0)],
            "Number of Teams": [len(game.get("teams", {}))]
        }
        pd.DataFrame(game_summary).to_excel(writer, sheet_name="Game Summary", index=False)

        # Sheet 2: Final Scores
        final_scores = []
        for team_name, team_data in game.get("teams", {}).items():
            if game["game_type"] == "build_country":
                metrics = team_data.get("metrics", {}) or {}
                fiscal = team_data.get("fiscal", {}) or {}

                score = compute_build_country_score(team_data)

                final_scores.append({
                    "Team": team_name,
                    "Final Score": round(score, 2),
                    "GDP": round(float(metrics.get("gdp", 100.0)), 2),
                    "Employment": round(float(metrics.get("employment", 75.0)), 2),
                    "Inequality": round(float(metrics.get("inequality", 50.0)), 2),
                    "Approval": round(float(metrics.get("approval", 50.0)), 2),
                    "Debt (%GDP)": round(float(metrics.get("debt", 0.0)), 2),
                    "Deficit (%GDP)": round(float(fiscal.get("deficit_pct_gdp", 0.0)), 2),
                    "Revenue (%GDP)": round(float(fiscal.get("revenue_pct_gdp", 0.0)), 2),
                    "Spend (%GDP)": round(float(fiscal.get("total_spend_pct_gdp", 0.0)), 2),
                })

            elif game["game_type"] == "beat_market":
                pv = team_data.get("portfolio_value", {}) or {}
                returns = float(pv.get("returns", 0))
                risk = float(pv.get("risk", 50))
                score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns
                final_scores.append({
                    "Team": team_name,
                    "Risk-Adj Score": round(score, 2),
                    "Portfolio Value": round(float(pv.get("value", 1000000)), 2),
                    "Returns (%)": round(returns, 2),
                    "Risk": round(risk, 2)
                })

            elif game["game_type"] == "crypto_crash":
                cp = team_data.get("crypto_portfolio", {}) or {}
                final_scores.append({
                    "Team": team_name,
                    "Final Equity": round(float(cp.get("equity", 1000)), 2),
                    "Total Return (%)": round(float(cp.get("total_return_pct", 0)), 2),
                    "Risk Exposure": round(float(cp.get("risk_exposure", 0)), 2),
                    "Risk Label": cp.get("risk_label", "Low"),
                    "Leverage": cp.get("leverage", 1),
                    "Liquidations": cp.get("liquidations", 0)
                })

        if final_scores:
            df_final = pd.DataFrame(final_scores)
            df_final = df_final.sort_values(by=df_final.columns[1], ascending=False)
            df_final.insert(0, "Rank", range(1, len(df_final) + 1))
            df_final.to_excel(writer, sheet_name="Final Scores", index=False)

        # Sheet 3-N: Round-by-Round Details for Each Team
        for team_name, team_data in game.get("teams", {}).items():
            round_history = team_data.get("round_history", {}) or {}
            if not round_history:
                continue

            rows = []
            for round_num in sorted([int(r) for r in round_history.keys()]):
                rd = round_history.get(str(round_num), {}) or {}

                if game["game_type"] == "build_country":
                    d = rd.get("decisions", {}) or {}
                    m = rd.get("metrics", {}) or {}
                    f = rd.get("fiscal", {}) or {}
                    rows.append({
                        "Round": round_num,
                        "Tax Rate (slider)": d.get("tax_rate", 30),
                        "Education (slider)": d.get("education_spending", 25),
                        "Infrastructure (slider)": d.get("infrastructure_spending", 25),
                        "Climate Policy": d.get("climate_policy", "Moderate"),
                        "GDP": round(float(m.get("gdp", 100.0)), 2),
                        "Employment": round(float(m.get("employment", 75.0)), 2),
                        "Inequality": round(float(m.get("inequality", 50.0)), 2),
                        "Approval": round(float(m.get("approval", 50.0)), 2),
                        "Debt (%GDP)": round(float(m.get("debt", 0.0)), 2),
                        "Deficit (%GDP)": round(float(f.get("deficit_pct_gdp", 0.0)), 2),
                        "Score": round(float(rd.get("score", 0.0)), 2),
                    })

                elif game["game_type"] == "beat_market":
                    d = rd.get("decisions", {}) or {}
                    pv = rd.get("portfolio_value", {}) or {}
                    rows.append({
                        "Round": round_num,
                        "Cash (%)": d.get("cash_pct", 25),
                        "Shares (%)": d.get("shares_pct", 25),
                        "Crypto (%)": d.get("crypto_pct", 25),
                        "Bonds (%)": d.get("bonds_pct", 25),
                        "Portfolio Value": round(float(pv.get("value", 1000000)), 2),
                        "Returns (%)": round(float(pv.get("returns", 0.0)), 2),
                        "Risk": round(float(pv.get("risk", 50.0)), 2),
                        "Risk-Adj Score": round(float(rd.get("score", 0.0)), 2)
                    })

                elif game["game_type"] == "crypto_crash":
                    d = rd.get("decisions", {}) or {}
                    alloc = d.get("allocations", {}) or {}
                    cp = rd.get("crypto_portfolio", {}) or {}
                    rows.append({
                        "Round": round_num,
                        "BTC (%)": alloc.get("btc", 40),
                        "ETH (%)": alloc.get("eth", 30),
                        "DOGE (%)": alloc.get("doge", 20),
                        "Stable (%)": alloc.get("stable", 10),
                        "Leverage": d.get("leverage", 1),
                        "Equity": round(float(cp.get("equity", 1000.0)), 2),
                        "Round Return (%)": round(float(cp.get("last_return_pct", 0.0)), 2),
                        "Risk Label": cp.get("risk_label", "Low"),
                        "Liquidations": cp.get("liquidations", 0),
                    })

            if rows:
                df_team = pd.DataFrame(rows)
                sheet_name = team_name[:28] + "..." if len(team_name) > 31 else team_name
                sheet_name = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in sheet_name)
                df_team.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    return output


# ============================================================================
# USER SESSION MANAGEMENT
# ============================================================================

def init_user_session():
    """Initialize user session state."""
    if "user_type" not in st.session_state:
        st.session_state.user_type = None

    if "join_code" not in st.session_state:
        st.session_state.join_code = None

    if "team_name" not in st.session_state:
        st.session_state.team_name = None

    if "admin_name" not in st.session_state:
        st.session_state.admin_name = None


def set_user_as_admin(admin_name: str, join_code: str):
    """Set current user as admin."""
    st.session_state.user_type = "admin"
    st.session_state.admin_name = admin_name
    st.session_state.join_code = join_code.upper()
    st.session_state.team_name = None


def set_user_as_team(team_name: str, join_code: str):
    """Set current user as team"""
    st.session_state.user_type = "team"
    st.session_state.team_name = team_name
    st.session_state.join_code = join_code.upper()
    st.session_state.admin_name = None


def clear_user_session():
    """Clear user session"""
    st.session_state.user_type = None
    st.session_state.join_code = None
    st.session_state.team_name = None
    st.session_state.admin_name = None


def is_admin() -> bool:
    """Check if current user is admin."""
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
