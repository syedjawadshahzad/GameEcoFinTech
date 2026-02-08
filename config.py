"""
Configuration file for Economics Games
ADMIN PASSWORD SETTINGS
"""

# ============================================================================
# ADMIN PASSWORD CONFIGURATION
# ============================================================================

ADMIN_PASSWORD = "ASDF"

# ============================================================================
# GAME SETTINGS (Optional Customization)
# ============================================================================

# Default number of rounds for each game type
DEFAULT_ROUNDS = {
    "build_country": 3,
    "beat_market": 3,
    "crypto_crash": 3
}

# Default round duration in seconds
DEFAULT_DURATION = {
    "build_country": 180,  # 3 minutes
    "beat_market": 180,    
    "crypto_crash": 180     
}

# Auto-lock rounds when timer expires (recommended: True)
AUTO_LOCK_DEFAULT = True

# Maximum number of teams allowed per game
MAX_TEAMS = 8

# Minimum number of teams to start game
MIN_TEAMS = 1

# ============================================================================
# DATA STORAGE SETTINGS
# ============================================================================

# Where to store game data (change for production)
DATA_DIRECTORY = "/tmp/economics_games_data"

# How long to keep old game sessions (in hours)
SESSION_CLEANUP_HOURS = 24

# ============================================================================
# ADVANCED SETTINGS (Don't change unless you know what you're doing)
# ============================================================================

# Join code length (characters)
JOIN_CODE_LENGTH = 6

# Timer auto-refresh interval (seconds)
TIMER_REFRESH_INTERVAL = 3

# Scoreboard auto-refresh interval (seconds)
SCOREBOARD_REFRESH_INTERVAL = 3
