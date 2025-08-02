#!/usr/bin/env python3
"""
Test suite for Werewolf AI Agent Game

Run with: python -m pytest tests/ -v
Or simply: python tests/test_werewolf.py
"""

import sys
import os
from pathlib import Path
import unittest

# Add src directory to Python path
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from core.game_state import GameState
from core.player import Player, Role
from agents.base_agent import BaseAgent
from ai.strategy_engine import StrategyEngine
from tools.search_tool import InternetSearchTool

class TestGameState(unittest.TestCase):
    """Test game state functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState(6)
    
    def test_game_initialization(self):
        """Test game state initialization."""
        self.assertEqual(len(self.game_state.players), 6)
        self.assertEqual(self.game_state.day_count, 1)
        self.assertEqual(self.game_state.current_phase.value, "day")
    
    def test_role_distribution(self):
        """Test role distribution is correct."""
        wolves = [p for p in self.game_state.players.values() if p.is_wolf()]
        civilians = [p for p in self.game_state.players.values() if p.is_civilian()]
        gods = [p for p in self.game_state.players.values() if p.is_god()]
        
        self.assertGreaterEqual(len(wolves), 1)  # At least 1 wolf
        self.assertEqual(len(gods), 1)  # Exactly 1 god
        self.assertGreater(len(civilians), 0)  # At least 1 civilian
    
    def test_player_elimination(self):
        """Test player elimination functionality."""
        initial_alive = len(self.game_state.get_alive_players())
        
        # Kill a player
        player_to_kill = list(self.game_state.players.keys())[0]
        self.game_state.kill_player(player_to_kill)
        
        final_alive = len(self.game_state.get_alive_players())
        self.assertEqual(final_alive, initial_alive - 1)
    
    def test_game_over_conditions(self):
        """Test game over detection."""
        # Kill all wolves
        wolves = self.game_state.get_alive_wolves()
        for wolf in wolves:
            self.game_state.kill_player(wolf.player_id)
        
        is_over, winner = self.game_state.check_game_over()
        self.assertTrue(is_over)
        self.assertEqual(winner, "Civilians")

class TestPlayer(unittest.TestCase):
    """Test player functionality."""
    
    def test_player_creation(self):
        """Test player creation and properties."""
        player = Player(1, "TestPlayer", Role.WOLF)
        
        self.assertEqual(player.player_id, 1)
        self.assertEqual(player.name, "TestPlayer")
        self.assertTrue(player.is_wolf())
        self.assertFalse(player.is_civilian())
        self.assertFalse(player.is_god())
        self.assertTrue(player.is_alive)
    
    def test_player_death(self):
        """Test player death functionality."""
        player = Player(1, "TestPlayer", Role.CIVILIAN)
        self.assertTrue(player.is_alive)
        
        player.kill()
        self.assertFalse(player.is_alive)

class TestBaseAgent(unittest.TestCase):
    """Test base agent functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = BaseAgent(None, 1, "TestAgent")
    
    def test_memory_management(self):
        """Test agent memory functionality."""
        self.agent.add_to_memory("Test message 1")
        self.agent.add_to_memory("Test message 2")
        
        memory = self.agent.get_memory_context()
        self.assertIn("Test message 1", memory)
        self.assertIn("Test message 2", memory)
    
    def test_memory_limit(self):
        """Test memory limit enforcement."""
        # Add more than the memory limit
        for i in range(25):
            self.agent.add_to_memory(f"Message {i}")
        
        # Should only keep the last 20
        self.assertEqual(len(self.agent.memory), 20)
        self.assertIn("Message 24", str(self.agent.memory))
        self.assertNotIn("Message 0", str(self.agent.memory))

class TestStrategyEngine(unittest.TestCase):
    """Test strategy engine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = StrategyEngine()
    
    def test_threat_assessment(self):
        """Test threat level assessment."""
        memory_high_threat = [
            "Player_1 is very suspicious of me",
            "Everyone thinks I'm a wolf",
            "They want to vote me out"
        ]
        
        memory_low_threat = [
            "Good morning everyone",
            "Nice day today"
        ]
        
        high_threat = self.engine._assess_threat_level(memory_high_threat, "wolf")
        low_threat = self.engine._assess_threat_level(memory_low_threat, "wolf")
        
        self.assertEqual(high_threat, "high")
        self.assertEqual(low_threat, "low")
    
    def test_strategy_recommendation(self):
        """Test strategy recommendation generation."""
        analysis = {
            "threat_level": "medium",
            "player_suspicions": {"Player_2": 2},
            "recommended_focus": ["blend_in", "deflect"],
            "communication_style": "defensive_subtle"
        }
        
        recommendation = self.engine.generate_strategy_recommendation(
            "Day 2 discussion", "wolf", analysis
        )
        
        self.assertIsNotNone(recommendation.action)
        self.assertGreater(recommendation.confidence, 0)
        self.assertLess(recommendation.confidence, 100)

class TestSearchTool(unittest.TestCase):
    """Test search tool functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.search_tool = InternetSearchTool()
    
    def test_search_tool_creation(self):
        """Test search tool can be created."""
        self.assertIsNotNone(self.search_tool)
        self.assertIsNotNone(self.search_tool.session)

def run_tests():
    """Run all tests."""
    print("🧪 Running Werewolf Game Tests")
    print("=" * 40)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestGameState))
    test_suite.addTest(unittest.makeSuite(TestPlayer))
    test_suite.addTest(unittest.makeSuite(TestBaseAgent))
    test_suite.addTest(unittest.makeSuite(TestStrategyEngine))
    test_suite.addTest(unittest.makeSuite(TestSearchTool))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")
        
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
