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


def _store_round_snapshot(join_code: str, round_num: int):
    """
    ✅ FIXED: Store a snapshot of current round data for history tracking.
    Called AFTER round processing but BEFORE advancing to next round.
    
    IMPORTANT: Only stores if round_num >= 1 (skips Round 0)
    FIXED: Removed the decision_saved_round check that was skipping auto-submitted teams
    """
    # Don't store Round 0 (game hasn't started yet)
    if round_num == 0:
        return
    
    game = get_game_session(join_code)
    if not game:
        return
    
    for team_name, team_data in game.get("teams", {}).items():
        if "round_history" not in team_data:
            team_data["round_history"] = {}
        
        # Only store if not already stored for this round
        if str(round_num) in team_data["round_history"]:
            continue
        
        # ✅ REMOVED: The check that was preventing auto-submitted teams from being stored
        # Old code: if decision_saved_round < round_num: continue
        
        decisions = team_data.get("decisions", {})
        
        if game["game_type"] == "build_country":
            metrics = team_data.get("metrics", {
                "gdp": 100.0,
                "employment": 75.0,
                "inequality": 50.0,
                "approval": 50.0
            })
            score = (
                metrics.get("gdp", 100) * 0.3 +
                metrics.get("employment", 75) * 0.25 +
                (100 - metrics.get("inequality", 50)) * 0.25 +
                metrics.get("approval", 50) * 0.2
            )
            
            # Deep copy to prevent reference issues
            team_data["round_history"][str(round_num)] = {
                "decisions": {
                    "tax_rate": decisions.get("tax_rate", 30),
                    "education_spending": decisions.get("education_spending", 25),
                    "infrastructure_spending": decisions.get("infrastructure_spending", 25),
                    "climate_policy": decisions.get("climate_policy", "Moderate")
                },
                "metrics": {
                    "gdp": metrics.get("gdp", 100.0),
                    "employment": metrics.get("employment", 75.0),
                    "inequality": metrics.get("inequality", 50.0),
                    "approval": metrics.get("approval", 50.0)
                },
                "score": score
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
            alloc = decisions.get("allocations", {})
            
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
    
    # Save back
    games = load_json(GAMES_FILE)
    games[join_code] = game
    save_json(GAMES_FILE, games)


def advance_round(join_code: str):
    """
    Advance to next round:
    1) Auto-submit missing decisions (use previous round's choices)
    2) Process current round outcomes
    3) ✅ STORE ROUND HISTORY SNAPSHOT (only if round >= 1)
    4) Generate next scenario/event/indicators + narrative hints
    5) Persist updated state
    """
    game = get_game_session(join_code)
    if not game:
        return

    # Auto-submit missing decisions before processing
    current_round = game.get("current_round", 1)
    
    for team_name, team_data in game.get("teams", {}).items():
        decision_saved_round = team_data.get("decision_saved_round", 0)
        
        # If team hasn't saved decision for current round
        if decision_saved_round != current_round:
            # Get their previous decisions (or use defaults)
            game_type = game.get("game_type")
            
            if game_type == "build_country":
                prev_decisions = team_data.get("decisions", {})
                default_decisions = {
                    "tax_rate": prev_decisions.get("tax_rate", 30),
                    "education_spending": prev_decisions.get("education_spending", 25),
                    "infrastructure_spending": prev_decisions.get("infrastructure_spending", 25),
                    "climate_policy": prev_decisions.get("climate_policy", "Moderate")
                }
                team_data["decisions"] = default_decisions
                team_data["decision_saved_round"] = current_round
                team_data["auto_submitted"] = True
                
            elif game_type == "beat_market":
                prev_portfolio = team_data.get("portfolio", {})
                default_portfolio = {
                    "cash_pct": prev_portfolio.get("cash_pct", 25),
                    "shares_pct": prev_portfolio.get("shares_pct", 25),
                    "crypto_pct": prev_portfolio.get("crypto_pct", 25),
                    "bonds_pct": prev_portfolio.get("bonds_pct", 25)
                }
                team_data["portfolio"] = default_portfolio
                team_data["decision_saved_round"] = current_round
                team_data["auto_submitted"] = True
                
            elif game_type == "crypto_crash":
                prev_decisions = team_data.get("decisions", {})
                prev_alloc = prev_decisions.get("allocations", {}) if isinstance(prev_decisions.get("allocations"), dict) else {}
                
                default_decisions = {
                    "allocations": {
                        "btc": prev_alloc.get("btc", 40),
                        "eth": prev_alloc.get("eth", 30),
                        "doge": prev_alloc.get("doge", 20),
                        "stable": prev_alloc.get("stable", 10)
                    },
                    "leverage": prev_decisions.get("leverage", 1)
                }
                team_data["decisions"] = default_decisions
                team_data["decision_saved_round"] = current_round
                team_data["auto_submitted"] = True

    # Save auto-submitted decisions
    games = load_json(GAMES_FILE)
    games[join_code] = game
    save_json(GAMES_FILE, games)

    # Process current round (scoreboard)
    process_current_round(join_code)

    # ✅ FIXED: Store round history AFTER processing, BEFORE advancing (skips Round 0)
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
    """Build-country toy mechanics with scenario shock."""
    scenario = game.get("game_state", {}).get("current_scenario", {})
    scenario_name = (scenario.get("name") or "").lower()

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
    UPDATED CRYPTO GAME (student-friendly):
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
    
    # Create Excel writer
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
        df_summary = pd.DataFrame(game_summary)
        df_summary.to_excel(writer, sheet_name="Game Summary", index=False)
        
        # Sheet 2: Final Scores
        final_scores = []
        for team_name, team_data in game.get("teams", {}).items():
            if game["game_type"] == "build_country":
                metrics = team_data.get("metrics", {})
                score = (
                    metrics.get("gdp", 100) * 0.3 +
                    metrics.get("employment", 75) * 0.25 +
                    (100 - metrics.get("inequality", 50)) * 0.25 +
                    metrics.get("approval", 50) * 0.2
                )
                final_scores.append({
                    "Team": team_name,
                    "Final Score": round(score, 2),
                    "GDP": round(metrics.get("gdp", 100), 2),
                    "Employment": round(metrics.get("employment", 75), 2),
                    "Inequality": round(metrics.get("inequality", 50), 2),
                    "Approval": round(metrics.get("approval", 50), 2)
                })
            
            elif game["game_type"] == "beat_market":
                pv = team_data.get("portfolio_value", {})
                returns = pv.get("returns", 0)
                risk = pv.get("risk", 50)
                score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns
                final_scores.append({
                    "Team": team_name,
                    "Risk-Adj Score": round(score, 2),
                    "Portfolio Value": round(pv.get("value", 1000000), 2),
                    "Returns (%)": round(returns, 2),
                    "Risk": round(risk, 2)
                })
            
            elif game["game_type"] == "crypto_crash":
                cp = team_data.get("crypto_portfolio", {})
                final_scores.append({
                    "Team": team_name,
                    "Final Equity": round(cp.get("equity", 1000), 2),
                    "Total Return (%)": round(cp.get("total_return_pct", 0), 2),
                    "Risk Exposure": round(cp.get("risk_exposure", 0), 2),
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
            round_history = team_data.get("round_history", {})
            
            if not round_history:
                continue
            
            round_data_list = []
            
            for round_num in sorted([int(r) for r in round_history.keys()]):
                round_data = round_history.get(str(round_num), {})
                
                if game["game_type"] == "build_country":
                    decisions = round_data.get("decisions", {})
                    metrics = round_data.get("metrics", {})
                    round_data_list.append({
                        "Round": round_num,
                        "Tax Rate (%)": decisions.get("tax_rate", 30),
                        "Education (%)": decisions.get("education_spending", 25),
                        "Infrastructure (%)": decisions.get("infrastructure_spending", 25),
                        "Climate Policy": decisions.get("climate_policy", "Moderate"),
                        "GDP": round(metrics.get("gdp", 100), 2),
                        "Employment (%)": round(metrics.get("employment", 75), 2),
                        "Inequality": round(metrics.get("inequality", 50), 2),
                        "Approval (%)": round(metrics.get("approval", 50), 2),
                        "Score": round(round_data.get("score", 0), 2)
                    })
                
                elif game["game_type"] == "beat_market":
                    decisions = round_data.get("decisions", {})
                    pv = round_data.get("portfolio_value", {})
                    round_data_list.append({
                        "Round": round_num,
                        "Cash (%)": decisions.get("cash_pct", 25),
                        "Shares (%)": decisions.get("shares_pct", 25),
                        "Crypto (%)": decisions.get("crypto_pct", 25),
                        "Bonds (%)": decisions.get("bonds_pct", 25),
                        "Portfolio Value": round(pv.get("value", 1000000), 2),
                        "Returns (%)": round(pv.get("returns", 0), 2),
                        "Risk": round(pv.get("risk", 50), 2),
                        "Risk-Adj Score": round(round_data.get("score", 0), 2)
                    })
                
                elif game["game_type"] == "crypto_crash":
                    decisions = round_data.get("decisions", {})
                    alloc = decisions.get("allocations", {})
                    cp = round_data.get("crypto_portfolio", {})
                    round_data_list.append({
                        "Round": round_num,
                        "BTC (%)": alloc.get("btc", 40),
                        "ETH (%)": alloc.get("eth", 30),
                        "DOGE (%)": alloc.get("doge", 20),
                        "Stable (%)": alloc.get("stable", 10),
                        "Leverage": decisions.get("leverage", 1),
                        "Equity": round(cp.get("equity", 1000), 2),
                        "Round Return (%)": round(cp.get("last_return_pct", 0), 2),
                        "Risk Label": cp.get("risk_label", "Low"),
                        "Liquidations": cp.get("liquidations", 0)
                    })
            
            if round_data_list:
                df_team = pd.DataFrame(round_data_list)
                # Sanitize sheet name (Excel limit: 31 chars, no special chars)
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