"""
Team Page - Compact layout with side timer
"""

import streamlit as st
import shared_state as state
import time
from datetime import timedelta, datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Team Play",
    page_icon="👥",
    layout="wide"
)

# Initialize
state.init_user_session()

# Compact CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem !important;
    }
    
    h1 { font-size: 1.8rem !important; margin: 0.5rem 0 !important; color: white; }
    h2 { font-size: 1.3rem !important; margin: 0.3rem 0 !important; color: white; }
    h3 { font-size: 1.1rem !important; margin: 0.2rem 0 !important; }
    p { font-size: 0.9rem !important; margin: 0.2rem 0 !important; }
    
    .stButton>button {
        padding: 0.4rem 1rem !important;
        font-size: 0.9rem !important;
    }
    
    .block-container {
        padding: 1rem !important;
        max-width: 100% !important;
    }
    
    .team-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
    }
    
    .timer-box {
        background: #0f2027;
        color: #00ff88;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
        position: sticky;
        top: 10px;
    }
    
    .scenario-box {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #f5576c;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.3rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Check team access
if not state.is_team():
    st.error("🚫 Team access required!")
    st.stop()

game = state.get_current_game()
if not game:
    st.error("❌ Game not found!")
    st.stop()

# Store previous game status and round to detect changes
if 'previous_game_status' not in st.session_state:
    st.session_state.previous_game_status = game['status']
if 'previous_round' not in st.session_state:
    st.session_state.previous_round = game['current_round']

# If game status just changed (e.g., from setup to running), do a manual refresh
if st.session_state.previous_game_status != game['status']:
    st.session_state.previous_game_status = game['status']
    st.session_state.previous_round = game['current_round']
    time.sleep(0.5)  # Brief pause to let state settle
    st.rerun()

# If round changed, refresh to show new timer
if st.session_state.previous_round != game['current_round']:
    st.session_state.previous_round = game['current_round']
    time.sleep(0.3)
    st.rerun()

# Auto-refresh using streamlit-autorefresh - but ONLY when game is running
# This prevents refresh from blocking game start
if game['status'] == 'running' and game.get("round_timer_end"):
    # Check if timer is actually running
    timer_active, remaining = state.check_round_timer(st.session_state.join_code)
    if timer_active and remaining > 0:
        # Refresh every 1 second while timer is running
        st_autorefresh(interval=1000, key="timer_refresh")

# ============================================================================
# RESULTS DISPLAY FUNCTIONS
# ============================================================================

def show_build_country_results(game, team_name):
    """Show final results for Build a Country game"""
    team_data = game['teams'].get(team_name, {})
    metrics = team_data.get('metrics', {'gdp': 100, 'employment': 75, 'inequality': 50, 'approval': 50})

    # Calculate score
    score = (
        metrics.get('gdp', 100) * 0.3 +
        metrics.get('employment', 75) * 0.25 +
        (100 - metrics.get('inequality', 50)) * 0.25 +
        metrics.get('approval', 50) * 0.2
    )

    # Calculate rank
    all_scores = []
    for t_name, t_data in game.get('teams', {}).items():
        t_metrics = t_data.get('metrics', {'gdp': 100, 'employment': 75, 'inequality': 50, 'approval': 50})
        t_score = (
            t_metrics.get('gdp', 100) * 0.3 +
            t_metrics.get('employment', 75) * 0.25 +
            (100 - t_metrics.get('inequality', 50)) * 0.25 +
            t_metrics.get('approval', 50) * 0.2
        )
        all_scores.append((t_name, t_score))
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (n, s) in enumerate(all_scores) if n == team_name), 1)

    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px;">
        <h1 style="color: #0f2027; margin: 0;">{medal} Your Final Rank</h1>
        <p style="font-size: 3rem; font-weight: bold; color: #0f2027; margin: 10px 0;">{rank} of {len(all_scores)}</p>
        <p style="font-size: 1.5rem; color: #333;">Score: {score:.1f}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 GDP", f"{metrics.get('gdp', 100):.1f}")
    with col2:
        st.metric("👷 Employment", f"{metrics.get('employment', 75):.1f}%")
    with col3:
        st.metric("⚖️ Inequality", f"{metrics.get('inequality', 50):.1f}")
    with col4:
        st.metric("❤️ Approval", f"{metrics.get('approval', 50):.1f}%")


def show_beat_market_results(game, team_name):
    """Show final results for Beat the Market game"""
    team_data = game['teams'].get(team_name, {})
    portfolio = team_data.get('portfolio_value', {'value': 1000000, 'returns': 0, 'risk': 50})

    value = portfolio.get('value', 1000000)
    returns = portfolio.get('returns', 0)
    risk = portfolio.get('risk', 50)
    risk_adj_score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns

    # Calculate rank
    all_scores = []
    for t_name, t_data in game.get('teams', {}).items():
        t_portfolio = t_data.get('portfolio_value', {'value': 1000000, 'returns': 0, 'risk': 50})
        t_returns = t_portfolio.get('returns', 0)
        t_risk = t_portfolio.get('risk', 50)
        t_score = (t_returns / max(1.0, t_risk)) * 100.0 if t_risk > 0 else t_returns
        all_scores.append((t_name, t_score))
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (n, s) in enumerate(all_scores) if n == team_name), 1)

    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px;">
        <h1 style="color: #0f2027; margin: 0;">{medal} Your Final Rank</h1>
        <p style="font-size: 3rem; font-weight: bold; color: #0f2027; margin: 10px 0;">{rank} of {len(all_scores)}</p>
        <p style="font-size: 1.5rem; color: #333;">Risk-Adjusted Score: {risk_adj_score:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💼 Portfolio Value", f"${value:,.0f}")
    with col2:
        st.metric("📈 Returns", f"{returns:+.1f}%")
    with col3:
        st.metric("⚠️ Risk Score", f"{risk:.0f}/100")


def show_crypto_crash_results(game, team_name):
    """Show final results for Crypto Crash game"""
    team_data = game['teams'].get(team_name, {})
    performance = team_data.get('performance', {'profit': 0, 'risk_score': 50, 'decisions_correct': 0, 'total_decisions': 1})

    profit = performance.get('profit', 0)
    risk_score = performance.get('risk_score', 50)
    correct = performance.get('decisions_correct', 0)
    total = performance.get('total_decisions', 1) or 1
    accuracy = (correct / total) * 100

    risk_bonus = (100 - risk_score) / 10.0 if profit > 0 else 0
    final_score = profit + risk_bonus + (accuracy / 2.0)

    # Calculate rank
    all_scores = []
    for t_name, t_data in game.get('teams', {}).items():
        t_perf = t_data.get('performance', {'profit': 0, 'risk_score': 50, 'decisions_correct': 0, 'total_decisions': 1})
        t_profit = t_perf.get('profit', 0)
        t_risk = t_perf.get('risk_score', 50)
        t_correct = t_perf.get('decisions_correct', 0)
        t_total = t_perf.get('total_decisions', 1) or 1
        t_acc = (t_correct / t_total) * 100
        t_bonus = (100 - t_risk) / 10.0 if t_profit > 0 else 0
        t_score = t_profit + t_bonus + (t_acc / 2.0)
        all_scores.append((t_name, t_score))
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (n, s) in enumerate(all_scores) if n == team_name), 1)

    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px;">
        <h1 style="color: #0f2027; margin: 0;">{medal} Your Final Rank</h1>
        <p style="font-size: 3rem; font-weight: bold; color: #0f2027; margin: 10px 0;">{rank} of {len(all_scores)}</p>
        <p style="font-size: 1.5rem; color: #333;">Final Score: {final_score:.1f}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Profit", f"{profit:+.1f}%")
    with col2:
        st.metric("⚠️ Risk", f"{risk_score:.0f}/100")
    with col3:
        st.metric("🎯 Accuracy", f"{accuracy:.0f}%")
    with col4:
        st.metric("✅ Correct", f"{correct}/{total}")


# ============================================================================
# GAME INTERFACE FUNCTIONS - DEFINED BEFORE USE
# ============================================================================

def show_build_country_compact(game):
    team_data = game['teams'].get(st.session_state.team_name, {})
    decisions = team_data.get('decisions', {})
    decision_saved = team_data.get('decision_saved_round') == game['current_round']

    # Game brief and scoring info
    with st.expander("📖 How to Play & Scoring", expanded=False):
        st.markdown("""
        **🎯 Objective:** Run a successful country by balancing economic growth with social welfare.

        **📋 Your Decisions:**
        - **Tax Rate:** Higher taxes reduce inequality but may slow growth
        - **Education Spending:** Improves long-term employment and reduces inequality
        - **Infrastructure Spending:** Boosts GDP and employment
        - **Climate Policy:** Strong policy improves approval but has short-term GDP cost

        **📊 Scoring Formula:**
        - GDP Growth: **30%** of score
        - Employment Rate: **25%** of score
        - Low Inequality: **25%** of score (lower is better!)
        - Public Approval: **20%** of score

        💡 *Tip: Balance all metrics - don't focus on just one!*
        """)

    # Scenario
    scenario = game.get('game_state', {}).get('current_scenario')
    if scenario:
        st.markdown(f"""
        <div class="scenario-box">
            <strong>{scenario.get('name', '')}</strong><br>
            <span style="font-size: 0.85rem;">{scenario.get('description', '')}</span>
        </div>
        """, unsafe_allow_html=True)

    # Check if already saved for this round
    if decision_saved:
        st.success("✅ Decision saved for this round! Wait for next round.")
        st.markdown("#### 📋 Your Saved Decisions")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"💵 Tax Rate: {decisions.get('tax_rate', 30)}%")
            st.info(f"📚 Education: {decisions.get('education_spending', 25)}%")
        with col2:
            st.info(f"🏗️ Infrastructure: {decisions.get('infrastructure_spending', 25)}%")
            st.info(f"🌱 Climate: {decisions.get('climate_policy', 'Moderate')}")
        return

    # Decision inputs - each on its own row
    st.markdown("#### 📋 Your Decisions")

    tax = st.slider("💵 Tax Rate (%)", 10, 50, decisions.get('tax_rate', 30), 5,
                   disabled=game['round_locked'])

    edu = st.slider("📚 Education Spending (%)", 10, 50, decisions.get('education_spending', 25), 5,
                   disabled=game['round_locked'])

    infra = st.slider("🏗️ Infrastructure Spending (%)", 10, 50, decisions.get('infrastructure_spending', 25), 5,
                     disabled=game['round_locked'])

    climate = st.selectbox("🌱 Climate Policy", ["Weak", "Moderate", "Strong"],
                          index=["Weak", "Moderate", "Strong"].index(decisions.get('climate_policy', 'Moderate')),
                          disabled=game['round_locked'])

    if not game['round_locked']:
        # Confirmation flow
        confirm_key = f"confirm_save_build_{game['current_round']}"
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure? You cannot change your decision after saving!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save", type="primary", use_container_width=True):
                    state.update_team_data(st.session_state.join_code, st.session_state.team_name, {
                        'decisions': {'tax_rate': tax, 'education_spending': edu,
                                     'infrastructure_spending': infra, 'climate_policy': climate},
                        'decision_saved_round': game['current_round']
                    })
                    st.session_state[confirm_key] = False
                    st.success("✅ Saved!")
                    time.sleep(0.5)
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.rerun()
        else:
            if st.button("💾 Save Decisions", type="primary", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()

def show_beat_market_compact(game):
    team_data = game['teams'].get(st.session_state.team_name, {})
    portfolio = team_data.get('portfolio', {'cash_pct': 25, 'shares_pct': 25, 'crypto_pct': 25, 'bonds_pct': 25})
    decision_saved = team_data.get('decision_saved_round') == game['current_round']

    # Game brief and scoring info
    with st.expander("📖 How to Play & Scoring", expanded=False):
        st.markdown("""
        **🎯 Objective:** Build the best investment portfolio by balancing returns and risk.

        **💼 Asset Classes:**
        - **Cash:** Safe but low returns (~0.2% per round)
        - **Bonds:** Low risk, modest returns (~0.6% per round)
        - **Shares:** Medium risk, good returns (~1.2% per round)
        - **Crypto:** High risk, high potential returns (~2% per round)

        **⚡ Market Events:** Each round has a market event that affects different assets!

        **📊 Scoring Formula:**
        - **Risk-Adjusted Return** = Returns ÷ Risk Score × 100
        - Higher returns with lower risk = better score!

        💡 *Tip: Read the market event carefully - it hints at which assets will perform well!*
        """)

    # Event
    event = game.get('game_state', {}).get('current_event')
    if event:
        st.markdown(f"""
        <div class="scenario-box" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);">
            <strong style="color: white;">{event.get('name', '')}</strong><br>
            <span style="font-size: 0.85rem; color: white;">{event.get('description', '')}</span>
        </div>
        """, unsafe_allow_html=True)

    # Check if already saved for this round
    if decision_saved:
        st.success("✅ Decision saved for this round! Wait for next round.")
        st.markdown("#### 💼 Your Saved Portfolio")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"💵 Cash: {portfolio.get('cash_pct', 25)}%")
            st.info(f"📊 Shares: {portfolio.get('shares_pct', 25)}%")
        with col2:
            st.info(f"₿ Crypto: {portfolio.get('crypto_pct', 25)}%")
            st.info(f"🏦 Bonds: {portfolio.get('bonds_pct', 25)}%")
        return

    # Portfolio sliders - each on its own row
    st.markdown("#### 💼 Portfolio Allocation")

    cash = st.slider("💵 Cash (%)", 0, 100, portfolio.get('cash_pct', 25), 5, disabled=game['round_locked'])

    shares = st.slider("📊 Shares (%)", 0, 100, portfolio.get('shares_pct', 25), 5, disabled=game['round_locked'])

    crypto = st.slider("₿ Crypto (%)", 0, 100, portfolio.get('crypto_pct', 25), 5, disabled=game['round_locked'])

    bonds = st.slider("🏦 Bonds (%)", 0, 100, portfolio.get('bonds_pct', 25), 5, disabled=game['round_locked'])

    total = cash + shares + crypto + bonds
    if total != 100:
        st.warning(f"⚠️ Total: {total}% (need 100%)")
    else:
        st.success("✅ Balanced (100%)")

    if not game['round_locked'] and total == 100:
        # Confirmation flow
        confirm_key = f"confirm_save_market_{game['current_round']}"
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure? You cannot change your decision after saving!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save", type="primary", use_container_width=True):
                    state.update_team_data(st.session_state.join_code, st.session_state.team_name, {
                        'portfolio': {'cash_pct': cash, 'shares_pct': shares, 'crypto_pct': crypto, 'bonds_pct': bonds},
                        'decision_saved_round': game['current_round']
                    })
                    st.session_state[confirm_key] = False
                    st.success("✅ Saved!")
                    time.sleep(0.5)
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.rerun()
        else:
            if st.button("💾 Save Portfolio", type="primary", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()

def show_crypto_crash_compact(game):
    team_data = game['teams'].get(st.session_state.team_name, {})
    decision = team_data.get('decision', {'action': 'Hold', 'exposure': 50})
    decision_saved = team_data.get('decision_saved_round') == game['current_round']

    # Game brief and scoring info
    with st.expander("📖 How to Play & Scoring", expanded=False):
        st.markdown("""
        **🎯 Objective:** Predict crypto market movements and manage your risk exposure.

        **📊 Market Indicators:**
        - **Sentiment:** How positive investors feel (higher = bullish)
        - **Volume:** Trading activity level (higher = more action)
        - **Hype:** Social media buzz (⚠️ high hype can signal a bubble!)

        **🎯 Your Decisions:**
        - **Buy:** Profit when market goes up
        - **Hold:** Play it safe, small steady gains
        - **Sell:** Profit when market goes down
        - **Risk Exposure:** Higher = bigger potential gains/losses

        **📊 Scoring Formula:**
        - Profit from correct predictions
        - Risk Bonus (lower risk = bonus points)
        - Accuracy (correct decisions / total)

        💡 *Tip: High hype + high sentiment often precedes a crash!*
        """)

    # Indicators
    indicators = game.get('game_state', {}).get('indicators',
                          {'sentiment': 50, 'volume': 50, 'hype': 50, 'price': 10000, 'price_change': 0})

    st.markdown("#### 📊 Market Indicators")

    col1, col2, col3 = st.columns(3)

    with col1:
        sentiment = indicators.get('sentiment', 50)
        color = "#00ff88" if sentiment > 60 else "#ffa502" if sentiment > 40 else "#ff4757"
        st.markdown(f"<div style='text-align:center'><span style='color:{color};font-size:2rem;font-weight:bold'>{sentiment:.0f}</span><br>😊 Sentiment</div>", unsafe_allow_html=True)

    with col2:
        volume = indicators.get('volume', 50)
        color = "#00ff88" if volume > 60 else "#ffa502" if volume > 40 else "#ff4757"
        st.markdown(f"<div style='text-align:center'><span style='color:{color};font-size:2rem;font-weight:bold'>{volume:.0f}</span><br>📈 Volume</div>", unsafe_allow_html=True)

    with col3:
        hype = indicators.get('hype', 50)
        color = "#ff4757" if hype > 70 else "#ffa502" if hype > 50 else "#00ff88"
        st.markdown(f"<div style='text-align:center'><span style='color:{color};font-size:2rem;font-weight:bold'>{hype:.0f}</span><br>🔥 Hype</div>", unsafe_allow_html=True)

    price = indicators.get('price', 10000)
    change = indicators.get('price_change', 0)
    change_color = "#00ff88" if change >= 0 else "#ff4757"
    st.markdown(f"<div style='text-align:center;font-size:2rem;color:#00ff88;font-weight:bold'>${price:,.0f} <span style='font-size:1.2rem;color:{change_color}'>({change:+.1f}%)</span></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Check if already saved for this round
    if decision_saved:
        st.success("✅ Decision saved for this round! Wait for next round.")
        st.markdown("#### 🎯 Your Saved Decision")
        st.info(f"Action: **{decision.get('action', 'Hold')}** | Risk Exposure: **{decision.get('exposure', 50)}%**")
        return

    st.markdown("#### 🎯 Your Decision")

    action = st.radio("Action", ["Buy", "Hold", "Sell"],
                     index=["Buy", "Hold", "Sell"].index(decision.get('action', 'Hold')),
                     disabled=game['round_locked'], horizontal=True)

    exposure = st.slider("⚠️ Risk Exposure (%)", 0, 100, decision.get('exposure', 50), 10, disabled=game['round_locked'])

    if not game['round_locked']:
        # Confirmation flow
        confirm_key = f"confirm_save_crypto_{game['current_round']}"
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure? You cannot change your decision after saving!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save", type="primary", use_container_width=True):
                    state.update_team_data(st.session_state.join_code, st.session_state.team_name, {
                        'decision': {'action': action, 'exposure': exposure},
                        'decision_saved_round': game['current_round']
                    })
                    st.session_state[confirm_key] = False
                    st.success("✅ Saved!")
                    time.sleep(0.5)
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.rerun()
        else:
            if st.button("💾 Save Decision", type="primary", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()

# ============================================================================
# MAIN PAGE LAYOUT
# ============================================================================

# Compact header
st.markdown(f"<h1>👥 {st.session_state.team_name} | Round {game['current_round']}/{game['settings']['num_rounds']}</h1>", 
            unsafe_allow_html=True)

# Main layout: Timer on left, content on right
timer_col, content_col = st.columns([1, 4])

with timer_col:
    # Timer display - always visible
    timer_active, remaining = state.check_round_timer(st.session_state.join_code)
    
    if game['status'] == 'setup':
        st.markdown("""
        <div class="timer-box" style="background: #2c3e50; color: #95a5a6;">
            ⏱️<br>WAITING<br>
            <span style="font-size: 1rem;">Game hasn't started</span>
        </div>
        """, unsafe_allow_html=True)
    
    elif game['status'] == 'finished':
        st.markdown("""
        <div class="timer-box" style="background: #27ae60; color: white;">
            🏁<br>FINISHED<br>
            <span style="font-size: 1rem;">Check scoreboard!</span>
        </div>
        """, unsafe_allow_html=True)
    
    elif timer_active and remaining > 0:
        timer_color = "#ff4757" if remaining <= 10 else "#ffa502" if remaining <= 30 else "#00ff88"
        st.markdown(f"""
        <div class="timer-box" style="color: {timer_color};">
            ⏱️<br>{state.format_time_remaining(remaining)}
        </div>
        """, unsafe_allow_html=True)
    
    elif timer_active and remaining == 0:
        st.markdown("""
        <div class="timer-box" style="color: #ff4757;">
            ⏰<br>TIME'S UP!<br>
            <span style="font-size: 1rem;">Wait for next round</span>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # No timer running during game
        st.markdown("""
        <div class="timer-box" style="background: #34495e; color: #95a5a6;">
            ⏱️<br>NO TIMER<br>
            <span style="font-size: 1rem;">Wait for admin</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Game Status Info with colored status
    status_colors = {
        'setup': '#95a5a6',
        'running': '#00ff88',
        'finished': '#3498db'
    }
    status_color = status_colors.get(game['status'], '#95a5a6')
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; text-align: center;">
        <strong style="color: white;">Round {game['current_round']}/{game['settings']['num_rounds']}</strong><br>
        <span style="color: {status_color}; font-size: 0.85rem; font-weight: bold;">{game['status'].upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Refresh button
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    st.markdown("---")

    # Ready status
    team_data = game['teams'].get(st.session_state.team_name, {})
    is_ready = team_data.get('ready', False)

    ready_clicked = st.checkbox(
        "✅ Ready",
        value=is_ready,
        disabled=game['round_locked'] or game['status'] != 'running'
    )

    if ready_clicked != is_ready:
        state.set_team_ready(st.session_state.join_code, st.session_state.team_name, ready_clicked)
        st.rerun()

with content_col:
    if game['status'] == 'setup':
        st.info("⏳ Waiting for admin to start...")

    elif game['status'] == 'finished':
        st.success("🏁 Game finished!")
        st.balloons()

        # Show final results based on game type
        if game['game_type'] == 'build_country':
            show_build_country_results(game, st.session_state.team_name)
        elif game['game_type'] == 'beat_market':
            show_beat_market_results(game, st.session_state.team_name)
        elif game['game_type'] == 'crypto_crash':
            show_crypto_crash_results(game, st.session_state.team_name)

    elif game['round_locked']:
        st.warning("🔒 Round locked - wait for admin")

    else:
        # Show game interface based on type
        if game['game_type'] == 'build_country':
            show_build_country_compact(game)
        elif game['game_type'] == 'beat_market':
            show_beat_market_compact(game)
        elif game['game_type'] == 'crypto_crash':
            show_crypto_crash_compact(game)

