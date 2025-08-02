"""Strategy engine for advanced game analysis and decision making."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..tools.search_tool import InternetSearchTool

@dataclass
class StrategyRecommendation:
    """Represents a strategic recommendation."""
    action: str
    confidence: float
    reasoning: str
    alternatives: List[str]

class StrategyEngine:
    """Advanced strategy engine for Werewolf game analysis."""
    
    def __init__(self):
        """Initialize the strategy engine."""
        self.search_tool = InternetSearchTool()
        self.knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict[str, Any]:
        """Build internal knowledge base of game strategies.
        
        Returns:
            Dictionary containing strategic knowledge
        """
        return {
            "wolf_strategies": [
                "Blend in with civilians",
                "Create doubt about other players",
                "Protect teammates subtly",
                "Avoid being too defensive",
                "Guide suspicion toward civilians"
            ],
            "civilian_strategies": [
                "Look for inconsistencies in behavior",
                "Ask probing questions",
                "Build coalitions with other civilians",
                "Track voting patterns",
                "Observe who defends whom"
            ],
            "communication_tactics": [
                "Use confident but not aggressive tone",
                "Share observations without seeming desperate",
                "Ask open-ended questions",
                "Acknowledge valid points from others",
                "Avoid contradicting yourself"
            ]
        }
    
    def analyze_game_state(self, game_context: str, role: str, memory: List[str]) -> Dict[str, Any]:
        """Analyze current game state and provide strategic insights.
        
        Args:
            game_context: Current game context
            role: Player's role (wolf, civilian, god)
            memory: Player's memory of recent events
            
        Returns:
            Dictionary containing strategic analysis
        """
        analysis = {
            "threat_level": self._assess_threat_level(memory, role),
            "player_suspicions": self._analyze_suspicions(memory),
            "recommended_focus": self._get_role_focus(role),
            "communication_style": self._recommend_communication_style(role, memory)
        }
        
        return analysis
    
    def generate_strategy_recommendation(self, 
                                       game_context: str, 
                                       role: str, 
                                       analysis: Dict[str, Any]) -> StrategyRecommendation:
        """Generate specific strategy recommendation.
        
        Args:
            game_context: Current game context
            role: Player's role
            analysis: Game state analysis
            
        Returns:
            Strategic recommendation
        """
        if role == "wolf":
            return self._wolf_strategy(game_context, analysis)
        elif role == "civilian":
            return self._civilian_strategy(game_context, analysis)
        else:
            return self._default_strategy(game_context, analysis)
    
    def research_strategy(self, query: str, role: str) -> str:
        """Research strategy using internet search.
        
        Args:
            query: Research query
            role: Player role for context
            
        Returns:
            Research results formatted for strategy use
        """
        # Enhance query with role context
        enhanced_query = f"werewolf mafia game {role} {query} strategy tactics"
        
        results = self.search_tool.search(enhanced_query)
        
        # Extract key insights
        insights = self._extract_strategic_insights(results, role)
        
        return insights
    
    def _assess_threat_level(self, memory: List[str], role: str) -> str:
        """Assess current threat level based on memory.
        
        Args:
            memory: Recent game events
            role: Player's role
            
        Returns:
            Threat level assessment
        """
        suspicious_words = ["suspicious", "wolf", "lying", "vote", "eliminate"]
        mentions = sum(1 for event in memory for word in suspicious_words if word in event.lower())
        
        if mentions > 3:
            return "high"
        elif mentions > 1:
            return "medium"
        else:
            return "low"
    
    def _analyze_suspicions(self, memory: List[str]) -> Dict[str, int]:
        """Analyze who seems to be under suspicion.
        
        Args:
            memory: Recent game events
            
        Returns:
            Dictionary mapping players to suspicion levels
        """
        suspicions = {}
        for event in memory:
            # Simple pattern matching for player mentions with negative context
            if "suspicious" in event.lower() or "wolf" in event.lower():
                # Extract player mentions (simplified)
                words = event.split()
                for word in words:
                    if word.startswith("Player_"):
                        player = word.strip(".,!?")
                        suspicions[player] = suspicions.get(player, 0) + 1
        
        return suspicions
    
    def _get_role_focus(self, role: str) -> List[str]:
        """Get strategic focus points for a role.
        
        Args:
            role: Player's role
            
        Returns:
            List of focus areas
        """
        if role == "wolf":
            return self.knowledge_base["wolf_strategies"]
        elif role == "civilian":
            return self.knowledge_base["civilian_strategies"]
        else:
            return ["Observe and facilitate", "Maintain game balance"]
    
    def _recommend_communication_style(self, role: str, memory: List[str]) -> str:
        """Recommend communication style based on role and situation.
        
        Args:
            role: Player's role
            memory: Recent events
            
        Returns:
            Communication style recommendation
        """
        threat_level = self._assess_threat_level(memory, role)
        
        if role == "wolf":
            if threat_level == "high":
                return "defensive_subtle"
            else:
                return "helpful_concerned"
        elif role == "civilian":
            if threat_level == "high":
                return "analytical_cautious"
            else:
                return "probing_collaborative"
        else:
            return "neutral_facilitative"
    
    def _wolf_strategy(self, game_context: str, analysis: Dict[str, Any]) -> StrategyRecommendation:
        """Generate wolf-specific strategy.
        
        Args:
            game_context: Current game context
            analysis: Game analysis results
            
        Returns:
            Wolf strategy recommendation
        """
        if analysis["threat_level"] == "high":
            action = "deflect_suspicion"
            reasoning = "High threat level detected. Need to redirect attention."
            alternatives = ["defend_subtly", "create_counter_suspicion"]
            confidence = 75.0
        else:
            action = "build_trust"
            reasoning = "Low threat level. Focus on appearing helpful and trustworthy."
            alternatives = ["gather_information", "guide_discussion"]
            confidence = 80.0
        
        return StrategyRecommendation(action, confidence, reasoning, alternatives)
    
    def _civilian_strategy(self, game_context: str, analysis: Dict[str, Any]) -> StrategyRecommendation:
        """Generate civilian-specific strategy.
        
        Args:
            game_context: Current game context
            analysis: Game analysis results
            
        Returns:
            Civilian strategy recommendation
        """
        if analysis["player_suspicions"]:
            action = "investigate_suspicions"
            reasoning = "Suspicions detected. Focus on gathering more evidence."
            alternatives = ["ask_probing_questions", "observe_reactions"]
            confidence = 70.0
        else:
            action = "gather_information"
            reasoning = "No clear suspicions yet. Focus on information gathering."
            alternatives = ["observe_behavior", "encourage_discussion"]
            confidence = 65.0
        
        return StrategyRecommendation(action, confidence, reasoning, alternatives)
    
    def _default_strategy(self, game_context: str, analysis: Dict[str, Any]) -> StrategyRecommendation:
        """Generate default strategy for other roles.
        
        Args:
            game_context: Current game context
            analysis: Game analysis results
            
        Returns:
            Default strategy recommendation
        """
        return StrategyRecommendation(
            action="observe_and_adapt",
            confidence=60.0,
            reasoning="Maintain neutral position and adapt to situation.",
            alternatives=["facilitate_discussion", "gather_information"]
        )
    
    def _extract_strategic_insights(self, research_results: str, role: str) -> str:
        """Extract strategic insights from research results.
        
        Args:
            research_results: Raw research results
            role: Player role for context filtering
            
        Returns:
            Extracted and formatted insights
        """
        # Simple keyword extraction and formatting
        keywords = {
            "wolf": ["deception", "misdirection", "trust", "suspicion", "deflect"],
            "civilian": ["observation", "questions", "patterns", "logic", "evidence"],
            "general": ["communication", "psychology", "strategy", "tactics"]
        }
        
        relevant_keywords = keywords.get(role, []) + keywords["general"]
        
        insights = f"Strategic Insights for {role}:\n"
        insights += "-" * 30 + "\n"
        
        # Extract sentences containing relevant keywords
        sentences = research_results.split('.')
        relevant_sentences = []
        
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            if any(keyword in sentence.lower() for keyword in relevant_keywords):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            insights += "\n".join(f"• {sentence}" for sentence in relevant_sentences[:5])
        else:
            insights += "• Focus on your role-specific objectives\n"
            insights += "• Adapt communication style to situation\n"
            insights += "• Observe other players carefully"
        
        return insights
