"""
Unit tests for the Pricing Engine.
Tests fare calculation, ETA estimation, and pricing constants.
"""
import pytest
from unittest.mock import patch
from services.pricing import (
    calculate_fare, calculate_eta, get_surge_multiplier,
    BASE_FARE, PER_KM_RATE, PER_MIN_RATE, MIN_FARE, AVERAGE_SPEED_KMH
)


class TestCalculateETA:
    """Tests for ETA calculation."""

    def test_short_distance(self):
        """1 km at 25 km/h should be ~2.4 min → rounds to 2."""
        eta = calculate_eta(1.0)
        assert eta == 2

    def test_medium_distance(self):
        """5 km at 25 km/h = 12 min."""
        eta = calculate_eta(5.0)
        assert eta == 12

    def test_long_distance(self):
        """20 km at 25 km/h = 48 min."""
        eta = calculate_eta(20.0)
        assert eta == 48

    def test_zero_distance_returns_minimum(self):
        """0 km should return at least 1 minute."""
        eta = calculate_eta(0.0)
        assert eta >= 1

    def test_very_short_distance_returns_minimum(self):
        """Very short distances should still return at least 1 minute."""
        eta = calculate_eta(0.01)
        assert eta >= 1

    def test_returns_integer(self):
        """ETA should always be an integer."""
        eta = calculate_eta(7.3)
        assert isinstance(eta, int)


class TestCalculateFare:
    """Tests for fare calculation logic."""

    @patch("services.pricing.get_surge_multiplier", return_value=1.0)
    def test_basic_fare_no_surge(self, mock_surge):
        """Test base fare calculation without surge pricing."""
        # 5 km, no surge
        # ETA = 12 min
        # BASE(50) + DISTANCE(5*20=100) + TIME(12*2=24) = 174
        fare = calculate_fare(5.0)
        assert fare == 174.0

    @patch("services.pricing.get_surge_multiplier", return_value=1.0)
    def test_minimum_fare_enforced(self, mock_surge):
        """Very short trips should still charge the minimum fare."""
        fare = calculate_fare(0.1)
        assert fare >= MIN_FARE

    @patch("services.pricing.get_surge_multiplier", return_value=2.0)
    def test_surge_doubles_fare(self, mock_surge):
        """2x surge should double the subtotal."""
        # 5 km, ETA = 12 min
        # Subtotal = 50 + 100 + 24 = 174
        # With 2x surge = 348
        fare = calculate_fare(5.0)
        assert fare == 348.0

    @patch("services.pricing.get_surge_multiplier", return_value=1.5)
    def test_surge_1_5x(self, mock_surge):
        """1.5x surge pricing calculation."""
        # 10 km, ETA = 24 min
        # Subtotal = 50 + 200 + 48 = 298
        # With 1.5x surge = 447
        fare = calculate_fare(10.0)
        assert fare == 447.0

    @patch("services.pricing.get_surge_multiplier", return_value=1.0)
    def test_custom_duration(self, mock_surge):
        """Test with explicit duration override."""
        # 5 km, 30 min
        # BASE(50) + DISTANCE(100) + TIME(30*2=60) = 210
        fare = calculate_fare(5.0, duration_min=30)
        assert fare == 210.0

    @patch("services.pricing.get_surge_multiplier", return_value=1.0)
    def test_fare_is_float(self, mock_surge):
        """Fare should always be a float."""
        fare = calculate_fare(3.0)
        assert isinstance(fare, float)

    @patch("services.pricing.get_surge_multiplier", return_value=1.0)
    def test_longer_distance_costs_more(self, mock_surge):
        """A longer trip should always cost more than a shorter one."""
        short_fare = calculate_fare(2.0)
        long_fare = calculate_fare(20.0)
        assert long_fare > short_fare


class TestSurgeMultiplier:
    """Tests for surge pricing multiplier."""

    def test_multiplier_range(self):
        """Surge multiplier should always be >= 1.0."""
        for _ in range(100):
            mult = get_surge_multiplier()
            assert mult >= 1.0

    def test_multiplier_max(self):
        """Surge multiplier should never exceed 2.0."""
        for _ in range(100):
            mult = get_surge_multiplier()
            assert mult <= 2.0


class TestPricingConstants:
    """Verify pricing constants are reasonable for the Ethiopian market."""

    def test_base_fare_positive(self):
        assert BASE_FARE > 0

    def test_per_km_rate_positive(self):
        assert PER_KM_RATE > 0

    def test_per_min_rate_positive(self):
        assert PER_MIN_RATE > 0

    def test_min_fare_positive(self):
        assert MIN_FARE > 0

    def test_min_fare_covers_base(self):
        """Minimum fare should be at least the base fare."""
        assert MIN_FARE >= BASE_FARE

    def test_average_speed_reasonable(self):
        """Average speed should be reasonable for city driving."""
        assert 10 <= AVERAGE_SPEED_KMH <= 60
