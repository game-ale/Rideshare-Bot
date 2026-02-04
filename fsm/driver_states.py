"""
Driver FSM states for the Rideshare Bot.
Manages driver interaction flow and state transitions.
"""
from telegram.ext import ConversationHandler

# Driver conversation states
DRIVER_REGISTERING_NAME = 0
DRIVER_REGISTERING_VEHICLE = 1
DRIVER_IDLE = 2
DRIVER_CONFIRMING_RIDE = 3
DRIVER_ONGOING_RIDE = 4

# State descriptions for debugging
STATE_NAMES = {
    DRIVER_REGISTERING_NAME: "REGISTERING_NAME",
    DRIVER_REGISTERING_VEHICLE: "REGISTERING_VEHICLE",
    DRIVER_IDLE: "IDLE",
    DRIVER_CONFIRMING_RIDE: "CONFIRMING_RIDE",
    DRIVER_ONGOING_RIDE: "ONGOING_RIDE",
    ConversationHandler.END: "END"
}


def get_state_name(state: int) -> str:
    """Get human-readable state name for logging."""
    return STATE_NAMES.get(state, f"UNKNOWN({state})")
