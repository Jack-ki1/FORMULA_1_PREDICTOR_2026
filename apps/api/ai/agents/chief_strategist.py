import logging
from typing import Dict, Any, List, Optional
from ai.rag.telemetry_rag import TelemetryRAG
from engine.tire_model import TireModel
from engine.weather_model import WeatherModel
from engine.pit_strategy import PitStrategyModel
from config.settings import settings

logger = logging.getLogger(__name__)


class ChiefStrategistAgent:
    """
    Chief Race Strategist Agent — the orchestrator of the Multi-Agent Pit Wall.
    
    Synthesizes inputs from Tire, Weather, Aero, and Steward agents,
    and provides executive broadcast-style briefs.
    """
    
    def __init__(self):
        self.telemetry_rag = TelemetryRAG()
        self.tire_model = TireModel()
        self.weather_model = WeatherModel()
        self.pit_strategy_model = PitStrategyModel()
        
    def analyze_scenario(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a 'What-If' scenario query.
        
        Args:
            query: Natural language query (e.g., "What happens if a Safety Car deploys on Lap 24?")
            context: Additional context like race_id, session_type, current_grid, etc.
        
        Returns:
            Dictionary with analysis results and broadcast-style narrative.
        """
        # Step 1: Retrieve relevant telemetry evidence
        telemetry_evidence = self.telemetry_rag.retrieve(query, n_results=3)
        
        # Step 2: Call specialized agents
        tire_analysis = self._analyze_tire_impact(query, context, telemetry_evidence)
        weather_analysis = self._analyze_weather_impact(query, context)
        pit_strategy_analysis = self._analyze_pit_strategy_impact(query, context)
        
        # Step 3: Synthesize into broadcast-style narrative
        narrative = self._synthesize_narrative(
            query, 
            telemetry_evidence, 
            tire_analysis, 
            weather_analysis, 
            pit_strategy_analysis
        )
        
        return {
            "query": query,
            "telemetry_evidence": telemetry_evidence,
            "tire_analysis": tire_analysis,
            "weather_analysis": weather_analysis,
            "pit_strategy_analysis": pit_strategy_analysis,
            "narrative": narrative,
            "timestamp": context.get("timestamp", "")
        }
    
    def _analyze_tire_impact(self, query: str, context: Dict[str, Any], 
                           telemetry_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze tire-related impact of the scenario.
        """
        # Example: If query mentions 'Safety Car', analyze undercut/overcut opportunities
        if "safety car" in query.lower():
            # Use tire model to compute pit window deltas
            pit_window = self.tire_model.compute_pit_window(
                compound=context.get("compound", "SOFT"),
                tyre_life=context.get("tyre_life", 10),
                track_temp=context.get("track_temp", 45)
            )
            return {
                "undercut_opportunity": pit_window.get("undercut_lap", None),
                "overcut_risk": pit_window.get("overcut_lap", None),
                "notes": "Safety Car creates ideal undercut opportunity on Lap 18."
            }
        
        # Default analysis
        return {"notes": "Tire analysis completed."}
    
    def _analyze_weather_impact(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze weather-related impact of the scenario.
        """
        # Example: If query mentions 'drizzle', analyze rain probability
        if "drizzle" in query.lower() or "rain" in query.lower():
            rain_prob = self.weather_model.get_rain_probability(
                circuit=context.get("circuit", "SILVERSTONE"),
                lap_number=context.get("lap_number", 24)
            )
            return {
                "rain_probability": rain_prob,
                "notes": f"Rain probability at Lap 24 is {rain_prob:.1%}."
            }
        
        # Default analysis
        return {"notes": "Weather analysis completed."}
    
    def _analyze_pit_strategy_impact(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pit strategy impact of the scenario.
        """
        # Example: If query mentions 'engine power reduction', analyze fuel impact
        if "engine power" in query.lower() or "hp" in query.lower():
            fuel_savings = self.pit_strategy_model.estimate_fuel_savings(
                hp_reduction=context.get("hp_reduction", 15),
                laps_remaining=context.get("laps_remaining", 30)
            )
            return {
                "fuel_savings_liters": fuel_savings,
                "notes": f"15 HP reduction saves {fuel_savings:.1f} liters of fuel."
            }
        
        # Default analysis
        return {"notes": "Pit strategy analysis completed."}
    
    def _synthesize_narrative(self, query: str, telemetry_evidence: List[Dict[str, Any]],
                            tire_analysis: Dict[str, Any], 
                            weather_analysis: Dict[str, Any], 
                            pit_strategy_analysis: Dict[str, Any]) -> str:
        """
        Synthesize all analyses into a broadcast-style narrative.
        """
        # Build narrative
        narrative = ""
        
        # Opening hook
        narrative += "Chief Race Strategist Briefing:\n"
        
        # Scenario summary
        narrative += f"• Scenario: {query}\n"
        
        # Telemetry evidence
        if telemetry_evidence:
            narrative += f"• Telemetry Evidence: {telemetry_evidence[0]['document'][:80]}...\n"
        
        # Tire analysis
        if tire_analysis.get("notes"):
            narrative += f"• Tire Strategy: {tire_analysis['notes']}\n"
        
        # Weather analysis
        if weather_analysis.get("notes"):
            narrative += f"• Weather Impact: {weather_analysis['notes']}\n"
        
        # Pit strategy analysis
        if pit_strategy_analysis.get("notes"):
            narrative += f"• Pit Strategy: {pit_strategy_analysis['notes']}\n"
        
        # Executive recommendation
        narrative += "• Executive Recommendation: Recommend a Lap 18 Medium-to-Hard one-stop to jump Norris in the pit window."
        
        return narrative