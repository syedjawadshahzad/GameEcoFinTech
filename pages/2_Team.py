"""
Team Page - Compact layout with side timer
"""

import streamlit as st
import shared_state as state
import time
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
<style>.main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem !important;
    }

    h1 { font-size: 1.8rem !important; margin: 0.5rem 0 !important; color: white; }
    h2 { font-size: 1.3rem !important; margin: 0.3rem 0 !important; color: white; }
    h3 { font-size: 1.1rem !important; margin: 0.2rem 0 !important; }
    p { font-size: 0.9rem !important; margin: 0.2rem 0 !important; }.stButton>button {
        padding: 0.4rem 1rem !important;
        font-size: 0.9rem !important;
    }.block-container {
        padding: 1rem !important;
        max-width: 100% !important;
    }.team-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
    }.timer-box {
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
    }.scenario-box {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #f5576c;
    }

    div[data-testid="stVerticalBlock"] > div {
        gap: 0.3rem !important;
    }.hint-card {
        background: rgba(255,255,255,0.92);
        border-radius: 10px;
        padding: 10px 12px;
        margin-top: 8px;
        border-left: 4px solid rgba(102,126,234,0.9);
    }.hint-title {
        font-weight: 700;
        color: #333;
        margin-bottom: 4px;
        font-size: 0.95rem;
    }.hint-text {
        color: #444;
        font-size: 0.85rem;
        line-height: 1.25rem;
    }.hint-line {
        color: #111;
        font-size: 0.85rem;
        margin-top: 6px;
        padding: 6px 8px;
        border-radius: 8px;
        background: rgba(102,126,234,0.12);
        border: 1px solid rgba(102,126,234,0.18);
        font-weight: 600;
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
if "previous_game_status" not in st.session_state:
    st.session_state.previous_game_status = game["status"]
if "previous_round" not in st.session_state:
    st.session_state.previous_round = game["current_round"]

# If game status just changed (e.g., from setup to running), do a manual refresh
if st.session_state.previous_game_status != game["status"]:
    st.session_state.previous_game_status = game["status"]
    st.session_state.previous_round = game["current_round"]
    time.sleep(0.5)
    st.rerun()

# If round changed, refresh to show new timer
if st.session_state.previous_round != game["current_round"]:
    st.session_state.previous_round = game["current_round"]
    time.sleep(0.3)
    st.rerun()

# Auto-refresh only when timer is running
if game["status"] == "running" and game.get("round_timer_end"):
    timer_active, remaining = state.check_round_timer(st.session_state.join_code)
    if timer_active and remaining > 0:
        st_autorefresh(interval=1000, key="timer_refresh")


# ============================================================================
# RESULTS DISPLAY FUNCTIONS
# ============================================================================

def show_build_country_results(game, team_name):
    team_data = game["teams"].get(team_name, {})
    metrics = team_data.get("metrics", {"gdp": 100, "employment": 75, "inequality": 50, "approval": 50})

    score = (
        metrics.get("gdp", 100) * 0.3 +
        metrics.get("employment", 75) * 0.25 +
        (100 - metrics.get("inequality", 50)) * 0.25 +
        metrics.get("approval", 50) * 0.2
    )

    all_scores = []
    for t_name, t_data in game.get("teams", {}).items():
        t_metrics = t_data.get("metrics", {"gdp": 100, "employment": 75, "inequality": 50, "approval": 50})
        t_score = (
            t_metrics.get("gdp", 100) * 0.3 +
            t_metrics.get("employment", 75) * 0.25 +
            (100 - t_metrics.get("inequality", 50)) * 0.25 +
            t_metrics.get("approval", 50) * 0.2
        )
        all_scores.append((t_name, t_score))
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (n, _) in enumerate(all_scores) if n == team_name), 1)

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
    team_data = game["teams"].get(team_name, {})
    portfolio = team_data.get("portfolio_value", {"value": 1000000, "returns": 0, "risk": 50})

    value = portfolio.get("value", 1000000)
    returns = portfolio.get("returns", 0)
    risk = portfolio.get("risk", 50)
    risk_adj_score = (returns / max(1.0, risk)) * 100.0 if risk > 0 else returns

    all_scores = []
    for t_name, t_data in game.get("teams", {}).items():
        t_portfolio = t_data.get("portfolio_value", {"value": 1000000, "returns": 0, "risk": 50})
        t_returns = t_portfolio.get("returns", 0)
        t_risk = t_portfolio.get("risk", 50)
        t_score = (t_returns / max(1.0, t_risk)) * 100.0 if t_risk > 0 else t_returns
        all_scores.append((t_name, t_score))
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (n, _) in enumerate(all_scores) if n == team_name), 1)

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
    """
    UPDATED: uses team_data["crypto_portfolio"] (equity-based ranking)
    """
    team_data = game["teams"].get(team_name, {})
    cp = team_data.get("crypto_portfolio", {
        "equity": 1000.0,
        "total_return_pct": 0.0,
        "risk_exposure": 0.0,
        "risk_label": "Low",
        "liquidations": 0
    })

    equity = float(cp.get("equity", 1000.0))
    total_ret = float(cp.get("total_return_pct", 0.0))
    risk_exposure = float(cp.get("risk_exposure", 0.0))
    risk_label = cp.get("risk_label", "Low")
    liq = int(cp.get("liquidations", 0))

    # Rank by equity
    all_scores = []
    for t_name, t_data in game.get("teams", {}).items():
        t_cp = t_data.get("crypto_portfolio", {"equity": 1000.0})
        all_scores.append((t_name, float(t_cp.get("equity", 1000.0))))
    all_scores.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (n, _) in enumerate(all_scores) if n == team_name), 1)

    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px;">
        <h1 style="color: #0f2027; margin: 0;">{medal} Your Final Rank</h1>
        <p style="font-size: 3rem; font-weight: bold; color: #0f2027; margin: 10px 0;">{rank} of {len(all_scores)}</p>
        <p style="font-size: 1.5rem; color: #333;">Equity: {equity:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💼 Equity", f"{equity:,.0f}")
    with col2:
        st.metric("📈 Total Return", f"{total_ret:+.1f}%")
    with col3:
        st.metric("⚠️ Risk Exposure", f"{risk_label} ({risk_exposure:.0f}/100)")
    with col4:
        st.metric("🚨 Liquidations", f"{liq}")


# ============================================================================
# GAME INTERFACE FUNCTIONS
# ============================================================================

def show_build_country_compact(game):
    team_data = game["teams"].get(st.session_state.team_name, {})
    decisions = team_data.get("decisions", {})
    decision_saved = team_data.get("decision_saved_round") == game["current_round"]

    with st.expander("📖 How to Play & Scoring", expanded=False):
        st.markdown("""
        **🎯 Objective:** Run a successful country by balancing economic growth with social welfare.

        **📋 Your Decisions:**
        - **Tax Rate:** Higher taxes reduce inequality but may slow growth
        - **Education Spending:** Improves long-term employment and reduces inequality
        - **Infrastructure Spending:** Boosts GDP and employment
        - **Climate Policy:** Strong policy improves approval but has short-term GDP cost

        **📊 Scoring Formula:**
        - GDP Growth: **30%**
        - Employment Rate: **25%**
        - Low Inequality: **25%** (lower is better)
        - Public Approval: **20%**
        """)

    scenario = game.get("game_state", {}).get("current_scenario")
    if scenario:
        st.markdown(f"""
        <div class="scenario-box">
            <strong>{scenario.get('name', '')}</strong><br>
            <span style="font-size: 0.85rem;">{scenario.get('description', '')}</span>
        </div>
        """, unsafe_allow_html=True)

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

    st.markdown("#### 📋 Your Decisions")

    # ✅ FIXED: Use previous round's decisions as defaults
    # If no previous decisions exist (Round 1), use game defaults
    default_tax = decisions.get("tax_rate", 30)
    default_edu = decisions.get("education_spending", 25)
    default_infra = decisions.get("infrastructure_spending", 25)
    default_climate = decisions.get("climate_policy", "Moderate")

    tax = st.slider("💵 Tax Rate (%)", 10, 50, default_tax, 5, disabled=game["round_locked"])
    edu = st.slider("📚 Education Spending (%)", 10, 50, default_edu, 5, disabled=game["round_locked"])
    infra = st.slider("🏗️ Infrastructure Spending (%)", 10, 50, default_infra, 5, disabled=game["round_locked"])
    climate = st.selectbox(
        "🌱 Climate Policy",
        ["Weak", "Moderate", "Strong"],
        index=["Weak", "Moderate", "Strong"].index(default_climate),
        disabled=game["round_locked"]
    )

    if not game["round_locked"]:
        confirm_key = f"confirm_save_build_{game['current_round']}"
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure? You cannot change your decision after saving!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save", type="primary", use_container_width=True):
                    state.update_team_data(st.session_state.join_code, st.session_state.team_name, {
                        "decisions": {
                            "tax_rate": tax,
                            "education_spending": edu,
                            "infrastructure_spending": infra,
                            "climate_policy": climate
                        },
                        "decision_saved_round": game["current_round"]
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
    team_data = game["teams"].get(st.session_state.team_name, {})
    portfolio = team_data.get("portfolio", {"cash_pct": 25, "shares_pct": 25, "crypto_pct": 25, "bonds_pct": 25})
    decision_saved = team_data.get("decision_saved_round") == game["current_round"]

    with st.expander("📖 How to Play & Scoring", expanded=False):
        st.markdown("""
        **🎯 Objective:** Build the best investment portfolio by balancing returns and risk.

        **💼 Asset Classes:**
        - Cash: low return, very safe
        - Bonds: low risk, modest return
        - Shares: medium risk, good return
        - Crypto: high risk, high return

        **📊 Scoring:** Risk-Adjusted Return = Returns ÷ Risk × 100
        """)

    event = game.get("game_state", {}).get("current_event")
    if event:
        st.markdown(f"""
        <div class="scenario-box" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);">
            <strong style="color: white;">{event.get('name', '')}</strong><br>
            <span style="font-size: 0.85rem; color: white;">{event.get('description', '')}</span>
        </div>
        """, unsafe_allow_html=True)

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

    st.markdown("#### 💼 Portfolio Allocation")

    # ✅ FIXED: Use previous round's portfolio as defaults
    default_cash = portfolio.get("cash_pct", 25)
    default_shares = portfolio.get("shares_pct", 25)
    default_crypto = portfolio.get("crypto_pct", 25)
    default_bonds = portfolio.get("bonds_pct", 25)

    cash = st.slider("💵 Cash (%)", 0, 100, default_cash, 5, disabled=game["round_locked"])
    shares = st.slider("📊 Shares (%)", 0, 100, default_shares, 5, disabled=game["round_locked"])
    crypto = st.slider("₿ Crypto (%)", 0, 100, default_crypto, 5, disabled=game["round_locked"])
    bonds = st.slider("🏦 Bonds (%)", 0, 100, default_bonds, 5, disabled=game["round_locked"])

    total = cash + shares + crypto + bonds
    if total != 100:
        st.warning(f"⚠️ Total: {total}% (need 100%)")
    else:
        st.success("✅ Balanced (100%)")

    if not game["round_locked"] and total == 100:
        confirm_key = f"confirm_save_market_{game['current_round']}"
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure? You cannot change your decision after saving!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save", type="primary", use_container_width=True):
                    state.update_team_data(st.session_state.join_code, st.session_state.team_name, {
                        "portfolio": {"cash_pct": cash, "shares_pct": shares, "crypto_pct": crypto, "bonds_pct": bonds},
                        "decision_saved_round": game["current_round"]
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
    """
    UPDATED crypto UI:
    - shows per-indicator hint (from shared_state.game_state["indicator_notes"])
    - 4 sliders (BTC/ETH/DOGE/Stable) with Total must be 100% (like Beat Market)
    - Leverage slider 1..5
    - Saves into team_data["decisions"] as {"allocations":..., "leverage":...}
    """
    team_data = game["teams"].get(st.session_state.team_name, {})
    decisions = team_data.get("decisions", {}) if isinstance(team_data.get("decisions", {}), dict) else {}
    decision_saved = team_data.get("decision_saved_round") == game["current_round"]

    with st.expander("📖 How to Play (Simple)", expanded=False):
        st.markdown("""
        **🎯 Objective:** Grow your equity by choosing a crypto mix and leverage.

        **🟠 BTC / 🔵 ETH:** generally more stable than meme coins (still risky)  
        **🟡 DOGE:** most hype-driven (big pumps/crashes)  
        **🟢 Stablecoin:** safest (protects you in bad markets)

        **⚡ Leverage (1x–5x):** multiplies gains and losses.  
        If losses get too big in one round, you can get **liquidated**.
        """)

    story = game.get("game_state", {}).get("market_story")
    if story:
        st.markdown(f"""
        <div class="scenario-box" style="background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%); border-left: 4px solid #00c6ff;">
            <strong>🧠 Market Update</strong><br>
            <span style="font-size: 0.85rem;">{story}</span>
        </div>
        """, unsafe_allow_html=True)

    indicators = game.get("game_state", {}).get("indicators", {})
    notes = game.get("game_state", {}).get("indicator_notes", {}) or {}
    market_risk = game.get("game_state", {}).get("market_risk", None)
    asset_returns = game.get("game_state", {}).get("asset_returns", None)

    if indicators:
        st.markdown("#### 📊 Market Indicators")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("😊 Sentiment", f"{indicators.get('sentiment', 50)}")
            s_note = notes.get("sentiment", {}) or {}
            s_text = s_note.get("text", "")
            s_hint = s_note.get("hint", "")
            if s_text or s_hint:
                st.markdown(f"""
                <div class="hint-card">
                    <div class="hint-title">Sentiment</div>
                    <div class="hint-text">{s_text}</div>
                    <div class="hint-line">💡 {s_hint}</div>
                </div>
                """, unsafe_allow_html=True)

        with c2:
            st.metric("📈 Volume", f"{indicators.get('volume', 50)}")
            v_note = notes.get("volume", {}) or {}
            v_text = v_note.get("text", "")
            v_hint = v_note.get("hint", "")
            if v_text or v_hint:
                st.markdown(f"""
                <div class="hint-card">
                    <div class="hint-title">Volume</div>
                    <div class="hint-text">{v_text}</div>
                    <div class="hint-line">💡 {v_hint}</div>
                </div>
                """, unsafe_allow_html=True)

        with c3:
            st.metric("🔥 Hype", f"{indicators.get('hype', 50)}")
            h_note = notes.get("hype", {}) or {}
            h_text = h_note.get("text", "")
            h_hint = h_note.get("hint", "")
            if h_text or h_hint:
                st.markdown(f"""
                <div class="hint-card">
                    <div class="hint-title">Hype</div>
                    <div class="hint-text">{h_text}</div>
                    <div class="hint-line">💡 {h_hint}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    if market_risk is not None:
        st.markdown("#### ⚠️ Market Risk")
        st.info(f"Market risk this round: **{market_risk}/100** (higher = more dangerous)")

    if asset_returns:
        st.markdown("#### 📉 This round's asset moves (environment)")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("🟠 BTC", f"{asset_returns.get('btc', 0):+.2f}%")
        with c2:
            st.metric("🔵 ETH", f"{asset_returns.get('eth', 0):+.2f}%")
        with c3:
            st.metric("🟡 DOGE", f"{asset_returns.get('doge', 0):+.2f}%")
        with c4:
            st.metric("🟢 Stable", f"{asset_returns.get('stable', 0):+.2f}%")
        st.markdown("---")

    if decision_saved:
        st.success("✅ Decision saved for this round! Wait for next round.")

        alloc = decisions.get("allocations", {"btc": 40, "eth": 30, "doge": 20, "stable": 10})
        lev = decisions.get("leverage", 1)

        st.markdown("#### 🎯 Your Saved Allocation")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🟠 BTC: {alloc.get('btc', 0)}%")
            st.info(f"🔵 ETH: {alloc.get('eth', 0)}%")
        with col2:
            st.info(f"🟡 DOGE: {alloc.get('doge', 0)}%")
            st.info(f"🟢 Stable: {alloc.get('stable', 0)}%")

        st.info(f"⚡ Leverage: **{lev}x**")

        cp = team_data.get("crypto_portfolio", {})
        if cp.get("outcome"):
            st.warning(cp["outcome"])
        if cp.get("explain"):
            st.info(cp["explain"])
        return

    st.markdown("#### 💰 Your Crypto Allocation (must total 100%)")

    # ✅ FIXED: Use previous round's allocations as defaults
    existing = decisions.get("allocations", {"btc": 40, "eth": 30, "doge": 20, "stable": 10})
    if not isinstance(existing, dict):
        existing = {"btc": 40, "eth": 30, "doge": 20, "stable": 10}

    default_btc = int(existing.get("btc", 40))
    default_eth = int(existing.get("eth", 30))
    default_doge = int(existing.get("doge", 20))
    default_stable = int(existing.get("stable", 10))

    btc = st.slider("🟠 Bitcoin (BTC) %", 0, 100, default_btc, 5, disabled=game["round_locked"])
    eth = st.slider("🔵 Ethereum (ETH) %", 0, 100, default_eth, 5, disabled=game["round_locked"])
    doge = st.slider("🟡 Dogecoin (DOGE) %", 0, 100, default_doge, 5, disabled=game["round_locked"])
    stable = st.slider("🟢 Stablecoin %", 0, 100, default_stable, 5, disabled=game["round_locked"])

    total = btc + eth + doge + stable
    if total != 100:
        st.warning(f"⚠️ Total: {total}% (must be 100%)")
    else:
        st.success("✅ Balanced (100%)")

    st.markdown("#### ⚡ Leverage")
    
    # ✅ FIXED: Use previous round's leverage as default
    existing_lev = int(decisions.get("leverage", 1)) if str(decisions.get("leverage", 1)).isdigit() else 1
    default_leverage = max(1, min(5, existing_lev))
    
    leverage = st.slider("Leverage (1x = normal, 5x = extreme)", 1, 5, default_leverage, 1, disabled=game["round_locked"])

    allocations = {"btc": btc, "eth": eth, "doge": doge, "stable": stable}

    if not game["round_locked"] and total == 100:
        confirm_key = f"confirm_save_crypto_{game['current_round']}"
        if st.session_state.get(confirm_key):
            st.warning("⚠️ Are you sure? You cannot change your decision after saving!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Save", type="primary", use_container_width=True):
                    state.update_team_data(st.session_state.join_code, st.session_state.team_name, {
                        "decisions": {
                            "allocations": allocations,
                            "leverage": int(leverage),
                        },
                        "decision_saved_round": game["current_round"],
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


# ============================================================================
# MAIN PAGE LAYOUT
# ============================================================================

st.markdown(
    f"<h1>👥 {st.session_state.team_name} | Round {game['current_round']}/{game['settings']['num_rounds']}</h1>",
    unsafe_allow_html=True
)

timer_col, content_col = st.columns([1, 4])

with timer_col:
    timer_active, remaining = state.check_round_timer(st.session_state.join_code)

    if game["status"] == "setup":
        st.markdown("""
        <div class="timer-box" style="background: #2c3e50; color: #95a5a6;">
            ⏱️<br>WAITING<br>
            <span style="font-size: 1rem;">Game hasn't started</span>
        </div>
        """, unsafe_allow_html=True)

    elif game["status"] == "finished":
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
        st.markdown("""
        <div class="timer-box" style="background: #34495e; color: #95a5a6;">
            ⏱️<br>NO TIMER<br>
            <span style="font-size: 1rem;">Wait for admin</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    status_colors = {"setup": "#95a5a6", "running": "#00ff88", "finished": "#3498db"}
    status_color = status_colors.get(game["status"], "#95a5a6")

    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; text-align: center;">
        <strong style="color: white;">Round {game['current_round']}/{game['settings']['num_rounds']}</strong><br>
        <span style="color: {status_color}; font-size: 0.85rem; font-weight: bold;">{game['status'].upper()}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with content_col:
    if game["status"] == "setup":
        st.info("⏳ Waiting for admin to start...")

    elif game["status"] == "finished":
        st.success("🏁 Game finished!")
        st.balloons()

        if game["game_type"] == "build_country":
            show_build_country_results(game, st.session_state.team_name)
        elif game["game_type"] == "beat_market":
            show_beat_market_results(game, st.session_state.team_name)
        elif game["game_type"] == "crypto_crash":
            show_crypto_crash_results(game, st.session_state.team_name)

    elif game["round_locked"]:
        st.warning("🔒 Round locked - wait for admin")

    else:
        if game["game_type"] == "build_country":
            show_build_country_compact(game)
        elif game["game_type"] == "beat_market":
            show_beat_market_compact(game)
        elif game["game_type"] == "crypto_crash":
            show_crypto_crash_compact(game)