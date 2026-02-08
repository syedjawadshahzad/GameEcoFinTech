# 🎮 Economics, Finance & FinTech Games 

A complete game management system with admin controls, team join codes, and live scoreboards for three engaging games.

---

## 🌟 Features

### Admin Controls
- **🔐 Password-protected admin access** (NEW!)
- **Create game sessions** with custom settings
- **Generate unique join codes** for teams
- **Control round flow** with start/stop/lock capabilities
- **Monitor team readiness** in real-time
- **Manage teams** (add/remove)
- **View raw game data** for debugging

---

## 📁 Project Structure

```
GameEcoFinTech/
├── Home.py                 # Main entry point - game selection & join
├── shared_state.py         # Data persistence & state management
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
├── pages/
│   ├── 1_Admin.py         # Admin control panel
│   ├── 2_Team.py          # Team gameplay interface
│   └── 3_Scoreboard.py    # Live scoreboard display
└── README.md              # This file
```

---

## 🚀 Quick Start

### Installation

```bash
# Navigate to the project directory
cd economics_games

# Install dependencies
pip install -r requirements.txt

# IMPORTANT: Set admin password (open config.py and change line 13)
# Default password: "ASDF"

# Run the app
streamlit run Home.py
```

The app will open at `http://localhost:8501`

### 🔐 First-Time Setup

**CRITICAL:** Before using in class, change the admin password!

1. Open `config.py`
2. Find line 13: `ADMIN_PASSWORD = "ASDF"`
3. Change to your secure password
4. Save and restart app

See `ADMIN_SECURITY.md` for complete security guide.

### For Classroom Use

**Before Class:**
1. Start the app on a teacher computer
2. Ensure students can access the same network/URL

**During Class:**
1. **Admin** creates a game session (gets join code)
2. **Teams** join using the code
3. **Admin** starts the game when ready
4. **Teams** make decisions each round
5. **Everyone** watches scoreboard on projected screen

---

## 🎮 How to Use

### As Admin (Teacher/Facilitator)

1. **Go to Home page** → Choose your game
2. **Fill in admin name** and game settings
3. **Click "Create Game Session"**
4. **Share the join code** with teams (write on board)
5. **Go to Admin page** to control the game:
   - Wait for teams to join
   - Start the game when ready
   - Start timer for each round
   - Lock rounds when time expires
   - Advance to next round
   - Finish game when complete

**Admin Page Features:**
- **Team Management tab:** See who's joined, ready status, remove teams
- **Round Control tab:** Timer controls, lock/unlock, advance rounds

### As Team (Students)

1. **Go to Home page** → Choose the game your teacher selected
2. **Enter team name** and **join code** from teacher
3. **Click "Join Game"**
4. **Go to Team page** to play:
   - Wait for admin to start
   - Read the scenario/event
   - Discuss with your team
   - Make your decisions
   - Save decisions
   - Mark as "Ready"
   - Wait for next round

**Team Page Features:**
- Live timer display in sidebar
- Decision inputs (sliders, selects)
- Save button to lock in choices
- Ready checkbox to signal completion
- Can't edit after round is locked

### Scoreboard (Anyone)

- **Go to Scoreboard page**
- **Enter game code** (if not already in a session)
- **Watch live rankings** update automatically
- Perfect for projection during gameplay!

---

## 🎯 Game-Specific Details

### 🌍 Build a Country

**Team Decisions Each Round:**
- 💵 Tax Rate (10-50%)
- 📚 Education Spending (10-50%)
- 🏗️ Infrastructure Spending (10-50%)
- 🌱 Climate Policy (Weak/Moderate/Strong)

**Metrics Tracked:**
- 💰 GDP - Economic output
- 👷 Employment - Job rate
- ⚖️ Inequality - Wealth gap (lower is better)
- ❤️ Approval - Public support

**Scoring:** Weighted average of all metrics

**Admin Settings:**
- Number of rounds (3-5)
- Round duration (60-300 seconds)
- Auto-lock when timer expires

### 📈 Beat the Market

**Team Decisions Each Round:**
- 💵 Cash allocation (0-100%)
- 📊 Shares allocation (0-100%)
- ₿ Crypto allocation (0-100%)
- 🏦 Bonds allocation (0-100%)
- *(Must total 100%)*

**Metrics Tracked:**
- 💼 Portfolio Value
- 📊 Returns (%)
- ⚠️ Risk Score (0-100)
- 🎯 Risk-Adjusted Score
- 🌱 ESG Score (if enabled)

**Scoring:** Risk-Adjusted Returns = (Returns / Risk) × 100

**Admin Settings:**
- Number of rounds (4-8)
- Round duration (60-300 seconds)
- Auto-lock when timer expires
- ESG Mode (environmental/social/governance)

### ₿ Crypto Crash or Boom?

**Team Decisions Each Round:**
- 🎯 Action: Buy / Hold / Sell
- ⚠️ Risk Exposure (0-100%)

**Indicators Analyzed:**
- 😊 Market Sentiment (0-100)
- 📈 Trading Volume (0-100)
- 🔥 Social Media Hype (0-100)
- 💰 Current Price & Change

**Metrics Tracked:**
- 💰 Profit/Loss (%)
- ⚠️ Risk Score
- 🎯 Decision Accuracy
- ✅ Correct Predictions

**Scoring:** Profit + Risk Management Bonus + Accuracy Bonus

**Admin Settings:**
- Number of rounds (5-8)
- Round duration (45-180 seconds)
- Auto-lock when timer expires
- Difficulty (Easy/Medium/Hard)

**Special Features:**
- Unexpected crash events
- Market manipulation scenarios
- Bonus points for risk management
- Teaches fintech concepts

---

## 💡 Tips for Facilitators

### Before the Session

1. **Test run** - Play through once yourself
2. **Prepare classroom** - Ensure network access for all
3. **Print reference guides** - Quick rules for students
4. **Set up projection** - Scoreboard visible to all
5. **Have backup plan** - Paper-based if tech fails

### During the Session

**Timing:**
- 2 minutes: Explain game & share code
- 1 minute: Teams join
- 2-3 minutes per round: Decisions + processing
- 3 minutes: Final results discussion

**Round Flow:**
1. **Announce scenario** if applicable
2. **Start timer** (180 seconds recommended)
3. **Circulate** - listen to discussions
4. **30-second warning**
5. **Lock round** when timer expires
6. **Process** (game calculations)
7. **Show scoreboard** briefly
8. **Advance round**

**Engagement Tips:**
- Project scoreboard between rounds
- Ask teams to predict outcomes
- Encourage strategy debates
- Don't give answers - guide thinking
- Celebrate interesting strategies, not just winners

### After the Session

**Debrief Questions:**
- What strategy did the winning team use?
- What would you do differently?
- How does this apply to real economics?
- What trade-offs were hardest?
- What surprised you most?

**NZ Context:**
- Connect to KiwiSaver (Beat the Market)
- Discuss NZ government budgets (Build a Country)
- Reference recent local economic events

---

**Good luck with your economics games! 🎓📈🌍**

*Remember: The goal is learning through experience, not just winning the game!*
