"""
Unit tests for the AI Support Service.
Tests intent classification, response generation, and driver quality insights.
"""
import pytest
from services.ai_support import (
    classify_support_query,
    get_support_response,
    generate_driver_insights,
    generate_demand_forecast,
    analyze_ride_issue,
    SUPPORT_CATEGORIES,
)


class TestClassifySupportQuery:
    """Tests for AI intent classification."""

    def test_driver_late(self):
        assert classify_support_query("My driver is late") == "driver_late"

    def test_driver_late_variant(self):
        assert classify_support_query("I've been waiting for 10 minutes") == "driver_late"

    def test_wrong_pickup(self):
        assert classify_support_query("The driver went to the wrong location") == "wrong_pickup"

    def test_payment_issue(self):
        assert classify_support_query("I was overcharged for my ride") == "payment_issue"

    def test_refund_request(self):
        assert classify_support_query("I need a refund") == "payment_issue"

    def test_lost_item(self):
        assert classify_support_query("I left my phone in the car") == "lost_item"

    def test_lost_bag(self):
        assert classify_support_query("I forgot my bag") == "lost_item"

    def test_safety_concern(self):
        assert classify_support_query("I feel unsafe with this driver") == "safety_concern"

    def test_emergency(self):
        assert classify_support_query("There was an accident") == "safety_concern"

    def test_rider_not_responding(self):
        assert classify_support_query("The rider is not responding") == "rider_not_responding"

    def test_general_fallback(self):
        """Unrecognized queries should fall back to 'general'."""
        assert classify_support_query("Hello how are you") == "general"

    def test_empty_string(self):
        assert classify_support_query("") == "general"


class TestGetSupportResponse:
    """Tests for the full support response pipeline."""

    def test_response_has_required_keys(self):
        result = get_support_response("My driver is late")
        assert "category" in result
        assert "response" in result
        assert "risk_level" in result
        assert "suggested_action" in result
        assert "escalated" in result

    def test_safety_is_escalated(self):
        result = get_support_response("I feel unsafe help me")
        assert result["escalated"] is True
        assert result["risk_level"] == "HIGH"

    def test_late_driver_not_escalated(self):
        result = get_support_response("Driver is taking long")
        assert result["escalated"] is False
        assert result["risk_level"] == "LOW"

    def test_payment_is_escalated(self):
        result = get_support_response("I was overcharged")
        assert result["escalated"] is True
        assert result["risk_level"] == "MEDIUM"

    def test_response_contains_html(self):
        """Responses should contain HTML formatting for Telegram."""
        result = get_support_response("driver late")
        assert "<b>" in result["response"]


class TestGenerateDriverInsights:
    """Tests for driver quality insight generation."""

    def test_excellent_rating_insight(self):
        driver = {"rating": 4.9, "total_rides": 30, "status": "APPROVED", "available": True, "wallet_balance": 500}
        insights = generate_driver_insights(driver)
        titles = [i["title"] for i in insights]
        assert "Excellent Rating" in titles

    def test_low_rating_warning(self):
        driver = {"rating": 3.2, "total_rides": 20, "status": "APPROVED", "available": True, "wallet_balance": 100}
        insights = generate_driver_insights(driver)
        types = [i["type"] for i in insights]
        assert "warning" in types

    def test_new_driver_insight(self):
        driver = {"rating": 5.0, "total_rides": 0, "status": "PENDING", "available": False, "wallet_balance": 0}
        insights = generate_driver_insights(driver)
        titles = [i["title"] for i in insights]
        assert "New Driver" in titles

    def test_pending_driver_needs_review(self):
        driver = {"rating": 5.0, "total_rides": 0, "status": "PENDING", "available": False, "wallet_balance": 0}
        insights = generate_driver_insights(driver)
        titles = [i["title"] for i in insights]
        assert "Needs Document Review" in titles

    def test_experienced_driver(self):
        driver = {"rating": 4.5, "total_rides": 75, "status": "APPROVED", "available": True, "wallet_balance": 2000}
        insights = generate_driver_insights(driver)
        titles = [i["title"] for i in insights]
        assert "Experienced Driver" in titles

    def test_insights_have_required_fields(self):
        driver = {"rating": 4.5, "total_rides": 10, "status": "APPROVED", "available": True, "wallet_balance": 100}
        insights = generate_driver_insights(driver)
        for insight in insights:
            assert "type" in insight
            assert "icon" in insight
            assert "title" in insight
            assert "detail" in insight
            assert "metric" in insight


class TestGenerateDemandForecast:
    """Tests for demand forecasting."""

    def test_forecast_has_required_keys(self):
        forecast = generate_demand_forecast()
        assert "generated_at" in forecast
        assert "current_hour" in forecast
        assert "forecast" in forecast
        assert "hotspots" in forecast
        assert "peak_prediction" in forecast
        assert "recommendation" in forecast

    def test_forecast_has_12_hours(self):
        forecast = generate_demand_forecast()
        assert len(forecast["forecast"]) == 12

    def test_hotspots_not_empty(self):
        forecast = generate_demand_forecast()
        assert len(forecast["hotspots"]) > 0

    def test_peak_prediction_exists(self):
        forecast = generate_demand_forecast()
        assert "hour" in forecast["peak_prediction"]
        assert "predicted_rides" in forecast["peak_prediction"]


class TestAnalyzeRideIssue:
    """Tests for ride issue analysis."""

    def test_cancelled_ride_flagged(self):
        ride = {"id": 1, "status": "CANCELLED", "rating": None, "distance": 5, "estimated_fare": 200}
        result = analyze_ride_issue(ride)
        assert result["risk_level"] in ["MEDIUM", "HIGH"]

    def test_low_rating_flagged(self):
        ride = {"id": 2, "status": "COMPLETED", "rating": 1, "distance": 5, "estimated_fare": 200}
        result = analyze_ride_issue(ride)
        assert "low rating" in result["summary"].lower()

    def test_normal_ride_no_issues(self):
        ride = {"id": 3, "status": "COMPLETED", "rating": 5, "distance": 10, "estimated_fare": 300}
        result = analyze_ride_issue(ride)
        assert result["risk_level"] == "LOW"

    def test_result_has_required_keys(self):
        ride = {"id": 4, "status": "COMPLETED", "rating": 4}
        result = analyze_ride_issue(ride)
        assert "ride_id" in result
        assert "summary" in result
        assert "risk_level" in result
        assert "recommended_actions" in result
