"""Test file to verify PR-Agent integration.

This file is created to trigger PR-Agent review on a test PR.
It can be deleted after verification.
"""

import pytest


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def subtract_numbers(a: int, b: int) -> int:
    """Subtract b from a.

    Args:
        a: First number
        b: Second number

    Returns:
        Difference of a and b
    """
    return a - b


class TestMathOperations:
    """Test cases for math operations."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add_numbers(2, 3) == 5

    def test_add_negative_numbers(self):
        """Test adding two negative numbers."""
        assert add_numbers(-2, -3) == -5

    def test_add_mixed_numbers(self):
        """Test adding positive and negative numbers."""
        assert add_numbers(-2, 3) == 1

    def test_subtract_positive_numbers(self):
        """Test subtracting two positive numbers."""
        assert subtract_numbers(5, 3) == 2

    def test_subtract_negative_numbers(self):
        """Test subtracting two negative numbers."""
        assert subtract_numbers(-5, -3) == -2
