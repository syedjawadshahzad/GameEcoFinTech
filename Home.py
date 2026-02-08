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

# Page config
st.set_page_config(
    page_title="Economics Games",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize user session
state.init_user_session()

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500&display=swap');
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: white;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 16px;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .game-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    .qr-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 10px;
    }
    
    .team-link {
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
</style>
""", unsafe_allow_html=True)

def generate_qr_code(url: str) -> str:
    """Generate QR code and return as base64 image"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        st.error(f"Error generating QR code: {e}")
        return ""

def show_admin_login():
    """Show admin login screen"""
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="font-size: 64px; margin: 0;">🎮 Economics Games</h1>
        <p style="color: white; font-size: 24px; margin: 20px 0;">
            University of Waikato | 2026
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="game-card">
            <h2 style="color: #667eea; text-align: center;">👨‍💼 Admin Login</h2>
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
    """Show game creation form for authenticated admin"""
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
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
        else:  # beat_market
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Create Game & Generate QR Codes", use_container_width=True, type="primary"):
            # Create game session with auto-generated admin name
            admin_name = f"Admin_{game_type[:5]}_{int(time.time()) % 10000}"
            join_code = state.create_game_session(game_type, admin_name, settings)
            team_codes = state.generate_team_codes(join_code, num_teams)
            
            state.set_user_as_admin(admin_name, join_code)
            
            # Store for display
            st.session_state.team_codes = team_codes
            st.session_state.game_join_code = join_code
            st.session_state.game_type = game_type
            st.session_state.show_qr_codes = True
            
            st.success("✅ Game created successfully!")
            st.balloons()
            st.rerun()

def show_qr_codes():
    """Display QR codes and links for each team"""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1>🎉 Game Created!</h1>
    </div>
    """, unsafe_allow_html=True)

    # Get deployed base URL
    origin = st_javascript("await window.location.origin")
    base_url = origin or "http://localhost:8501"

    # Build all team URLs
    team_codes_list = list(st.session_state.team_codes.items())
    all_team_urls = []

    # Grid layout
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
                # Small team label
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        font-size:18px;
                        font-weight:600;
                        color:#c7d2fe;
                        margin-bottom:6px;
                    ">
                        Team {team_slot}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # QR Code
                st.image(qr_img, width=200)

                # Link display
                st.code(team_url, language=None)

                # Status
                status_text = "✅ Joined" if info["assigned"] else "⏳ Waiting"
                status_color = "#00ff88" if info["assigned"] else "#ffa502"
                st.markdown(
                    f"""
                    <p style="
                        text-align:center;
                        font-size:14px;
                        color:{status_color};
                        font-weight:bold;
                        margin-top:6px;
                    ">
                        {status_text}
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Combined links section for easy sharing
    st.markdown("### 📋 All Team Links (Copy & Share)")
    combined_links = "\n".join(all_team_urls)
    st.code(combined_links, language=None)

    st.markdown("---")

    # Footer actions
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
    """Show team join screen when accessed via QR code"""
    # Get team code from URL parameters
    try:
        team_code = st.query_params.get("team_code", "")
        if isinstance(team_code, list):
            team_code = team_code[0] if team_code else ""
    except:
        # Fallback for older Streamlit versions
        team_code = ""
    
    team_code = team_code.upper()
    
    if not team_code:
        st.error("❌ Invalid access link. Please scan the QR code provided by your teacher.")
        st.stop()
    
    # Find the game this team code belongs to
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
    
    # Check if already joined
    if team_info["assigned"]:
        st.info(f"✅ This team has already joined as: **{team_info['team_name']}**")
        st.markdown("Click below to go to the game!")
        
        if st.button("🎮 Go to Team Page", use_container_width=True, type="primary"):
            state.set_user_as_team(team_info['team_name'], found_game_code)
            st.switch_page("pages/2_Team.py")
        st.stop()
    
    # Show join form
    game_names = {
        "build_country": "🌍 Build a Country",
        "beat_market": "📈 Beat the Market",
        "crypto_crash": "₿ Crypto Crash or Boom?"
    }
    
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="font-size: 56px; margin: 0;">👥 Join Game</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div class="game-card">
            <h2 style="color: #667eea; text-align: center;">{game_names.get(found_game['game_type'], 'Game')}</h2>
            <p style="color: #666; text-align: center; font-size: 24px;">
                <strong>Team {team_info['team_slot']}</strong>
            </p>
            <p style="color: #999; text-align: center;">
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
                st.success(f"✅ Joined successfully!")
                st.balloons()
                time.sleep(2)
                st.switch_page("pages/2_Team.py")
            else:
                st.error(f"❌ {message}")

# Sidebar
with st.sidebar:
       
    if st.session_state.get('admin_authenticated'):
        st.markdown("---")
        st.markdown("## 👨‍💼 Admin")
        st.success("✅ Authenticated")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_authenticated = False
            if 'show_qr_codes' in st.session_state:
                del st.session_state.show_qr_codes
            st.rerun()

# Main routing logic
try:
    has_team_code = "team_code" in st.query_params
except:
    has_team_code = False

if has_team_code:
    # Student accessing via QR code
    show_team_join()
elif st.session_state.get('admin_authenticated'):
    if st.session_state.get('show_qr_codes'):
        show_qr_codes()
    else:
        show_game_creation()
else:
    # Show admin login
    show_admin_login()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: white; padding: 20px;">
    <p style="font-size: 14px;">🎓 University of Waikato | 2026</p>
</div>
""", unsafe_allow_html=True)