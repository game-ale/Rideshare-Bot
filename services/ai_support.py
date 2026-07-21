"""
AI Support Service for the Rideshare Bot.
Provides intelligent support responses, ride issue analysis, driver quality insights,
and demand forecasting using rule-based AI logic.

Note: In production, this would integrate with OpenAI/Gemini API.
For the portfolio demo, we use deterministic, rule-based intelligence
that demonstrates the product thinking behind AI-assisted operations.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import random


# ==================== Support Categories ====================

SUPPORT_CATEGORIES = {
    "driver_late": {
        "keywords": ["late", "waiting", "not here", "where is", "taking long", "delayed"],
        "response": (
            "⏳ <b>Driver Running Late</b>\n\n"
            "We understand the inconvenience. Here's what you can do:\n\n"
            "1️⃣ Check your ride status — the driver may be in traffic.\n"
            "2️⃣ Contact the driver directly via the app.\n"
            "3️⃣ If the driver doesn't arrive in 5 minutes, you can cancel for free.\n\n"
            "💡 <i>Tip: Sharing a precise GPS pin helps drivers find you faster.</i>"
        ),
        "risk_level": "LOW",
        "suggested_action": "Monitor — auto-resolves in most cases",
    },
    "wrong_pickup": {
        "keywords": ["wrong location", "wrong place", "wrong pickup", "different location", "not my location"],
        "response": (
            "📍 <b>Wrong Pickup Location</b>\n\n"
            "It seems there's a mismatch. Please try:\n\n"
            "1️⃣ Share your exact GPS location to the driver.\n"
            "2️⃣ Describe a nearby landmark.\n"
            "3️⃣ Cancel and re-request with the correct pickup pin.\n\n"
            "💡 <i>Tip: Use the 'Share Location' button for the most accurate results.</i>"
        ),
        "risk_level": "LOW",
        "suggested_action": "No admin action needed",
    },
    "payment_issue": {
        "keywords": ["payment", "pay", "charge", "wallet", "money", "refund", "overcharged", "fare"],
        "response": (
            "💳 <b>Payment Support</b>\n\n"
            "We're here to help with your payment concern:\n\n"
            "• If you were <b>overcharged</b>, please note the ride ID — an admin will review it.\n"
            "• For <b>wallet issues</b>, check your balance in the 💳 Wallet menu.\n"
            "• For <b>refund requests</b>, an admin will process it within 24 hours.\n\n"
            "⚠️ <i>This issue has been flagged for admin review.</i>"
        ),
        "risk_level": "MEDIUM",
        "suggested_action": "Review fare breakdown and issue refund if overcharged",
    },
    "lost_item": {
        "keywords": ["lost", "forgot", "left", "item", "phone", "bag", "belongings"],
        "response": (
            "📦 <b>Lost Item Report</b>\n\n"
            "We'll help you recover your item:\n\n"
            "1️⃣ Your report has been logged.\n"
            "2️⃣ The driver from your last ride will be notified.\n"
            "3️⃣ If found, we'll coordinate the return.\n\n"
            "💡 <i>Include your ride ID for faster resolution.</i>\n\n"
            "⚠️ <i>This issue has been escalated to the admin team.</i>"
        ),
        "risk_level": "MEDIUM",
        "suggested_action": "Contact driver from last ride — coordinate item return",
    },
    "safety_concern": {
        "keywords": ["unsafe", "dangerous", "accident", "emergency", "threat", "scared", "help me", "safety"],
        "response": (
            "🚨 <b>Safety Alert</b>\n\n"
            "Your safety is our top priority.\n\n"
            "🔴 If you are in <b>immediate danger</b>, call <b>911</b> or your local emergency number.\n\n"
            "This report has been <b>immediately escalated</b> to the admin team.\n"
            "An admin will contact you as soon as possible.\n\n"
            "⚠️ <i>HIGH PRIORITY — Admin notified.</i>"
        ),
        "risk_level": "HIGH",
        "suggested_action": "IMMEDIATE: Contact user, review ride details, suspend driver if needed",
    },
    "rider_not_responding": {
        "keywords": ["no response", "not responding", "can't reach", "no answer", "rider gone"],
        "response": (
            "📵 <b>Unresponsive Rider</b>\n\n"
            "If the rider is not at the pickup location:\n\n"
            "1️⃣ Wait at least 3 minutes.\n"
            "2️⃣ Try sending a message through the app.\n"
            "3️⃣ If no response, you may cancel without penalty.\n\n"
            "💡 <i>A cancellation fee may apply to the rider.</i>"
        ),
        "risk_level": "LOW",
        "suggested_action": "Allow driver to cancel after waiting period",
    },
    "general": {
        "keywords": [],
        "response": (
            "💬 <b>Support</b>\n\n"
            "Thank you for reaching out! Here are some things I can help with:\n\n"
            "• 🚗 <b>Driver issues</b> — late, wrong location, behavior\n"
            "• 💳 <b>Payment</b> — charges, refunds, wallet\n"
            "• 📦 <b>Lost items</b> — forgot something in the car\n"
            "• 🚨 <b>Safety</b> — feel unsafe, emergency\n\n"
            "Please describe your issue and I'll assist you right away."
        ),
        "risk_level": "LOW",
        "suggested_action": "Awaiting user clarification",
    },
}


def classify_support_query(text: str) -> str:
    """Classify a support message into a category using keyword matching."""
    text_lower = text.lower()
    
    # Check each category's keywords
    best_match = "general"
    best_score = 0
    
    for category, config in SUPPORT_CATEGORIES.items():
        if category == "general":
            continue
        score = sum(1 for kw in config["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = category
    
    return best_match


def get_support_response(text: str) -> Dict:
    """Get an AI support response for a user query."""
    category = classify_support_query(text)
    config = SUPPORT_CATEGORIES[category]
    
    return {
        "category": category,
        "response": config["response"],
        "risk_level": config["risk_level"],
        "suggested_action": config["suggested_action"],
        "escalated": config["risk_level"] in ["MEDIUM", "HIGH"],
    }


# ==================== Ride Issue Analysis ====================

def analyze_ride_issue(ride_data: dict) -> Dict:
    """
    Generate an AI summary of a ride issue for admin review.
    In production, this would use an LLM to analyze the full context.
    """
    status = ride_data.get("status", "UNKNOWN")
    rating = ride_data.get("rating")
    distance = ride_data.get("distance", 0)
    fare = ride_data.get("final_fare") or ride_data.get("estimated_fare", 0)
    created_at = ride_data.get("created_at")
    completed_at = ride_data.get("completed_at")
    
    # Calculate duration if dates available
    duration_str = "Unknown"
    duration_minutes = 0
    if created_at and completed_at:
        try:
            start = datetime.fromisoformat(created_at)
            end = datetime.fromisoformat(completed_at)
            duration_minutes = (end - start).total_seconds() / 60
            duration_str = f"{duration_minutes:.0f} min"
        except (ValueError, TypeError):
            pass
    
    # Build analysis
    issues = []
    risk_level = "LOW"
    
    if status == "CANCELLED":
        issues.append("Ride was cancelled — check if rider or driver initiated")
        risk_level = "MEDIUM"
    
    if rating and rating <= 2:
        issues.append(f"Very low rating ({rating}/5) — rider was likely dissatisfied")
        risk_level = "MEDIUM"
    
    if duration_minutes > 60 and distance and distance < 5:
        issues.append("Unusually long duration for short distance — potential route manipulation")
        risk_level = "HIGH"
    
    if fare and fare > 500:
        issues.append(f"High fare ({fare:.0f} ETB) — verify surge pricing was appropriate")
    
    if not issues:
        issues.append("No issues detected — ride appears normal")
    
    summary = {
        "ride_id": ride_data.get("id"),
        "summary": " | ".join(issues),
        "risk_level": risk_level,
        "duration": duration_str,
        "recommended_actions": [],
    }
    
    if risk_level == "HIGH":
        summary["recommended_actions"].append("Review ride details immediately")
        summary["recommended_actions"].append("Contact both rider and driver")
    elif risk_level == "MEDIUM":
        summary["recommended_actions"].append("Review during daily audit")
    else:
        summary["recommended_actions"].append("No action required")
    
    return summary


# ==================== Driver Quality Insights ====================

def generate_driver_insights(driver_data: dict) -> List[Dict]:
    """
    Generate AI-powered quality insights for a driver.
    Analyzes rating, ride count, and activity patterns.
    """
    insights = []
    
    rating = driver_data.get("rating", 5.0)
    total_rides = driver_data.get("total_rides", 0)
    status = driver_data.get("status", "APPROVED")
    available = driver_data.get("available", False)
    wallet = driver_data.get("wallet_balance", 0)
    
    # Rating insights
    if rating >= 4.8:
        insights.append({
            "type": "positive",
            "icon": "⭐",
            "title": "Excellent Rating",
            "detail": f"Rating of {rating:.1f}/5.0 is in the top tier. Keep it up!",
            "metric": f"{rating:.1f}",
        })
    elif rating >= 4.0:
        insights.append({
            "type": "neutral",
            "icon": "📊",
            "title": "Good Rating",
            "detail": f"Rating of {rating:.1f}/5.0 is solid. Focus on small improvements.",
            "metric": f"{rating:.1f}",
        })
    elif rating < 4.0 and total_rides > 5:
        insights.append({
            "type": "warning",
            "icon": "⚠️",
            "title": "Low Rating Alert",
            "detail": f"Rating of {rating:.1f}/5.0 needs attention. Review recent feedback.",
            "metric": f"{rating:.1f}",
        })
    
    # Activity insights
    if total_rides == 0:
        insights.append({
            "type": "warning",
            "icon": "🆕",
            "title": "New Driver",
            "detail": "This driver hasn't completed any rides yet.",
            "metric": "0 rides",
        })
    elif total_rides > 50:
        insights.append({
            "type": "positive",
            "icon": "🏆",
            "title": "Experienced Driver",
            "detail": f"Completed {total_rides} rides — a veteran on the platform.",
            "metric": f"{total_rides} rides",
        })
    elif total_rides > 10:
        insights.append({
            "type": "neutral",
            "icon": "📈",
            "title": "Growing Activity",
            "detail": f"Completed {total_rides} rides and building experience.",
            "metric": f"{total_rides} rides",
        })
    
    # Status insights
    if status == "PENDING":
        insights.append({
            "type": "action",
            "icon": "📋",
            "title": "Needs Document Review",
            "detail": "Driver application is pending — review license and vehicle docs.",
            "metric": "PENDING",
        })
    elif status == "SUSPENDED":
        insights.append({
            "type": "warning",
            "icon": "🚫",
            "title": "Account Suspended",
            "detail": "This driver's account is currently suspended. Review suspension reason.",
            "metric": "SUSPENDED",
        })
    
    # Availability insight
    if status == "APPROVED" and not available:
        insights.append({
            "type": "neutral",
            "icon": "💤",
            "title": "Currently Offline",
            "detail": "Driver is approved but not currently accepting rides.",
            "metric": "OFFLINE",
        })
    
    # Earnings insight
    if wallet > 1000:
        insights.append({
            "type": "positive",
            "icon": "💰",
            "title": "Strong Earnings",
            "detail": f"Wallet balance of {wallet:.0f} ETB indicates active earning.",
            "metric": f"{wallet:.0f} ETB",
        })
    
    return insights


# ==================== Demand Forecasting ====================

def generate_demand_forecast() -> Dict:
    """
    Generate a simulated demand forecast for demo purposes.
    In production, this would analyze historical ride data patterns.
    """
    current_hour = datetime.now().hour
    
    # Simulated hourly demand pattern (typical for a city like Addis Ababa)
    hourly_demand = {
        0: 5, 1: 3, 2: 2, 3: 2, 4: 3, 5: 8,
        6: 25, 7: 45, 8: 60, 9: 40, 10: 30, 11: 35,
        12: 50, 13: 45, 14: 30, 15: 35, 16: 45, 17: 65,
        18: 70, 19: 55, 20: 40, 21: 30, 22: 20, 23: 10,
    }
    
    # Generate forecast for next 12 hours
    forecast_hours = []
    for i in range(12):
        hour = (current_hour + i) % 24
        base_demand = hourly_demand.get(hour, 20)
        # Add some randomness for realism
        actual = max(0, base_demand + random.randint(-5, 5))
        forecast_hours.append({
            "hour": f"{hour:02d}:00",
            "predicted_rides": actual,
            "demand_level": "HIGH" if actual > 50 else "MEDIUM" if actual > 25 else "LOW",
        })
    
    # Hotspot areas (simulated for Addis Ababa)
    hotspots = [
        {"area": "Bole", "lat": 9.0107, "lng": 38.7612, "demand": "HIGH", "drivers_needed": 8},
        {"area": "Piassa", "lat": 9.0350, "lng": 38.7480, "demand": "MEDIUM", "drivers_needed": 4},
        {"area": "Megenagna", "lat": 9.0200, "lng": 38.7900, "demand": "HIGH", "drivers_needed": 6},
        {"area": "Mexico", "lat": 9.0050, "lng": 38.7400, "demand": "LOW", "drivers_needed": 2},
        {"area": "CMC", "lat": 9.0400, "lng": 38.8200, "demand": "MEDIUM", "drivers_needed": 3},
    ]
    
    # Peak time prediction
    peak_hour = max(forecast_hours, key=lambda x: x["predicted_rides"])
    
    return {
        "generated_at": datetime.now().isoformat(),
        "current_hour": f"{current_hour:02d}:00",
        "forecast": forecast_hours,
        "hotspots": hotspots,
        "peak_prediction": {
            "hour": peak_hour["hour"],
            "predicted_rides": peak_hour["predicted_rides"],
        },
        "recommendation": f"Deploy more drivers in Bole and Megenagna areas before {peak_hour['hour']}.",
    }


# ==================== AI Matching Explanation ====================

def explain_driver_match(driver_data: dict, distance: float) -> str:
    """
    Generate a human-readable explanation of why a driver was matched.
    Shows the matching algorithm's decision-making process.
    """
    reasons = []
    
    reasons.append(f"📍 <b>Proximity:</b> {distance:.1f} km away — closest available driver")
    
    rating = driver_data.get("rating", 5.0)
    if rating >= 4.5:
        reasons.append(f"⭐ <b>Rating:</b> {rating:.1f}/5.0 — excellent rider feedback")
    else:
        reasons.append(f"⭐ <b>Rating:</b> {rating:.1f}/5.0")
    
    vehicle = driver_data.get("vehicle_type", "Car")
    reasons.append(f"🚗 <b>Vehicle:</b> {vehicle} — suitable for this trip")
    
    total_rides = driver_data.get("total_rides", 0)
    if total_rides > 20:
        reasons.append(f"🏆 <b>Experience:</b> {total_rides} completed rides")
    
    return "\n".join(reasons)
