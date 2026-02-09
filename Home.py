"""
Economics Games - Multi-Page Streamlit App
"""

import streamlit as st
import shared_state as state
import config
import qrcode
from io import BytesIO
import base64
import time
from streamlit_javascript import st_javascript

st.set_page_config(
    page_title="Economics Games",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

state.init_user_session()
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500&display=swap');.main {
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
        margin: 0.4rem 0 !important;
    }

    p { margin: 0.2rem 0 !important; }.stButton>button {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 0.55rem 1.15rem;
        font-size: 16px;
        transition: transform 0.2s;
    }.stButton>button:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }.game-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 18px;
        padding: 22px;
        margin: 10px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }.qr-card {
        background: white;
        border-radius: 16px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 10px;
    }.team-link {
        background: #000000;
        color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 11px;
        word-break: break-all;
        margin: 10px 0;
        border: 1px solid rgba(255,255,255,0.2);
    }

    /* ✅ FIXED: Sidebar text now BLACK and visible */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.95) !important;
        border-right: 1px solid rgba(0,0,0,0.1);
    }
    
    section[data-testid="stSidebar"] * {
        color: #111111 !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] hr {
        border: none;
        border-top: 2px solid rgba(0,0,0,0.15);
        margin: 10px 0;
    }
    
    section[data-testid="stSidebar"].stMarkdown {
        color: #222222 !important;
    }
    
    /* ✅ NEW: Clickable QR code styling */.qr-clickable {
        display: inline-block;
        transition: transform 0.2s;
        cursor: pointer;
    }.qr-clickable:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)


def _get_query_param(name: str) -> str:
    try:
        v = st.query_params.get(name, "")
        if isinstance(v, list):
            return (v[0] if v else "").strip()
        return str(v).strip()
    except Exception:
        return ""


def generate_qr_code(url: str) -> str:
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        st.error(f"Error generating QR code: {e}")
        return ""


def show_admin_login():
    st.markdown("""
    <div style="text-align: center; padding: 26px 0 12px 0;">
        <h1 style="font-size: 56px; margin: 0;">🎮 Economics Games</h1>
        <p style="color: white; font-size: 20px; margin: 10px 0 0 0;">
            University of Waikato | 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="game-card">
            <h2 style="color: #667eea; text-align: center; margin-top: 0;">👨‍💼 Admin Login</h2>
            <p style="color: #666; text-align: center;">
                Enter admin password to create a game session
            </p>
        </div>
        """, unsafe_allow_html=True)

        admin_password = st.text_input(
            "Admin Password",
            type="password",
            key="admin_password",
            help="Contact your teacher for the admin password"
        )

        if admin_password:
            if admin_password == config.ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid admin password!")


def show_game_creation():
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 4px 0;">
        <h1>🎮 Create Game Session</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        st.markdown("### Select Game Type")
        game_type = st.selectbox(
            "Game",
            options=[
                ("build_country", "🌍 Build a Country - Economics & Policy"),
                ("beat_market", "📈 Beat the Market - Investment & Finance"),
                ("crypto_crash", "₿ Crypto Crash or Boom - Fintech & Risk")
            ],
            format_func=lambda x: x[1]
        )
        game_type = game_type[0]

        st.markdown("### Number of Teams")
        num_teams = st.number_input(
            "How many teams?",
            min_value=1,
            max_value=8,
            value=2,
            help="Each team will get a unique QR code"
        )

        st.markdown("### Game Settings")

        if game_type == "build_country":
            num_rounds = st.slider("Number of Rounds", 1, 4, 2)
            round_duration = st.slider("Round Duration (seconds)", 60, 300, 180)
            auto_lock = st.checkbox("Auto-lock rounds when timer expires", value=True)
            settings = {
                "num_rounds": num_rounds,
                "round_duration": round_duration,
                "auto_lock": auto_lock,
                "num_teams": num_teams
            }

        elif game_type == "crypto_crash":
            num_rounds = st.slider("Number of Rounds", 1, 4, 2)
            round_duration = st.slider("Round Duration (seconds)", 60, 300, 180)
            auto_lock = st.checkbox("Auto-lock rounds when timer expires", value=True)
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
            settings = {
                "num_rounds": num_rounds,
                "round_duration": round_duration,
                "auto_lock": auto_lock,
                "difficulty": difficulty,
                "num_teams": num_teams
            }

        else:
            num_rounds = st.slider("Number of Rounds", 1, 4, 2)
            round_duration = st.slider("Round Duration (seconds)", 60, 300, 180)
            auto_lock = st.checkbox("Auto-lock rounds when timer expires", value=True)
            esg_mode = st.checkbox("Enable ESG Mode", value=False)
            settings = {
                "num_rounds": num_rounds,
                "round_duration": round_duration,
                "auto_lock": auto_lock,
                "esg_mode": esg_mode,
                "num_teams": num_teams
            }

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("🚀 Create Game & Generate QR Codes", use_container_width=True, type="primary"):
            admin_name = f"Admin_{game_type[:5]}_{int(time.time()) % 10000}"
            join_code = state.create_game_session(game_type, admin_name, settings)
            team_codes = state.generate_team_codes(join_code, num_teams)

            state.set_user_as_admin(admin_name, join_code)

            st.session_state.team_codes = team_codes
            st.session_state.game_join_code = join_code
            st.session_state.game_type = game_type
            st.session_state.show_qr_codes = True

            st.success("✅ Game created successfully!")
            st.balloons()
            st.rerun()


def show_qr_codes():
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 4px 0;">
        <h1>🎉 Game Created!</h1>
    </div>
    """, unsafe_allow_html=True)

    origin = st_javascript("await window.location.origin")
    base_url = origin or "http://localhost:8501"

    team_codes_list = list(st.session_state.team_codes.items())
    all_team_urls = []

    cols_per_row = 3

    for i in range(0, len(team_codes_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j >= len(team_codes_list):
                continue

            code, info = team_codes_list[i + j]
            team_slot = info["team_slot"]
            team_url = f"{base_url}/?team_code={code}"
            all_team_urls.append(f"Team {team_slot}: {team_url}")
            qr_img = generate_qr_code(team_url)

            with col:
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        font-size:18px;
                        font-weight:800;
                        color:#c7d2fe;
                        margin-bottom:6px;
                    ">
                        Team {team_slot}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # ✅ FIXED: Clickable QR code with link
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <a href="{team_url}" target="_blank" class="qr-clickable">
                            <img src="{qr_img}" width="200" style="border-radius: 12px; border: 3px solid #667eea;">
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Show URL for reference (not for copying)
                st.markdown(
                    f"""
                    <div style="
                        background: rgba(255,255,255,0.15);
                        padding: 8px;
                        border-radius: 8px;
                        margin-top: 10px;
                        text-align: center;
                    ">
                        <a href="{team_url}" target="_blank" style="
                            color: #c7d2fe;
                            text-decoration: none;
                            font-size: 11px;
                            font-family: monospace;
                            word-break: break-all;
                        ">
                            🔗 Click QR or this link
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                status_text = "✅ Joined" if info["assigned"] else "⏳ Waiting"
                status_color = "#00ff88" if info["assigned"] else "#ffa502"
                st.markdown(
                    f"""
                    <p style="
                        text-align:center;
                        font-size:14px;
                        color:{status_color};
                        font-weight:800;
                        margin-top:6px;
                    ">
                        {status_text}
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    st.markdown("### 📋 All Team Links (for sharing)")
    st.code("\n".join(all_team_urls), language=None)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🔄 Refresh Status", use_container_width=True):
                game = state.get_game_session(st.session_state.game_join_code)
                if game:
                    st.session_state.team_codes = game["team_codes"]
                st.rerun()

        with col_b:
            if st.button("📊 Go to Admin Panel", use_container_width=True, type="primary"):
                st.session_state.show_qr_codes = False
                st.switch_page("pages/1_Admin.py")


def show_team_join():
    team_code = _get_query_param("team_code").upper()

    if not team_code:
        st.error("❌ Invalid access link. Please scan the QR code provided by your teacher.")
        st.stop()

    all_games = state.get_all_game_sessions()
    found_game = None
    found_game_code = None
    team_info = None

    for game_code, game_data in all_games.items():
        if game_data.get("team_codes") and team_code in game_data["team_codes"]:
            found_game = game_data
            found_game_code = game_code
            team_info = game_data["team_codes"][team_code]
            break

    if not found_game:
        st.error("❌ This team code is not valid or the game has been deleted.")
        st.stop()

    if team_info["assigned"]:
        st.info(f"✅ This team has already joined as: **{team_info['team_name']}**")
        st.markdown("Click below to go to the game!")

        if st.button("🎮 Go to Team Page", use_container_width=True, type="primary"):
            state.set_user_as_team(team_info["team_name"], found_game_code)
            st.switch_page("pages/2_Team.py")
        st.stop()

    game_names = {
        "build_country": "🌍 Build a Country",
        "beat_market": "📈 Beat the Market",
        "crypto_crash": "₿ Crypto Crash or Boom?"
    }

    st.markdown("""
    <div style="text-align: center; padding: 22px 0 10px 0;">
        <h1 style="font-size: 52px; margin: 0;">👥 Join Game</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(f"""
        <div class="game-card">
            <h2 style="color: #667eea; text-align: center; margin-top: 0;">{game_names.get(found_game['game_type'], 'Game')}</h2>
            <p style="color: #666; text-align: center; font-size: 22px; margin: 6px 0 0 0;">
                <strong>Team {team_info['team_slot']}</strong>
            </p>
            <p style="color: #999; text-align: center; margin: 8px 0 0 0;">
                Enter your team name to join
            </p>
        </div>
        """, unsafe_allow_html=True)

        team_name = st.text_input(
            "Team Name",
            key="team_name_join",
            placeholder="e.g., Awesome Economists",
            max_chars=30
        )

        if st.button("🚀 Join Game", use_container_width=True, type="primary", disabled=not team_name):
            success, message, team_slot = state.add_team_to_game(
                found_game_code,
                team_name,
                team_code
            )

            if success:
                state.set_user_as_team(team_name, found_game_code)
                st.success("✅ Joined successfully!")
                st.balloons()
                time.sleep(1.2)
                st.switch_page("pages/2_Team.py")
            else:
                st.error(f"❌ {message}")


with st.sidebar:
    if st.session_state.admin_authenticated:
        st.markdown("---")
        st.markdown("## 👨‍💼 Admin")
        st.success("✅ Authenticated")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_authenticated = False

            for k in ["show_qr_codes", "team_codes", "game_join_code", "game_type"]:
                if k in st.session_state:
                    del st.session_state[k]

            st.rerun()


has_team_code = bool(_get_query_param("team_code"))

if has_team_code:
    show_team_join()
elif st.session_state.admin_authenticated:
    if st.session_state.get("show_qr_codes"):
        show_qr_codes()
    else:
        show_game_creation()
else:
    show_admin_login()

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: white; padding: 12px 0 4px 0;">
    <p style="font-size: 14px;">🎓 University of Waikato | 2026</p>
</div>
""", unsafe_allow_html=True)