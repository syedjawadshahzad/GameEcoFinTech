"""
Admin Page - Control game flow, manage teams, and monitor progress
"""

import streamlit as st
import shared_state as state
import time
import config
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Admin Control",
    page_icon="👨‍💼",
    layout="wide"
)

# Initialize
state.init_user_session()

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap');

    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: white;
    }

    .admin-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .team-list-item {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .status-ready {
        background: #00ff88;
        color: #0f2027;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
    }

    .status-waiting {
        background: #ffa502;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
    }

    .round-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 20px;
        display: inline-block;
        margin: 10px 0;
    }

    .timer-display {
        background: #0f2027;
        color: #00ff88;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-family: 'Courier New', monospace;
        font-size: 48px;
        font-weight: bold;
        margin: 20px 0;
    }

    .warning-box {
        background: #fff3cd;
        border-left: 5px solid #ffa502;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        color: #000000; /* ✅ ensure readable text */
    }
</style>
""", unsafe_allow_html=True)

# Check admin access
if not state.is_admin():
    st.error("🚫 Admin access required! Please create a game from the Home page.")
    st.stop()

# Get current game
game = state.get_current_game()

if not game:
    st.error("❌ Game session not found!")

    st.markdown("---")
    st.markdown("### 🔐 Re-authenticate as Admin")

    with st.form("admin_reauth"):
        reauth_password = st.text_input("Admin Password", type="password")
        join_code_input = st.text_input("Game Join Code")

        if st.form_submit_button("Re-authenticate"):
            if reauth_password != config.ADMIN_PASSWORD:
                st.error("❌ Invalid admin password!")
            else:
                game_check = state.get_game_session(join_code_input.upper())
                if game_check:
                    state.set_user_as_admin(game_check['admin_name'], join_code_input.upper())
                    st.success("✅ Re-authenticated!")
                    st.rerun()
                else:
                    st.error("❌ Game not found!")

    st.stop()

# Header
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h1>👨‍💼 Admin Control Panel</h1>
</div>
""", unsafe_allow_html=True)

# Auto-refresh using streamlit-autorefresh - but ONLY when game is running
# This prevents refresh from blocking game start
if game['status'] == 'running' and game.get("round_timer_end"):
    # Check if timer is actually running
    timer_active, remaining = state.check_round_timer(st.session_state.join_code)
    if timer_active and remaining > 0:
        # Refresh every 1 second while timer is running
        st_autorefresh(interval=1000, key="admin_timer_refresh")

# Sidebar - Game Info
with st.sidebar:
    st.markdown("## 🎮 Game Info")

    game_names = {
        "build_country": "🌍 Build a Country",
        "beat_market": "📈 Beat the Market",
        "crypto_crash": "₿ Crypto Crash"
    }

    st.markdown(f"**Game:** {game_names.get(game['game_type'], game['game_type'])}")
    st.markdown(f"**Status:** {game['status'].upper()}")
    st.markdown(f"**Teams:** {len(game['teams'])}")
    st.markdown(f"**Round:** {game['current_round']}/{game['settings']['num_rounds']}")

    st.markdown("---")

    st.markdown("## ⚙️ Settings")
    st.markdown(f"**Rounds:** {game['settings']['num_rounds']}")
    st.markdown(f"**Round Duration:** {game['settings']['round_duration']}s")
    st.markdown(f"**Auto-lock:** {'Yes' if game['settings']['auto_lock'] else 'No'}")

    if game['game_type'] == 'beat_market':
        st.markdown(f"**ESG Mode:** {'Yes' if game['settings'].get('esg_mode') else 'No'}")

    st.markdown("---")

    if st.button("🚪 End Game & Return Home", use_container_width=True):
        if st.session_state.get('confirm_end'):
            state.delete_game_session(st.session_state.join_code)
            state.clear_user_session()
            st.rerun()
        else:
            st.session_state.confirm_end = True
            st.warning("Click again to confirm")

# Main content
tab1, tab2 = st.tabs(["📋 Team Management", "🎮 Round Control"])

with tab1:
    st.markdown("### 👥 Team Management")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Teams Joined:** {len(game['teams'])} teams")

    with col2:
        if game['status'] == 'setup':
            st.markdown(f"**Status:** Ready to start")
        else:
            # Count teams that have saved their decision for current round
            current_round = game.get('current_round', 1)
            saved_count = sum(1 for t in game['teams'].values() if t.get('decision_saved_round') == current_round)
            st.markdown(f"**Decisions Saved:** {saved_count}/{len(game['teams'])}")

    if not game['teams']:
        st.info("⏳ Waiting for teams to join...")
    else:
        for team_name, team_data in game['teams'].items():
            # During setup, show "Joined" instead of "Ready/Not Ready"
            if game['status'] == 'setup':
                status_class = "status-ready"
                status_text = "✅ Joined"
            else:
                # During game, show decision saved status
                current_round = game.get('current_round', 1)
                decision_saved = team_data.get('decision_saved_round') == current_round
                if decision_saved:
                    status_class = "status-ready"
                    status_text = "✅ Saved"
                else:
                    status_class = "status-waiting"
                    status_text = "⏳ Deciding..."

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div class="team-list-item">
                    <div>
                        <strong style="font-size: 18px; color: #333;">{team_name}</strong><br>
                        <span style="color: #666; font-size: 14px;">
                            Joined: {team_data.get('joined_at', 'Unknown')[:19]}
                        </span>
                    </div>
                    <span class="{status_class}">{status_text}</span>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("🗑️ Remove", key=f"remove_{team_name}"):
                    state.remove_team_from_game(st.session_state.join_code, team_name)
                    st.rerun()

    st.markdown("---")

    if game['status'] == 'setup':
        if len(game['teams']) < 1:
            st.warning("⚠️ Need at least 1 team to start!")
        else:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("▶️ START GAME", use_container_width=True, type="primary"):
                    # Start the game and automatically start the timer
                    state.update_game_session(st.session_state.join_code, {
                        "status": "running",
                        "current_round": 1
                    })
                    
                    # Automatically start timer for first round
                    duration = game['settings']['round_duration']
                    state.start_round_timer(st.session_state.join_code, duration)
                    
                    st.success(f"✅ Game started! Timer: {duration}s")
                    time.sleep(1)
                    st.rerun()

with tab2:
    st.markdown("### 🎮 Round Control")

    if game['status'] != 'running':
        st.info("ℹ️ Start the game first from Team Management tab")
    else:
        st.markdown(f"""
        <div style="text-align: center;">
            <span class="round-badge">Round {game['current_round']} / {game['settings']['num_rounds']}</span>
        </div>
        """, unsafe_allow_html=True)

        # Timer
        timer_active, remaining = state.check_round_timer(st.session_state.join_code)

        if timer_active and remaining > 0:
            st.markdown(f"""
            <div class="timer-display">
                ⏱️ {state.format_time_remaining(remaining)}
            </div>
            """, unsafe_allow_html=True)

        elif timer_active and remaining == 0:
            st.markdown("""
            <div class="timer-display" style="color: #ff4757;">
                ⏰ TIME'S UP!
            </div>
            """, unsafe_allow_html=True)

            # ✅ Auto-lock when expired (this was previously unreachable)
            if game['settings']['auto_lock'] and not game['round_locked']:
                state.lock_round(st.session_state.join_code)
                st.rerun()

        # Round status panels
        col1, col2 = st.columns(2)

        with col1:
            lock_status = "🔒 LOCKED" if game['round_locked'] else "🔓 UNLOCKED"
            st.markdown(f"""
            <div class="admin-card">
                <h3 style="color: #667eea;">Round Status</h3>
                <p style="font-size: 24px; font-weight: bold; color: #333;">
                    {lock_status}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            ready_count = state.get_ready_team_count(st.session_state.join_code)
            all_ready = state.are_all_teams_ready(st.session_state.join_code)

            st.markdown(f"""
            <div class="admin-card">
                <h3 style="color: #667eea;">Teams Ready</h3>
                <p style="font-size: 24px; font-weight: bold; color: {'#00ff88' if all_ready else '#ffa502'};">
                    {ready_count} / {len(game['teams'])}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Timer Control Section
        st.markdown("#### ⏱️ Timer Control")
        
        timer_col1, timer_col2 = st.columns([2, 1])
        
        with timer_col1:
            if timer_active and remaining > 0:
                st.info(f"⏱️ Timer running: {state.format_time_remaining(remaining)} remaining")
            elif timer_active and remaining == 0:
                st.warning("⏰ Timer expired!")
            else:
                st.info("⏱️ No timer active for this round")
        
        with timer_col2:
            if not timer_active or remaining <= 0:
                if st.button("▶️ Start Timer", use_container_width=True, type="primary", key="start_timer_btn"):
                    duration = game['settings']['round_duration']
                    state.start_round_timer(st.session_state.join_code, duration)
                    st.success(f"✅ Timer started: {duration}s")
                    time.sleep(0.5)
                    st.rerun()
            else:
                if st.button("⏹️ Stop Timer", use_container_width=True, key="stop_timer_btn"):
                    state.update_game_session(st.session_state.join_code, {
                        "round_timer_end": None
                    })
                    st.success("✅ Timer stopped")
                    time.sleep(0.5)
                    st.rerun()

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if game['round_locked']:
                if st.button("🔓 Unlock Round", use_container_width=True):
                    state.unlock_round(st.session_state.join_code)
                    st.rerun()
            else:
                if st.button("🔒 Lock Round", use_container_width=True):
                    state.lock_round(st.session_state.join_code)
                    st.rerun()

        with col2:
            if st.button("🔄 Reset Ready Status", use_container_width=True):
                for team_name in game['teams'].keys():
                    state.set_team_ready(st.session_state.join_code, team_name, False)
                st.rerun()

        with col3:
            if game['current_round'] < game['settings']['num_rounds']:
                if st.button("⏭️ Next Round", use_container_width=True, type="primary"):
                    # Process current round and advance
                    state.advance_round(st.session_state.join_code)

                    # Reset all teams to not ready
                    for team_name in game['teams'].keys():
                        state.set_team_ready(st.session_state.join_code, team_name, False)
                    
                    # Automatically start timer for next round
                    duration = game['settings']['round_duration']
                    state.start_round_timer(st.session_state.join_code, duration)

                    st.success(f"✅ Round {game['current_round'] + 1} started! Timer: {duration}s")
                    time.sleep(1)
                    st.rerun()
            else:
                if st.button("🏁 Finish Game", use_container_width=True, type="primary"):
                    # ✅ process final round outcomes BEFORE finishing
                    state.process_current_round(st.session_state.join_code)

                    state.update_game_session(st.session_state.join_code, {
                        "status": "finished",
                        "round_locked": True,
                        "round_timer_end": None
                    })

                    st.success("🎉 Game finished! Final results saved.")
                    time.sleep(1)
                    st.rerun()