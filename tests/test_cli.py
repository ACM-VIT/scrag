"""
Tests for the Scrag CLI module.

This module contains smoke tests and basic functionality tests for the CLI.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch

# Add src to path so we can import scrag
sys.path.insert(0, 'src')
from scrag.cli import main


class TestCLI:
    """Test cases for the CLI functionality."""
    
    def test_main_returns_zero_exit_code(self):
        """Test that main() returns 0 for successful execution."""
        exit_code = main([])
        assert exit_code == 0
    
    def test_main_with_arguments(self):
        """Test that main() handles arguments correctly."""
        test_args = ["--help", "test"]
        exit_code = main(test_args)
        assert exit_code == 0
    
    def test_main_prints_greeting(self):
        """Test that main() prints the expected greeting."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main([])
            output = mock_stdout.getvalue()
            
            assert "Hello from Scrag!" in output
            assert "Adaptive web scraper" in output
            assert "Version: 0.1.0" in output
    
    def test_main_shows_arguments_when_provided(self):
        """Test that main() shows provided arguments."""
        test_args = ["test", "argument"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main(test_args)
            output = mock_stdout.getvalue()
            
            assert "Arguments received:" in output
            assert "test" in output
            assert "argument" in output
    
    def test_main_shows_no_arguments_message_when_empty(self):
        """Test that main() shows appropriate message when no arguments provided."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main([])
            output = mock_stdout.getvalue()
            
            assert "No arguments provided" in output
            assert "--help" in output


def test_cli_smoke_test():
    """Smoke test to ensure CLI can be imported and executed without errors."""
    # This is a basic smoke test that just ensures the CLI can run
    try:
        exit_code = main(["--version"])
        assert isinstance(exit_code, int)
        assert exit_code == 0
    except Exception as e:
        pytest.fail(f"CLI smoke test failed with exception: {e}")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__])