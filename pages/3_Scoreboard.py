"""
Scoreboard Page - Live view of all team standings and scores
"""

import streamlit as st
import shared_state as state
import time

# ✅ add this dependency: streamlit-autorefresh
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Scoreboard",
    page_icon="📊",
    layout="wide"
)

# Initialize
state.init_user_session()

# Auto-refresh every 3 seconds (works even when game is finished)
st_autorefresh(interval=3000, key="scoreboard_refresh")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Poppins:wght@600;700&display=swap');

    .main {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ff88;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }

    .scoreboard-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #00ff88;
        border-radius: 16px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
    }

    .rank-1 {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        border: 3px solid #ffd700;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
    }

    .rank-2 {
        background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
        border: 3px solid #c0c0c0;
        box-shadow: 0 0 20px rgba(192, 192, 192, 0.3);
    }

    .rank-3 {
        background: linear-gradient(135deg, #cd7f32 0%, #e9a76a 100%);
        border: 3px solid #cd7f32;
        box-shadow: 0 0 20px rgba(205, 127, 50, 0.3);
    }

    .metric-display {
        text-align: center;
        padding: 15px;
        background: rgba(0, 255, 136, 0.1);
        border-radius: 12px;
        margin: 10px 0;
    }

    .metric-value {
        font-size: 32px;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
        color: #00ff88;
    }

    .metric-label {
        font-size: 14px;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .team-name-display {
        font-size: 36px;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SCOREBOARD DISPLAY FUNCTIONS
# ============================================================================

def show_build_country_scoreboard(game):
    if not game.get("teams"):
        st.info("⏳ Waiting for teams to join...")
        return

    current_round = game.get("current_round", 1)
    scores = []
    waiting_teams = []

    for team_name, team_data in game["teams"].items():
        # Only show teams that have saved their decision for this round
        decision_saved_round = team_data.get("decision_saved_round", 0)
        if decision_saved_round != current_round:
            waiting_teams.append(team_name)
            continue

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

        scores.append({
            "team": team_name,
            "score": score,
            "gdp": metrics.get("gdp", 100),
            "employment": metrics.get("employment", 75),
            "inequality": metrics.get("inequality", 50),
            "approval": metrics.get("approval", 50),
        })

    # Show waiting teams
    if waiting_teams:
        st.markdown(f"⏳ **Waiting for decisions:** {', '.join(waiting_teams)}")
        st.markdown("---")

    scores.sort(key=lambda x: x["score"], reverse=True)

    for rank, data in enumerate(scores, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        card_class = f"rank-{rank}" if rank <= 3 else "scoreboard-card"
        name_color = "#0f2027" if rank <= 3 else "#00ff88"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:48px;">{medal}</span>
                    <span class="team-name-display" style="color:{name_color};">{data['team']}</span>
                </div>
                <div class="metric-value" style="color:{name_color};">{data['score']:.1f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(4)
        with cols[0]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{data['gdp']:.1f}</div>
                <div class="metric-label">💰 GDP</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{data['employment']:.1f}%</div>
                <div class="metric-label">👷 Employment</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{data['inequality']:.1f}</div>
                <div class="metric-label">⚖️ Inequality</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{data['approval']:.1f}%</div>
                <div class="metric-label">❤️ Approval</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

def show_beat_market_scoreboard(game):
    if not game.get("teams"):
        st.info("⏳ Waiting for teams to join...")
        return

    esg_mode = bool(game.get("settings", {}).get("esg_mode"))
    current_round = game.get("current_round", 1)

    scores = []
    waiting_teams = []

    for team_name, team_data in game["teams"].items():
        # Only show teams that have saved their decision for this round
        decision_saved_round = team_data.get("decision_saved_round", 0)
        if decision_saved_round != current_round:
            waiting_teams.append(team_name)
            continue

        portfolio = team_data.get("portfolio_value", {
            "value": 1_000_000,
            "returns": 0.0,
            "risk": 50.0,
            "esg": 50.0
        })

        returns = float(portfolio.get("returns", 0.0))
        risk = float(portfolio.get("risk", 50.0))
        risk_adj_score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns

        scores.append({
            "team": team_name,
            "score": risk_adj_score,
            "value": float(portfolio.get("value", 1_000_000)),
            "returns": returns,
            "risk": risk,
            "esg": float(portfolio.get("esg", 50.0)),
        })

    # Show waiting teams
    if waiting_teams:
        st.markdown(f"⏳ **Waiting for decisions:** {', '.join(waiting_teams)}")
        st.markdown("---")

    scores.sort(key=lambda x: x["score"], reverse=True)

    for rank, data in enumerate(scores, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        card_class = f"rank-{rank}" if rank <= 3 else "scoreboard-card"
        name_color = "#0f2027" if rank <= 3 else "#00ff88"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:48px;">{medal}</span>
                    <span class="team-name-display" style="color:{name_color};">{data['team']}</span>
                </div>
                <div class="metric-value" style="color:{name_color};">{data['score']:.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(5 if esg_mode else 4)

        with cols[0]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">${data['value']:,.0f}</div>
                <div class="metric-label">💼 VALUE</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            returns_color = "#00ff88" if data["returns"] >= 0 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{returns_color};">{data['returns']:+.1f}%</div>
                <div class="metric-label">📈 RETURNS</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            risk_color = "#ff4757" if data["risk"] > 70 else "#ffa502" if data["risk"] > 40 else "#00ff88"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{risk_color};">{data['risk']:.0f}/100</div>
                <div class="metric-label">⚠️ RISK</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[3]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{data['score']:.2f}</div>
                <div class="metric-label">🎯 RISK-ADJ</div>
            </div>
            """, unsafe_allow_html=True)

        if esg_mode:
            with cols[4]:
                esg_color = "#00ff88" if data["esg"] > 70 else "#ffa502" if data["esg"] > 40 else "#ff4757"
                st.markdown(f"""
                <div class="metric-display">
                    <div class="metric-value" style="color:{esg_color};">{data['esg']:.0f}/100</div>
                    <div class="metric-label">🌱 ESG</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

def show_crypto_crash_scoreboard(game):
    if not game.get("teams"):
        st.info("⏳ Waiting for teams to join...")
        return

    current_round = game.get("current_round", 1)
    scores = []
    waiting_teams = []

    for team_name, team_data in game["teams"].items():
        # Only show teams that have saved their decision for this round
        decision_saved_round = team_data.get("decision_saved_round", 0)
        if decision_saved_round != current_round:
            waiting_teams.append(team_name)
            continue

        performance = team_data.get("performance", {
            "profit": 0.0,
            "risk_score": 50.0,
            "decisions_correct": 0,
            "total_decisions": 1
        })

        profit = float(performance.get("profit", 0.0))
        risk_score = float(performance.get("risk_score", 50.0))
        correct = int(performance.get("decisions_correct", 0))
        total = int(performance.get("total_decisions", 1)) or 1

        risk_bonus = (100.0 - risk_score) / 10.0 if profit > 0 else 0.0
        accuracy = (correct / total) * 100.0
        final_score = profit + risk_bonus + (accuracy / 2.0)

        scores.append({
            "team": team_name,
            "score": final_score,
            "profit": profit,
            "risk": risk_score,
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        })

    # Show waiting teams
    if waiting_teams:
        st.markdown(f"⏳ **Waiting for decisions:** {', '.join(waiting_teams)}")
        st.markdown("---")

    scores.sort(key=lambda x: x["score"], reverse=True)

    for rank, data in enumerate(scores, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        card_class = f"rank-{rank}" if rank <= 3 else "scoreboard-card"
        name_color = "#0f2027" if rank <= 3 else "#00ff88"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:48px;">{medal}</span>
                    <span class="team-name-display" style="color:{name_color};">{data['team']}</span>
                </div>
                <div class="metric-value" style="color:{name_color};">{data['score']:.1f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(4)
        with cols[0]:
            profit_color = "#00ff88" if data["profit"] >= 0 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{profit_color};">{data['profit']:+.1f}%</div>
                <div class="metric-label">💰 PROFIT</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[1]:
            risk_color = "#00ff88" if data["risk"] < 40 else "#ffa502" if data["risk"] < 70 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{risk_color};">{data['risk']:.0f}/100</div>
                <div class="metric-label">⚠️ RISK</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[2]:
            acc_color = "#00ff88" if data["accuracy"] > 60 else "#ffa502" if data["accuracy"] > 40 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{acc_color};">{data['accuracy']:.0f}%</div>
                <div class="metric-label">🎯 ACCURACY</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{data['correct']}/{data['total']}</div>
                <div class="metric-label">✅ CORRECT</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# MAIN
# ============================================================================

game = None

# Persist which game code the scoreboard is watching
if st.session_state.get("join_code"):
    st.session_state["scoreboard_code"] = st.session_state["join_code"]

# If no game code set, try to find the most recent running game
if not st.session_state.get("scoreboard_code"):
    all_games = state.get_all_game_sessions()

    # Filter to only running games and sort by created_at (most recent first)
    running_games = []
    for code, g in all_games.items():
        if g.get("status") == "running":
            running_games.append((code, g, g.get("created_at", "")))

    # Sort by created_at descending (most recent first)
    running_games.sort(key=lambda x: x[2], reverse=True)

    if len(running_games) >= 1:
        # Auto-select the most recent running game
        st.session_state["scoreboard_code"] = running_games[0][0]
    else:
        # No running games
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1>📊 LIVE SCOREBOARD</h1>
            <p style="color: #aaa; font-size: 18px;">
                No active games found. Create a game from the Home page.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

# Always re-fetch game from shared storage
if st.session_state.get("scoreboard_code"):
    game = state.get_game_session(st.session_state["scoreboard_code"])

if not game:
    st.session_state["scoreboard_code"] = None
    st.rerun()

# Header
game_names = {
    "build_country": "🌍 Build a Country",
    "beat_market": "📈 Beat the Market",
    "crypto_crash": "₿ Crypto Crash or Boom?"
}

st.markdown(f"""
<div style="text-align: center; padding: 20px;">
    <h1 style="font-size: 56px;">📊 LIVE SCOREBOARD</h1>
    <h2>{game_names.get(game['game_type'], game['game_type'])}</h2>
    <p style="color: #00ff88; font-size: 20px;">
        Round {game['current_round']} / {game['settings']['num_rounds']}
        | Status: {game['status'].upper()}
    </p>
</div>
""", unsafe_allow_html=True)

if game.get("status") == "finished":
    st.success("🏁 Game finished — final results below.")

# Scoreboard content
if game["game_type"] == "build_country":
    show_build_country_scoreboard(game)
elif game["game_type"] == "beat_market":
    show_beat_market_scoreboard(game)
elif game["game_type"] == "crypto_crash":
    show_crypto_crash_scoreboard(game)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px;">
    <p style="color: #00ff88; font-size: 14px;">
        🔄 Auto-refreshing every 3 seconds | Last update: {time.strftime("%H:%M:%S")}
    </p>
</div>
""", unsafe_allow_html=True)
