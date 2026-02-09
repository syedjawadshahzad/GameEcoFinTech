"""
Scoreboard Page - Live view of all team standings and scores
"""

import streamlit as st
import shared_state as state
import time

from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Scoreboard",
    page_icon="📊",
    layout="wide"
)

# Initialize
state.init_user_session()

# Auto-refresh every 3 seconds
st_autorefresh(interval=3000, key="scoreboard_refresh")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Poppins:wght@600;700&display=swap');.main {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ff88;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }.scoreboard-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #00ff88;
        border-radius: 16px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
    }.rank-1 {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        border: 3px solid #ffd700;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
    }.rank-2 {
        background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
        border: 3px solid #c0c0c0;
        box-shadow: 0 0 20px rgba(192, 192, 192, 0.3);
    }.rank-3 {
        background: linear-gradient(135deg, #cd7f32 0%, #e9a76a 100%);
        border: 3px solid #cd7f32;
        box-shadow: 0 0 20px rgba(205, 127, 50, 0.3);
    }.metric-display {
        text-align: center;
        padding: 15px;
        background: rgba(0, 255, 136, 0.1);
        border-radius: 12px;
        margin: 10px 0;
    }.metric-value {
        font-size: 32px;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
        color: #00ff88;
    }.metric-label {
        font-size: 14px;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }.team-name-display {
        font-size: 36px;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
        margin: 15px 0;
    }.round-history-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #00ff88;
    }.decision-item {
        background: rgba(255, 255, 255, 0.85);
        padding: 8px 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 14px;
        color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SCOREBOARD DISPLAY FUNCTIONS (DISPLAY ONLY - NO STORAGE)
# ============================================================================

def show_build_country_scoreboard(game):
    if not game.get("teams"):
        st.info("⏳ Waiting for teams to join...")
        return

    # Calculate current scores (USE SHARED scoring function)
    scores = []
    for team_name, team_data in game["teams"].items():
        score = float(state.compute_build_country_score(team_data))
        scores.append({
            "team": team_name,
            "score": score,
            "data": team_data
        })

    scores.sort(key=lambda x: x["score"], reverse=True)

    # Display rankings
    for rank, item in enumerate(scores, 1):
        team_name = item["team"]
        team_data = item["data"]
        score = item["score"]

        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        card_class = f"rank-{rank}" if rank <= 3 else "scoreboard-card"
        name_color = "#0f2027" if rank <= 3 else "#00ff88"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:48px;">{medal}</span>
                    <span class="team-name-display" style="color:{name_color};">{team_name}</span>
                </div>
                <div class="metric-value" style="color:{name_color};">{score:.1f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Current metrics (+ fiscal)
        metrics = team_data.get("metrics", {})
        fiscal = team_data.get("fiscal", {})

        cols = st.columns(6)
        with cols[0]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{float(metrics.get('gdp', 100)):.1f}</div>
                <div class="metric-label">💰 GDP</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{float(metrics.get('employment', 75)):.1f}%</div>
                <div class="metric-label">👷 Employment</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{float(metrics.get('inequality', 50)):.1f}</div>
                <div class="metric-label">⚖️ Inequality</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{float(metrics.get('approval', 50)):.1f}%</div>
                <div class="metric-label">❤️ Approval</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{float(metrics.get('debt', 0)):.0f}%</div>
                <div class="metric-label">🏦 Debt %GDP</div>
            </div>
            """, unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{float(fiscal.get('deficit_pct_gdp', 0)):+.1f}%</div>
                <div class="metric-label">📉 Deficit %GDP</div>
            </div>
            """, unsafe_allow_html=True)

        # Round History (now also show fiscal + debt if present)
        with st.expander(f"📊 {team_name} - Round History", expanded=False):
            round_history = team_data.get("round_history", {})
            if not round_history:
                st.info("No history available yet - play at least one round")
            else:
                sorted_rounds = sorted([int(r) for r in round_history.keys()])
                for round_num in sorted_rounds:
                    round_data = round_history.get(str(round_num), {})
                    if not round_data:
                        continue

                    decisions = round_data.get("decisions", {})
                    round_metrics = round_data.get("metrics", {})
                    round_fiscal = round_data.get("fiscal", {})
                    round_score = float(round_data.get("score", 0))

                    st.markdown(f"""
                    <div class="round-history-card">
                        <h4 style="color: #00ff88; margin: 0 0 10px 0;">Round {round_num} - Score: {round_score:.1f}</h4>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Decisions:**")
                        st.markdown(f"""
                        <div class="decision-item">💵 Tax Rate: {decisions.get('tax_rate', 30)}%</div>
                        <div class="decision-item">📚 Education (slider): {decisions.get('education_spending', 25)}</div>
                        <div class="decision-item">🏗️ Infrastructure (slider): {decisions.get('infrastructure_spending', 25)}</div>
                        <div class="decision-item">🌱 Climate: {decisions.get('climate_policy', 'Moderate')}</div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown("**Results:**")
                        st.markdown(f"""
                        <div class="decision-item">💰 GDP: {float(round_metrics.get('gdp', 100)):.1f}</div>
                        <div class="decision-item">👷 Employment: {float(round_metrics.get('employment', 75)):.1f}%</div>
                        <div class="decision-item">⚖️ Inequality: {float(round_metrics.get('inequality', 50)):.1f}</div>
                        <div class="decision-item">❤️ Approval: {float(round_metrics.get('approval', 50)):.1f}%</div>
                        <div class="decision-item">🏦 Debt %GDP: {float(round_metrics.get('debt', 0)):.0f}%</div>
                        <div class="decision-item">📉 Deficit %GDP: {float(round_fiscal.get('deficit_pct_gdp', 0)):+.1f}%</div>
                        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)



def show_beat_market_scoreboard(game):
    if not game.get("teams"):
        st.info("⏳ Waiting for teams to join...")
        return

    esg_mode = bool(game.get("settings", {}).get("esg_mode"))
    
    scores = []
    for team_name, team_data in game["teams"].items():
        portfolio_value = team_data.get("portfolio_value", {})
        returns = float(portfolio_value.get("returns", 0.0))
        risk = float(portfolio_value.get("risk", 50.0))
        score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns

        scores.append({
            "team": team_name,
            "score": score,
            "data": team_data
        })

    scores.sort(key=lambda x: x["score"], reverse=True)

    for rank, item in enumerate(scores, 1):
        team_name = item["team"]
        team_data = item["data"]
        score = item["score"]
        
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        card_class = f"rank-{rank}" if rank <= 3 else "scoreboard-card"
        name_color = "#0f2027" if rank <= 3 else "#00ff88"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:48px;">{medal}</span>
                    <span class="team-name-display" style="color:{name_color};">{team_name}</span>
                </div>
                <div class="metric-value" style="color:{name_color};">{score:.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        portfolio_value = team_data.get("portfolio_value", {})
        cols = st.columns(5 if esg_mode else 4)

        with cols[0]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">${portfolio_value.get('value', 1000000):,.0f}</div>
                <div class="metric-label">💼 VALUE</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            returns = portfolio_value.get("returns", 0)
            returns_color = "#00ff88" if returns >= 0 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{returns_color};">{returns:+.1f}%</div>
                <div class="metric-label">📈 RETURNS</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            risk = portfolio_value.get("risk", 50)
            risk_color = "#ff4757" if risk > 70 else "#ffa502" if risk > 40 else "#00ff88"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{risk_color};">{risk:.0f}/100</div>
                <div class="metric-label">⚠️ RISK</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[3]:
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value">{score:.2f}</div>
                <div class="metric-label">🎯 RISK-ADJ</div>
            </div>
            """, unsafe_allow_html=True)

        if esg_mode:
            with cols[4]:
                esg = portfolio_value.get("esg", 50)
                esg_color = "#00ff88" if esg > 70 else "#ffa502" if esg > 40 else "#ff4757"
                st.markdown(f"""
                <div class="metric-display">
                    <div class="metric-value" style="color:{esg_color};">{esg:.0f}/100</div>
                    <div class="metric-label">🌱 ESG</div>
                </div>
                """, unsafe_allow_html=True)

        # Round history
        with st.expander(f"📊 {team_name} - Round History", expanded=False):
            round_history = team_data.get("round_history", {})
            
            if not round_history:
                st.info("No history available yet - play at least one round")
            else:
                sorted_rounds = sorted([int(r) for r in round_history.keys()])
                
                for round_num in sorted_rounds:
                    round_data = round_history.get(str(round_num), {})
                    
                    if not round_data:
                        continue
                    
                    decisions = round_data.get("decisions", {})
                    pv = round_data.get("portfolio_value", {})
                    round_score = round_data.get("score", 0)
                    
                    st.markdown(f"""
                    <div class="round-history-card">
                        <h4 style="color: #00ff88; margin: 0 0 10px 0;">Round {round_num} - Risk-Adj Score: {round_score:.2f}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Portfolio Allocation:**")
                        st.markdown(f"""
                        <div class="decision-item">💵 Cash: {decisions.get('cash_pct', 25)}%</div>
                        <div class="decision-item">📊 Shares: {decisions.get('shares_pct', 25)}%</div>
                        <div class="decision-item">₿ Crypto: {decisions.get('crypto_pct', 25)}%</div>
                        <div class="decision-item">🏦 Bonds: {decisions.get('bonds_pct', 25)}%</div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("**Results:**")
                        st.markdown(f"""
                        <div class="decision-item">💼 Value: ${pv.get('value', 1000000):,.0f}</div>
                        <div class="decision-item">📈 Returns: {pv.get('returns', 0):+.1f}%</div>
                        <div class="decision-item">⚠️ Risk: {pv.get('risk', 50):.0f}/100</div>
                        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)


def show_crypto_crash_scoreboard(game):
    if not game.get("teams"):
        st.info("⏳ Waiting for teams to join...")
        return

    scores = []
    for team_name, team_data in game["teams"].items():
        cp = team_data.get("crypto_portfolio", {"equity": 1000.0})
        equity = float(cp.get("equity", 1000.0))

        scores.append({
            "team": team_name,
            "equity": equity,
            "data": team_data
        })

    scores.sort(key=lambda x: x["equity"], reverse=True)

    for rank, item in enumerate(scores, 1):
        team_name = item["team"]
        team_data = item["data"]
        equity = item["equity"]
        
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        card_class = f"rank-{rank}" if rank <= 3 else "scoreboard-card"
        name_color = "#0f2027" if rank <= 3 else "#00ff88"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:48px;">{medal}</span>
                    <span class="team-name-display" style="color:{name_color};">{team_name}</span>
                </div>
                <div class="metric-value" style="color:{name_color};">{equity:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cp = team_data.get("crypto_portfolio", {})
        cols = st.columns(5)
        
        with cols[0]:
            equity_color = "#00ff88" if equity >= 1000 else "#ffa502" if equity >= 500 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{equity_color};">{equity:,.0f}</div>
                <div class="metric-label">💼 EQUITY</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            total_ret = cp.get("total_return_pct", 0)
            ret_color = "#00ff88" if total_ret >= 0 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{ret_color};">{total_ret:+.1f}%</div>
                <div class="metric-label">📈 TOTAL RETURN</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            risk_exposure = cp.get("risk_exposure", 0)
            risk_label = cp.get("risk_label", "Low")
            risk_color = "#00ff88" if risk_exposure < 30 else "#ffa502" if risk_exposure < 60 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{risk_color};">{risk_label}</div>
                <div class="metric-label">⚠️ RISK ({risk_exposure:.0f}/100)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[3]:
            leverage = cp.get("leverage", 1)
            lev_color = "#00ff88" if leverage <= 2 else "#ffa502" if leverage <= 3 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{lev_color};">{leverage:.0f}x</div>
                <div class="metric-label">⚡ LEVERAGE</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[4]:
            liquidations = cp.get("liquidations", 0)
            liq_color = "#00ff88" if liquidations == 0 else "#ff4757"
            st.markdown(f"""
            <div class="metric-display">
                <div class="metric-value" style="color:{liq_color};">{liquidations}</div>
                <div class="metric-label">🚨 LIQUIDATIONS</div>
            </div>
            """, unsafe_allow_html=True)

        # Round history
        with st.expander(f"📊 {team_name} - Round History", expanded=False):
            round_history = team_data.get("round_history", {})
            
            if not round_history:
                st.info("No history available yet - play at least one round")
            else:
                sorted_rounds = sorted([int(r) for r in round_history.keys()])
                
                for round_num in sorted_rounds:
                    round_data = round_history.get(str(round_num), {})
                    
                    if not round_data:
                        continue
                    
                    decisions = round_data.get("decisions", {})
                    alloc = decisions.get("allocations", {})
                    leverage_used = decisions.get("leverage", 1)
                    cp_round = round_data.get("crypto_portfolio", {})
                    round_equity = round_data.get("score", 1000)
                    
                    st.markdown(f"""
                    <div class="round-history-card">
                        <h4 style="color: #00ff88; margin: 0 0 10px 0;">Round {round_num} - Equity: {round_equity:,.0f}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Allocation:**")
                        st.markdown(f"""
                        <div class="decision-item">🟠 BTC: {alloc.get('btc', 40)}%</div>
                        <div class="decision-item">🔵 ETH: {alloc.get('eth', 30)}%</div>
                        <div class="decision-item">🟡 DOGE: {alloc.get('doge', 20)}%</div>
                        <div class="decision-item">🟢 Stable: {alloc.get('stable', 10)}%</div>
                        <div class="decision-item">⚡ Leverage: {leverage_used}x</div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("**Results:**")
                        st.markdown(f"""
                        <div class="decision-item">💼 Equity: {cp_round.get('equity', 1000):,.0f}</div>
                        <div class="decision-item">📈 Return: {cp_round.get('last_return_pct', 0):+.1f}%</div>
                        <div class="decision-item">⚠️ Risk: {cp_round.get('risk_label', 'Low')}</div>
                        <div class="decision-item">🚨 Liquidations: {cp_round.get('liquidations', 0)}</div>
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

    running_games = []
    for code, g in all_games.items():
        if g.get("status") in ["running", "finished"]:
            running_games.append((code, g, g.get("created_at", "")))

    running_games.sort(key=lambda x: x[2], reverse=True)

    if len(running_games) >= 1:
        st.session_state["scoreboard_code"] = running_games[0][0]
    else:
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