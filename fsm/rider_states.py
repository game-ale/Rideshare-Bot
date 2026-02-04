"""
Rider FSM states for the Rideshare Bot.
Manages rider interaction flow and state transitions.
"""
from telegram.ext import ConversationHandler

# Rider conversation states
RIDER_IDLE = 0
RIDER_REQUESTING_RIDE = 1
RIDER_WAITING_DRIVER = 2
RIDER_RIDE_ASSIGNED = 3
RIDER_ONGOING_RIDE = 4
RIDER_RATING_DRIVER = 5

# State descriptions for debugging
STATE_NAMES = {
    RIDER_IDLE: "IDLE",
    RIDER_REQUESTING_RIDE: "REQUESTING_RIDE",
    RIDER_WAITING_DRIVER: "WAITING_DRIVER",
    RIDER_RIDE_ASSIGNED: "RIDE_ASSIGNED",
    RIDER_ONGOING_RIDE: "ONGOING_RIDE",
    RIDER_RATING_DRIVER: "RATING_DRIVER",
    ConversationHandler.END: "END"
}


def get_state_name(state: int) -> str:
    """Get human-readable state name for logging."""
    return STATE_NAMES.get(state, f"UNKNOWN({state})")
