"""
Admin Page - Control game flow, manage teams, and monitor progress
"""

import streamlit as st
import shared_state as state
import time
import config
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Admin Control",
    page_icon="👨‍💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

def _get_query_param(name: str) -> str:
    try:
        v = st.query_params.get(name, "")
        if isinstance(v, list):
            return (v[0] if v else "").strip()
        return str(v).strip()
    except Exception:
        return ""

url_join_code = _get_query_param("join_code").upper()

if url_join_code and not st.session_state.get("user_type"):
    g = state.get_game_session(url_join_code)
    if g:
        st.session_state.user_type = "admin"
        st.session_state.admin_name = g.get("admin_name", "Admin")
        st.session_state.join_code = url_join_code
        st.session_state.team_name = None
        st.rerun()

state.init_user_session()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap');.main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem !important;
    }.block-container {
        padding: 1rem !important;
        max-width: 100% !important;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.35rem !important;
    }
    
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: white;
    }.admin-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 22px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }.team-list-item {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }.status-ready {
        background: #00ff88;
        color: #0f2027;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
    }.status-waiting {
        background: #ffa502;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
    }.round-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 10px 18px;
        border-radius: 25px;
        font-weight: 800;
        font-size: 20px;
        display: inline-block;
        margin: 10px 0;
    }.timer-display {
        background: #0f2027;
        color: #00ff88;
        padding: 18px;
        border-radius: 12px;
        text-align: center;
        font-family: 'Courier New', monospace;
        font-size: 48px;
        font-weight: bold;
        margin: 12px 0;
    }
    
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.96) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #111 !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #111 !important;
    }
</style>
""", unsafe_allow_html=True)

if not state.is_admin():
    st.error("🚫 Admin access required")
    st.markdown("---")
    st.markdown("### 🔐 Re-authenticate as Admin")
    
    url_join = _get_query_param("join_code").upper()
    
    with st.form("admin_reauth_top"):
        reauth_password = st.text_input("Admin Password", type="password")
        join_code_input = st.text_input("Game Join Code", value=url_join)
        
        if st.form_submit_button("Re-authenticate"):
            if not reauth_password:
                st.error("❌ Please enter admin password!")
            elif reauth_password != config.ADMIN_PASSWORD:
                st.error("❌ Invalid admin password!")
            elif not join_code_input:
                st.error("❌ Please enter game join code!")
            else:
                game_check = state.get_game_session(join_code_input.upper())
                if game_check:
                    state.set_user_as_admin(game_check.get("admin_name", "Admin"), join_code_input.upper())
                    st.success("✅ Re-authenticated!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Game not found!")
    
    st.info("💡 **Tip:** Create a new game from the Home page if you don't have a join code.")
    st.stop()

game = state.get_current_game()

if not game:
    st.error("❌ Game session not found!")
    
    st.markdown("---")
    st.markdown("### 🔐 Re-authenticate as Admin")
    
    with st.form("admin_reauth_nogame"):
        reauth_password = st.text_input("Admin Password", type="password")
        join_code_input = st.text_input("Game Join Code")
        
        if st.form_submit_button("Re-authenticate"):
            if not reauth_password:
                st.error("❌ Please enter admin password!")
            elif reauth_password != config.ADMIN_PASSWORD:
                st.error("❌ Invalid admin password!")
            elif not join_code_input:
                st.error("❌ Please enter game join code!")
            else:
                game_check = state.get_game_session(join_code_input.upper())
                if game_check:
                    state.set_user_as_admin(game_check["admin_name"], join_code_input.upper())
                    st.success("✅ Re-authenticated!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Game not found!")
    
    st.info("💡 **Tip:** Create a new game from the Home page.")
    st.stop()

st.markdown("""
<div style="text-align: center; padding: 12px 0 6px 0;">
    <h1>👨‍💼 Admin Control Panel</h1>
</div>
""", unsafe_allow_html=True)

if game["status"] == "running" and game.get("round_timer_end"):
    timer_active, remaining = state.check_round_timer(st.session_state.join_code)
    if timer_active and remaining > 0:
        st_autorefresh(interval=1000, key="admin_timer_refresh")

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
    
    if game["game_type"] == "beat_market":
        st.markdown(f"**ESG Mode:** {'Yes' if game['settings'].get('esg_mode') else 'No'}")
    
    st.markdown("---")
    
    if st.button("🚪 End Game & Return Home", use_container_width=True):
        if st.session_state.get("confirm_end"):
            state.delete_game_session(st.session_state.join_code)
            state.clear_user_session()
            st.rerun()
        else:
            st.session_state.confirm_end = True
            st.warning("Click again to confirm")

tab1, tab2 = st.tabs(["📋 Team Management", "🎮 Round Control"])

with tab1:
    st.markdown("### 👥 Team Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Teams Joined:** {len(game['teams'])} teams")
    
    with col2:
        if game["status"] == "setup":
            st.markdown("**Status:** Ready to start")
        else:
            current_round = game.get("current_round", 1)
            saved_count = sum(1 for t in game["teams"].values() if t.get("decision_saved_round") == current_round)
            st.markdown(f"**Decisions Saved:** {saved_count}/{len(game['teams'])}")
    
    if not game["teams"]:
        st.info("⏳ Waiting for teams to join...")
    else:
        for team_name, team_data in game["teams"].items():
            if game["status"] == "setup":
                status_class = "status-ready"
                status_text = "✅ Joined"
            else:
                current_round = game.get("current_round", 1)
                decision_saved = team_data.get("decision_saved_round") == current_round
                if decision_saved:
                    status_class = "status-ready"
                    status_text = "✅ Saved"
                else:
                    status_class = "status-waiting"
                    status_text = "⏳ Deciding..."
            
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
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
            
            with col_b:
                if st.button("🗑️ Remove", key=f"remove_{team_name}"):
                    state.remove_team_from_game(st.session_state.join_code, team_name)
                    st.rerun()
    
    st.markdown("---")
    
    if game["status"] == "setup":
        if len(game["teams"]) < 1:
            st.warning("⚠️ Need at least 1 team to start!")
        else:
            _, mid, _ = st.columns([1, 1, 1])
            with mid:
                if st.button("▶️ START GAME", use_container_width=True, type="primary"):
                    state.update_game_session(st.session_state.join_code, {
                        "status": "running",
                        "current_round": 0,
                        "round_locked": False,
                        "round_timer_end": None
                    })
                    
                    state.advance_round(st.session_state.join_code)
                    
                    duration = game["settings"]["round_duration"]
                    state.start_round_timer(st.session_state.join_code, duration)
                    
                    st.success(f"✅ Game started! Round 1 timer: {duration}s")
                    time.sleep(0.8)
                    st.rerun()

with tab2:
    st.markdown("### 🎮 Round Control")
    
    if game["status"] != "running":
        st.info("ℹ️ Start the game first from Team Management tab")
    else:
        st.markdown(f"""
        <div style="text-align: center;">
            <span class="round-badge">Round {game['current_round']} / {game['settings']['num_rounds']}</span>
        </div>
        """, unsafe_allow_html=True)
        
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
            
            if game["settings"]["auto_lock"] and not game["round_locked"]:
                state.lock_round(st.session_state.join_code)
                st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            lock_status = "🔒 LOCKED" if game["round_locked"] else "🔓 UNLOCKED"
            st.markdown(f"""
            <div class="admin-card">
                <h3 style="color: #667eea;">Round Status</h3>
                <p style="font-size: 24px; font-weight: 800; color: #333; margin: 6px 0 0 0;">
                    {lock_status}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            current_round = game.get("current_round", 1)
            saved_count = sum(1 for t in game["teams"].values() if t.get("decision_saved_round") == current_round)
            total_teams = len(game["teams"])
            all_saved = (total_teams > 0 and saved_count == total_teams)
            
            st.markdown(f"""
            <div class="admin-card">
                <h3 style="color: #667eea;">Decisions Saved</h3>
                <p style="font-size: 24px; font-weight: 800; color: {'#00ff88' if all_saved else '#ffa502'}; margin: 6px 0 0 0;">
                    {saved_count} / {total_teams}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        if game["teams"]:
            current_round = game.get("current_round", 1)
            missing = [name for name, t in game["teams"].items() if t.get("decision_saved_round") != current_round]
            if missing:
                st.info("⏳ Waiting on: " + ", ".join(missing))
            else:
                st.success("✅ All teams have saved decisions!")
        
        st.markdown("---")
        
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
            if (not timer_active) or (remaining <= 0):
                if st.button("▶️ Start Timer", use_container_width=True, type="primary", key="start_timer_btn"):
                    duration = game["settings"]["round_duration"]
                    state.start_round_timer(st.session_state.join_code, duration)
                    st.success(f"✅ Timer started: {duration}s")
                    time.sleep(0.5)
                    st.rerun()
            else:
                if st.button("⏹️ Stop Timer", use_container_width=True, key="stop_timer_btn"):
                    state.update_game_session(st.session_state.join_code, {"round_timer_end": None})
                    st.success("✅ Timer stopped")
                    time.sleep(0.5)
                    st.rerun()
        
        st.markdown("---")
        
        btn1, btn2 = st.columns(2)
        
        with btn1:
            if game["round_locked"]:
                if st.button("🔓 Unlock Round", use_container_width=True):
                    state.unlock_round(st.session_state.join_code)
                    st.rerun()
            else:
                if st.button("🔒 Lock Round", use_container_width=True):
                    state.lock_round(st.session_state.join_code)
                    st.rerun()
        
        with btn2:
            if game["current_round"] < game["settings"]["num_rounds"]:
                if st.button("⏭️ Next Round", use_container_width=True, type="primary"):
                    state.advance_round(st.session_state.join_code)
                    
                    duration = game["settings"]["round_duration"]
                    state.start_round_timer(st.session_state.join_code, duration)
                    
                    st.success("✅ Next round started! Timer running.")
                    time.sleep(0.8)
                    st.rerun()
            else:
                if st.button("🏁 Finish Game", use_container_width=True, type="primary"):
                    state.process_current_round(st.session_state.join_code)
                    
                    state.update_game_session(st.session_state.join_code, {
                        "status": "finished",
                        "round_locked": True,
                        "round_timer_end": None
                    })
                    
                    st.success("🎉 Game finished! Final results saved.")
                    time.sleep(0.8)
                    st.rerun()