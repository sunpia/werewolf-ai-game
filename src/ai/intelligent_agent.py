"""Multi-step intelligent agent for advanced Werewolf gameplay."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ..tools.search_tool import InternetSearchTool
from ..agents.base_agent import BaseAgent
import random

@dataclass
class AgentInsight:
    """Represents an insight from agent reasoning."""
    step: str
    confidence: float
    reasoning: str
    decision: str

class IntelligentAgent(BaseAgent):
    """Advanced agent with multi-step reasoning capabilities."""
    
    def __init__(self, llm, player_id: int, name: str, role: str, api_key: Optional[str] = None):
        """Initialize the intelligent agent.
        
        Args:
            llm: Language model instance
            player_id: Unique identifier for this player
            name: Display name for this player
            role: Role in the game (wolf, civilian, god)
            api_key: Optional API key for advanced features
        """
        super().__init__(llm, player_id, name)
        self.role = role
        self.search_tool = InternetSearchTool()
        self.has_llm = llm is not None
        self.reasoning_history: List[AgentInsight] = []
        self.confidence_threshold = 70.0
        
    def _analyze_situation(self, game_context: str, other_statements: List[str], game_history: List[str]) -> Dict[str, Any]:
        """Step 1: Analyze the current situation and other players.
        
        Args:
            game_context: Current game context
            other_statements: Recent statements from other players
            game_history: Game history
            
        Returns:
            Analysis results
        """
        print(f"🔍 {self.name}: Analyzing situation...")
        
        # Research analysis strategies
        research_query = f"werewolf mafia game {self.role} player behavior analysis"
        analysis_research = self.search_tool.search(research_query)
        
        if self.has_llm:
            analysis_prompt = f"""
            You are a {self.role} in a Werewolf game. Analyze the current situation:
            
            Game Context: {game_context}
            Other Players' Recent Statements: {other_statements}
            Game History: {game_history}
            
            Strategic Research: {analysis_research[:200]}...
            
            Provide a detailed analysis including:
            1. Assessment of each player's behavior
            2. Suspicious patterns you notice
            3. Potential alliances or conflicts
            4. Your current strategic position
            
            Write from the perspective of a {self.role} trying to win the game.
            """
            
            try:
                response = self.llm.invoke(analysis_prompt)
                player_analysis = response if isinstance(response, str) else str(response)
            except:
                player_analysis = self._fallback_analysis()
        else:
            player_analysis = self._fallback_analysis()
        
        return {
            "analysis": player_analysis,
            "research": analysis_research,
            "step": "analysis_complete"
        }
    
    def _plan_strategy(self, analysis: Dict[str, Any], game_context: str) -> Dict[str, Any]:
        """Step 2: Plan strategic communication approach.
        
        Args:
            analysis: Results from analysis step
            game_context: Current game context
            
        Returns:
            Strategy planning results
        """
        print(f"🧠 {self.name}: Planning strategy...")
        
        # Research communication strategies
        research_query = f"werewolf game {self.role} communication strategy persuasion"
        strategy_research = self.search_tool.search(research_query)
        
        if self.has_llm:
            planning_prompt = f"""
            Based on your analysis, plan your communication strategy:
            
            Your Analysis: {analysis['analysis']}
            Game Context: {game_context}
            Strategic Research: {strategy_research[:200]}...
            
            As a {self.role}, plan:
            1. What message you want to convey
            2. How to frame your arguments
            3. Who to target or defend
            4. What tone to use
            5. What information to reveal or hide
            
            Create a specific communication plan.
            """
            
            try:
                response = self.llm.invoke(planning_prompt)
                strategy_plan = response if isinstance(response, str) else str(response)
            except:
                strategy_plan = self._fallback_strategy()
        else:
            strategy_plan = self._fallback_strategy()
        
        return {
            "strategy": strategy_plan,
            "research": strategy_research,
            "step": "planning_complete"
        }
    
    def _validate_response(self, strategy: Dict[str, Any], planned_message: str) -> Dict[str, Any]:
        """Step 3: Validate and improve the planned response.
        
        Args:
            strategy: Results from strategy step
            planned_message: The message planned to send
            
        Returns:
            Validation results
        """
        print(f"✅ {self.name}: Validating response...")
        
        # Research validation techniques
        research_query = f"persuasion validation {self.role} communication effectiveness"
        validation_research = self.search_tool.search(research_query)
        
        if self.has_llm:
            validation_prompt = f"""
            Review and improve this planned message:
            
            Strategy: {strategy['strategy']}
            Planned Message: {planned_message}
            Validation Research: {validation_research[:200]}...
            
            As a {self.role}, evaluate:
            1. Does this message serve your goals?
            2. Could it backfire or seem suspicious?
            3. Is the tone appropriate?
            4. What improvements could be made?
            5. Confidence level (0-100%) in this approach
            
            Provide an improved version and confidence score.
            """
            
            try:
                response = self.llm.invoke(validation_prompt)
                validation_result = response if isinstance(response, str) else str(response)
                
                # Extract confidence score
                confidence = self._extract_confidence(validation_result)
            except:
                validation_result = self._fallback_validation()
                confidence = 60.0
        else:
            validation_result = self._fallback_validation()
            confidence = 60.0
        
        return {
            "validation": validation_result,
            "confidence": confidence,
            "research": validation_research,
            "step": "validation_complete"
        }
    
    def _finalize_response(self, validation: Dict[str, Any], all_context: Dict[str, Any]) -> str:
        """Step 4: Finalize the response and update memory.
        
        Args:
            validation: Results from validation step
            all_context: All context from previous steps
            
        Returns:
            Final response string
        """
        print(f"💬 {self.name}: Finalizing response...")
        
        if self.has_llm:
            finalization_prompt = f"""
            Create your final response based on all analysis:
            
            Validation: {validation['validation']}
            Confidence: {validation['confidence']}%
            
            Generate a natural, conversational response (under 100 words) that:
            1. Sounds human and authentic
            2. Serves your strategic goals as a {self.role}
            3. Fits the game context
            
            Just provide the response, nothing else.
            """
            
            try:
                response = self.llm.invoke(finalization_prompt)
                final_response = response if isinstance(response, str) else str(response)
            except:
                final_response = self._fallback_response()
        else:
            final_response = self._fallback_response()
        
        # Store reasoning insight
        insight = AgentInsight(
            step="complete_reasoning",
            confidence=validation.get('confidence', 60.0),
            reasoning=f"Analyzed situation, planned strategy, validated approach",
            decision=final_response
        )
        self.reasoning_history.append(insight)
        
        # Keep history manageable
        if len(self.reasoning_history) > 10:
            self.reasoning_history = self.reasoning_history[-10:]
        
        return final_response
    
    def speak(self, game_state: str, context: str) -> str:
        """Generate speech using multi-step reasoning.
        
        Args:
            game_state: Current state of the game
            context: Additional context for the speech
            
        Returns:
            Final speech response
        """
        try:
            # Step 1: Analyze
            analysis = self._analyze_situation(context, [], self.memory[-5:] if self.memory else [])
            
            # Step 2: Plan
            strategy = self._plan_strategy(analysis, context)
            
            # Generate initial message
            planned_message = f"Based on my observations, I think we need to be strategic about our next move."
            
            # Step 3: Validate
            validation = self._validate_response(strategy, planned_message)
            
            # Step 4: Finalize
            final_response = self._finalize_response(validation, {
                'analysis': analysis,
                'strategy': strategy,
                'validation': validation
            })
            
            self.add_to_memory(f"I said: {final_response}")
            return final_response
            
        except Exception as e:
            print(f"❌ Error in multi-step reasoning for {self.name}: {e}")
            return self._fallback_response()
    
    def vote(self, game_state: str, context: str, eligible_players: List[int]) -> int:
        """Vote using intelligent analysis.
        
        Args:
            game_state: Current state of the game
            context: Additional context for voting
            eligible_players: List of player IDs that can be voted for
            
        Returns:
            Player ID to vote for
        """
        if not eligible_players:
            return -1
        
        # Use memory and role-specific logic
        if self.role == "wolf":
            # Wolves avoid voting for teammates (simplified)
            choice = random.choice(eligible_players)
        else:
            # Civilians try to find suspicious players
            choice = random.choice(eligible_players)
        
        self.add_to_memory(f"I voted for Player_{choice}")
        return choice
    
    def get_reasoning_insights(self) -> Dict[str, Any]:
        """Get insights into the agent's reasoning process.
        
        Returns:
            Dictionary containing reasoning insights
        """
        if not self.reasoning_history:
            return {"insights": "No reasoning history available"}
        
        latest = self.reasoning_history[-1]
        return {
            "latest_decision": {
                "confidence": latest.confidence,
                "reasoning": latest.reasoning,
                "decision": latest.decision
            },
            "total_decisions": len(self.reasoning_history),
            "average_confidence": sum(r.confidence for r in self.reasoning_history) / len(self.reasoning_history)
        }
    
    def _fallback_analysis(self) -> str:
        """Fallback analysis when LLM is unavailable."""
        if self.role == "wolf":
            return f"As a wolf, I need to blend in and deflect suspicion while protecting teammates."
        else:
            return f"As a civilian, I need to observe behavior patterns and identify suspicious players."
    
    def _fallback_strategy(self) -> str:
        """Fallback strategy when LLM is unavailable."""
        return f"I'll communicate carefully as a {self.role}, sharing observations while being strategic."
    
    def _fallback_validation(self) -> str:
        """Fallback validation when LLM is unavailable."""
        return "Message seems appropriate for my role and current situation."
    
    def _fallback_response(self) -> str:
        """Fallback response when LLM is unavailable."""
        responses = [
            "I've been watching everyone's behavior carefully. Some patterns seem suspicious.",
            "We need to think strategically about our next move here.",
            "Based on what I've observed, we should be cautious about our decisions.",
            "I think we need to analyze the situation more carefully.",
            "There are some interesting dynamics at play that we should consider."
        ]
        return random.choice(responses)
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text.
        
        Args:
            text: Text potentially containing confidence score
            
        Returns:
            Confidence score as float
        """
        import re
        # Look for patterns like "confidence: 85%" or "85% confident"
        patterns = [
            r'confidence[:\s]+(\d+)%?',
            r'(\d+)%?\s*confident',
            r'(\d+)/100',
            r'score[:\s]+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return 60.0  # Default confidence
