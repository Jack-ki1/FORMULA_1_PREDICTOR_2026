"""
Advanced Pit Strategy & Tire Degradation Simulation.

Extends the existing TireStrategyModel with:
  1. Per-lap tire compound degradation curves (Soft/Medium/Hard)
  2. Pit stop delta calculation and window optimization
  3. Undercut/overcut success probability estimation
  4. Multi-stop race strategy evaluation
  5. Safety car pit window analysis
  6. Telemetry-derived long-run pace deltas
  7. Driver-specific tire management profiles
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

# Pit stop time loss by circuit (seconds) — varies by pit lane length
PIT_LOSS_BY_CIRCUIT: Dict[str, float] = {
    "australia": 22.0,
    "china": 21.5,
    "japan": 21.0,
    "bahrain": 21.5,
    "saudi_arabia": 23.0,
    "miami": 23.5,
    "canada": 20.5,
    "monaco": 25.0,   # Tight pit lane
    "spain": 21.5,
    "austria": 19.5,
    "britain": 22.0,
    "hungary": 21.0,
    "belgium": 22.5,
    "netherlands": 21.0,
    "italy": 23.0,
    "madrid": 22.0,
    "azerbaijan": 21.0,
    "singapore": 25.5,  # Long pit lane
    "usa": 22.0,
    "mexico": 22.5,
    "brazil": 21.5,
    "las_vegas": 21.0,
    "qatar": 21.5,
    "uae": 22.0,
}

# Typical pit loss for unknown circuits
DEFAULT_PIT_LOSS = 22.0

# Safety car pit stop time loss (reduced due to pit lane speed limit)
SC_PIT_LOSS_FACTOR = 0.55  # SC pit stop costs ~55% of normal

# Undercut/overcut time advantage
UNDERCUT_WINDOW_LAPS = 3   # Number of laps undercut typically takes effect
OVERCUT_WINDOW_LAPS = 3    # Number of laps overcut typically takes effect


class TireCompound(Enum):
    """F1 tire compounds with performance characteristics."""
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    INTERMEDIATE = "intermediate"
    WET = "wet"

    @property
    def degradation_rate(self) -> float:
        return {
            TireCompound.SOFT: 0.085,
            TireCompound.MEDIUM: 0.055,
            TireCompound.HARD: 0.035,
            TireCompound.INTERMEDIATE: 0.10,
            TireCompound.WET: 0.12,
        }[self]

    @property
    def initial_grip(self) -> float:
        return {
            TireCompound.SOFT: 1.0,
            TireCompound.MEDIUM: 0.97,
            TireCompound.HARD: 0.94,
            TireCompound.INTERMEDIATE: 0.90,
            TireCompound.WET: 0.85,
        }[self]

    @property
    def optimal_laps(self) -> int:
        return {
            TireCompound.SOFT: 18,
            TireCompound.MEDIUM: 28,
            TireCompound.HARD: 38,
            TireCompound.INTERMEDIATE: 20,
            TireCompound.WET: 15,
        }[self]

    @property
    def max_laps(self) -> int:
        return {
            TireCompound.SOFT: 30,
            TireCompound.MEDIUM: 45,
            TireCompound.HARD: 65,
            TireCompound.INTERMEDIATE: 40,
            TireCompound.WET: 30,
        }[self]


@dataclass
class StintResult:
    """Results of a single tire stint simulation."""
    compound: TireCompound
    start_lap: int
    end_lap: int
    stint_length: int
    avg_lap_time_delta: float       # Average time delta vs optimal (seconds)
    peak_degradation: float          # Maximum performance loss
    tire_wear_factor: float          # End-of-stint wear (0-1)
    under_optimum_window: bool       # True if within optimal window
    exceeded_max_laps: bool          # True if stint too long
    lap_times: List[float] = field(default_factory=list)


@dataclass
class StrategyEvaluation:
    """Complete evaluation of a race strategy."""
    strategy_name: str
    total_pit_stops: int
    total_pit_time_loss: float        # Seconds
    total_tire_time_loss: float       # Seconds lost to degradation
    total_time_loss: float            # Total time lost
    avg_lap_time_delta: float          # Average per-lap delta
    stints: List[StintResult] = field(default_factory=list)
    risk_level: str = "medium"         # "low", "medium", "high"
    undercut_opportunity: bool = False
    overcut_opportunity: bool = False


@dataclass
class UndercutAnalysis:
    """Analysis of undercut/overcut potential."""
    possible: bool
    time_advantage: float             # Seconds gained
    optimal_pit_lap: int              # Best lap to pit
    success_probability: float        # 0-1
    risk_factor: str                  # "low", "medium", "high"


@dataclass
class PitStrategyResult:
    """Complete pit strategy analysis for a race."""
    circuit_id: str
    race_laps: int
    optimal_strategy: StrategyEvaluation
    alternative_strategies: List[StrategyEvaluation]
    undercut_analysis: UndercutAnalysis
    overcut_analysis: UndercutAnalysis
    sc_window_analysis: Dict[str, Any]
    driver_recommendations: Dict[str, str]
    telemetry_deltas: Dict[str, Any]





# ── Tire Degradation Model ───────────────────────────────────────────────────

class TireDegradationModel:
    """
    Advanced tire degradation modeling with per-lap drop-off curves.

    Models the exponential degradation pattern:
    - Initial phase (laps 1-3): Peak grip
    - Optimal phase (laps 4~optimal_laps): Gradual deg
    - Degradation phase: Exponential drop-off
    - Cliff phase: Sudden performance loss
    """

    def __init__(self, circuit_id: str, race_laps: int):
        self.circuit_id = circuit_id
        self.race_laps = race_laps
        self.circuit_factor = self._get_circuit_factor()

    def _get_circuit_factor(self) -> float:
        """Get tire degradation multiplier for this circuit."""
        factors = {
            "monaco": 1.35, "singapore": 1.30, "hungary": 1.25,
            "bahrain": 1.20, "spain": 1.15, "brazil": 1.15,
            "japan": 1.10, "canada": 1.10, "uae": 1.20,
            "saudi_arabia": 1.25, "miami": 1.15, "netherlands": 1.10,
            "belgium": 0.90, "italy": 0.85, "austria": 0.95,
            "britain": 1.0, "usa": 0.95, "azerbaijan": 0.88,
            "china": 1.05, "australia": 1.0, "mexico": 0.90,
            "las_vegas": 0.95, "qatar": 1.10, "madrid": 1.05,
        }
        return factors.get(self.circuit_id, 1.0)

    def lap_time_delta(
        self,
        compound: TireCompound,
        lap_in_stint: int,
        stint_length: int,
        driver_tire_mgmt: float = 0.7,  # 0-1 tire management skill
        temperature: float = 25.0,
    ) -> float:
        """
        Calculate lap time delta due to tire degradation.

        Args:
            compound: Tire compound
            lap_in_stint: Current lap number within stint (1-based)
            stint_length: Total planned stint length
            driver_tire_mgmt: Driver tire management skill (0-1)
            temperature: Track temperature (Celsius)

        Returns:
            Time delta in seconds compared to optimal tire performance
        """
        deg_rate = compound.degradation_rate
        optimal = compound.optimal_laps
        max_laps = compound.max_laps

        # Apply circuit factor
        adjusted_deg = deg_rate * self.circuit_factor

        # Temperature effect (+2% per °C above 25°C)
        temp_factor = 1.0 + max(0, (temperature - 25) / 50)

        # Driver tire management reduces degradation
        mgmt_factor = 1.0 - driver_tire_mgmt * 0.3

        # Phase 1: Initial grip (laps 1-3)
        if lap_in_stint <= 3:
            base_delta = -0.05 * (1 - driver_tire_mgmt)  # Slight improvement
        # Phase 2: Optimal window
        elif lap_in_stint <= optimal:
            base_delta = adjusted_deg * mgmt_factor * (lap_in_stint / optimal) * 0.5
        # Phase 3: Degradation phase
        elif lap_in_stint <= max_laps:
            base_delta = adjusted_deg * mgmt_factor * (
                0.5 + 1.5 * (lap_in_stint - optimal) / (max_laps - optimal)
            )
        # Phase 4: Cliff (beyond max laps)
        else:
            base_delta = adjusted_deg * mgmt_factor * (2.0 + (lap_in_stint - max_laps) * 0.5)

        # Apply temperature and circuit factors
        delta = base_delta * temp_factor * self.circuit_factor

        # Add compound-specific characteristics
        if compound == TireCompound.SOFT:
            # Softs have higher initial performance but sharper drop-off
            delta *= (1.0 + 0.2 * max(0, lap_in_stint - optimal) / max_laps)
        elif compound == TireCompound.HARD:
            # Hards have more consistent degradation
            delta *= 0.85

        return round(delta, 3)

    def simulate_stint(
        self,
        compound: TireCompound,
        start_lap: int,
        end_lap: int,
        driver_tire_mgmt: float = 0.7,
        temperature: float = 25.0,
    ) -> StintResult:
        """
        Simulate a full tire stint.

        Args:
            compound: Tire compound
            start_lap: First lap of stint
            end_lap: Last lap of stint
            driver_tire_mgmt: Driver tire management
            temperature: Track temperature

        Returns:
            StintResult with per-lap analysis
        """
        stint_length = end_lap - start_lap + 1
        lap_times = []

        for lap in range(start_lap, end_lap + 1):
            lap_in_stint = lap - start_lap + 1
            delta = self.lap_time_delta(
                compound, lap_in_stint, stint_length,
                driver_tire_mgmt, temperature,
            )
            lap_times.append(delta)

        avg_delta = sum(lap_times) / len(lap_times) if lap_times else 0.0
        peak_deg = max(lap_times) if lap_times else 0.0
        wear_factor = min(1.0, stint_length / compound.max_laps)

        return StintResult(
            compound=compound,
            start_lap=start_lap,
            end_lap=end_lap,
            stint_length=stint_length,
            avg_lap_time_delta=round(avg_delta, 3),
            peak_degradation=round(peak_deg, 3),
            tire_wear_factor=round(wear_factor, 3),
            under_optimum_window=stint_length <= compound.optimal_laps,
            exceeded_max_laps=stint_length > compound.max_laps,
            lap_times=lap_times,
        )


# ── Pit Stop Strategy Simulator ──────────────────────────────────────────────

class PitStrategySimulator:
    """
    Multi-stop pit strategy simulator.

    Evaluates 1-stop, 2-stop, and 3-stop strategies with compound
    optimization. Calculates undercut/overcut windows and SC opportunities.
    """

    def __init__(self, circuit_id: str, race_laps: int):
        self.circuit_id = circuit_id
        self.race_laps = race_laps
        self.pit_loss = PIT_LOSS_BY_CIRCUIT.get(circuit_id, DEFAULT_PIT_LOSS)
        self.tire_model = TireDegradationModel(circuit_id, race_laps)

    def evaluate_strategy(
        self,
        stints: List[Tuple[TireCompound, int, int]],
        driver_tire_mgmt: float = 0.7,
        temperature: float = 25.0,
    ) -> StrategyEvaluation:
        """
        Evaluate a complete race strategy.

        Args:
            stints: List of (compound, start_lap, end_lap)
            driver_tire_mgmt: Driver tire management
            temperature: Track temperature

        Returns:
            StrategyEvaluation with time losses
        """
        total_pit_stops = len(stints) - 1
        total_pit_loss = total_pit_stops * self.pit_loss

        stint_results = []
        total_tire_loss = 0.0
        total_laps = 0

        for compound, start_lap, end_lap in stints:
            stint = self.tire_model.simulate_stint(
                compound, start_lap, end_lap,
                driver_tire_mgmt, temperature,
            )
            stint_results.append(stint)
            total_tire_loss += stint.avg_lap_time_delta * stint.stint_length
            total_laps += stint.stint_length

        avg_lap_delta = total_tire_loss / max(total_laps, 1)

        # Risk assessment
        risk_level = "low"
        if total_pit_stops >= 3:
            risk_level = "high"
        elif total_pit_stops >= 2:
            risk_level = "medium"
        elif any(s.exceeded_max_laps for s in stint_results):
            risk_level = "medium"

        # Strategy name
        compounds_used = [s.compound.value[0].upper() for s in stint_results]
        strategy_name = "-".join(compounds_used)

        return StrategyEvaluation(
            strategy_name=strategy_name,
            total_pit_stops=total_pit_stops,
            total_pit_time_loss=round(total_pit_loss, 2),
            total_tire_time_loss=round(total_tire_loss, 2),
            total_time_loss=round(total_pit_loss + total_tire_loss, 2),
            avg_lap_time_delta=round(avg_lap_delta, 3),
            stints=stint_results,
            risk_level=risk_level,
        )

    def generate_strategies(
        self,
        available_compounds: List[TireCompound] = None,
        driver_tire_mgmt: float = 0.7,
        temperature: float = 25.0,
    ) -> List[StrategyEvaluation]:
        """
        Generate and evaluate all viable strategies.

        Args:
            available_compounds: Available tire compounds
            driver_tire_mgmt: Driver tire management
            temperature: Track temperature

        Returns:
            List of evaluated strategies sorted by total time loss
        """
        if available_compounds is None:
            available_compounds = [
                TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD,
            ]

        has_soft = TireCompound.SOFT in available_compounds
        has_medium = TireCompound.MEDIUM in available_compounds
        has_hard = TireCompound.HARD in available_compounds

        strategies = []
        L = self.race_laps

        # 1-stop strategies
        if has_medium and has_hard:
            strategies.append([
                (TireCompound.MEDIUM, 1, L // 2),
                (TireCompound.HARD, L // 2 + 1, L),
            ])
            strategies.append([
                (TireCompound.HARD, 1, L // 2 + 5),
                (TireCompound.MEDIUM, L // 2 + 6, L),
            ])

        # 2-stop strategies
        if has_soft and has_medium and has_hard:
            # Soft-Mid-Hard
            s1_end = int(L * 0.25)
            s2_end = int(L * 0.60)
            strategies.append([
                (TireCompound.SOFT, 1, s1_end),
                (TireCompound.MEDIUM, s1_end + 1, s2_end),
                (TireCompound.HARD, s2_end + 1, L),
            ])
            # Medium-Hard-Medium
            m1_end = int(L * 0.30)
            h_end = int(L * 0.65)
            strategies.append([
                (TireCompound.MEDIUM, 1, m1_end),
                (TireCompound.HARD, m1_end + 1, h_end),
                (TireCompound.MEDIUM, h_end + 1, L),
            ])

        # 3-stop aggressive
        if has_soft and has_medium:
            s1_end = int(L * 0.15)
            s2_end = int(L * 0.35)
            m_end = int(L * 0.60)
            strategies.append([
                (TireCompound.SOFT, 1, s1_end),
                (TireCompound.SOFT, s1_end + 1, s2_end),
                (TireCompound.MEDIUM, s2_end + 1, m_end),
                (TireCompound.HARD, m_end + 1, L),
            ])

        # Full hard (ultra-conservative)
        if has_hard:
            strategies.append([
                (TireCompound.HARD, 1, L),
            ])

        # Evaluate all
        evaluations = []
        for s in strategies:
            try:
                ev = self.evaluate_strategy(s, driver_tire_mgmt, temperature)
                evaluations.append(ev)
            except Exception as e:
                logger.warning(f"Strategy evaluation failed: {e}")

        return sorted(evaluations, key=lambda x: x.total_time_loss)

    def find_optimal_strategy(
        self,
        available_compounds: List[TireCompound] = None,
        driver_tire_mgmt: float = 0.7,
        temperature: float = 25.0,
    ) -> StrategyEvaluation:
        """Find the strategy with minimum total time loss."""
        strategies = self.generate_strategies(
            available_compounds, driver_tire_mgmt, temperature
        )
        return strategies[0] if strategies else self._default_strategy()

    def _default_strategy(self) -> StrategyEvaluation:
        """Return a safe default strategy."""
        return StrategyEvaluation(
            strategy_name="MED-HARD",
            total_pit_stops=1,
            total_pit_time_loss=self.pit_loss,
            total_tire_time_loss=0.0,
            total_time_loss=self.pit_loss,
            avg_lap_time_delta=0.0,
            risk_level="low",
        )

    def analyze_undercut(
        self,
        pitting_driver_lap: int,
        target_driver_lap: Optional[int] = None,
        lap_time_diff: float = 0.3,  # Time advantage per lap on fresh tires
    ) -> UndercutAnalysis:
        """
        Analyze undercut potential.

        Undercut: Pitting earlier than a competitor to gain track position
        by using the lap time advantage of fresh tires.

        Args:
            pitting_driver_lap: Lap number for the undercutting driver
            target_driver_lap: Lap number for the target (None = estimated optimal)
            lap_time_diff: Time advantage per lap on fresh tires

        Returns:
            UndercutAnalysis with success probability
        """
        if target_driver_lap is None:
            target_driver_lap = pitting_driver_lap + 2

        window_laps = target_driver_lap - pitting_driver_lap
        if window_laps <= 0:
            return UndercutAnalysis(
                possible=False,
                time_advantage=0.0,
                optimal_pit_lap=pitting_driver_lap,
                success_probability=0.0,
                risk_factor="high",
            )

        # Fresh tire advantage during undercut window
        # Driver on fresh tires gains ~0.3s per lap for ~3 laps
        advantage_laps = min(window_laps, UNDERCUT_WINDOW_LAPS)
        total_advantage = advantage_laps * lap_time_diff

        # Pit stop time loss
        net_advantage = total_advantage - self.pit_loss * (1 - SC_PIT_LOSS_FACTOR)

        # Success probability
        if net_advantage > 0:
            prob = min(0.9, 0.5 + net_advantage / 5.0)
            risk = "low" if net_advantage > 2.0 else "medium"
        else:
            prob = max(0.1, 0.5 + net_advantage / 5.0)
            risk = "high"

        return UndercutAnalysis(
            possible=net_advantage > -2.0,
            time_advantage=round(net_advantage, 2),
            optimal_pit_lap=pitting_driver_lap,
            success_probability=round(prob, 2),
            risk_factor=risk,
        )

    def analyze_overcut(
        self,
        target_pit_lap: int,
        stay_out_laps: int = 2,
        lap_time_diff: float = 0.2,
    ) -> UndercutAnalysis:
        """
        Analyze overcut potential.

        Overcut: Staying out longer than a competitor who has pitted,
        hoping to gain track position if they lose time in traffic.

        Args:
            target_pit_lap: Lap the target driver pits
            stay_out_laps: How many extra laps to stay out
            lap_time_diff: Time advantage from clear air per lap

        Returns:
            UndercutAnalysis (reused type) for overcut
        """
        # Overcut works best when:
        # 1. Target gets stuck in traffic after pit stop
        # 2. Clear air allows faster laps
        # 3. Tire degradation difference is minimal
        traffic_delay = 0.5  # Estimated seconds lost in traffic per lap
        clear_air_advantage = stay_out_laps * lap_time_diff

        # Tire penalty for staying out
        tire_degradation_penalty = stay_out_laps * 0.1  # ~0.1s per extra lap

        net_advantage = clear_air_advantage + traffic_delay - tire_degradation_penalty

        # Success probability (lower than undercut)
        if net_advantage > 0:
            prob = min(0.7, 0.4 + net_advantage / 8.0)
            risk = "medium" if net_advantage > 1.0 else "high"
        else:
            prob = max(0.1, 0.3 + net_advantage / 5.0)
            risk = "high"

        return UndercutAnalysis(
            possible=net_advantage > -3.0,
            time_advantage=round(net_advantage, 2),
            optimal_pit_lap=target_pit_lap + stay_out_laps,
            success_probability=round(prob, 2),
            risk_factor=risk,
        )

    def analyze_sc_windows(
        self,
        sc_probability: float,
        typical_sc_lap: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze virtual safety car / safety car pit windows.

        Args:
            sc_probability: Probability of SC (from circuit data)
            typical_sc_lap: Typical lap for SC deployment (if known)

        Returns:
            Dict with SC window analysis
        """
        analysis = {
            "sc_probability": sc_probability,
            "optimal_sc_pit_lap": None,
            "time_saved_under_sc": 0.0,
            "recommendation": "",
        }

        if sc_probability < 0.1:
            analysis["recommendation"] = "Low SC probability, plan normal strategy"
            return analysis

        # Under SC, pit stop time loss is reduced by ~45%
        time_saved = self.pit_loss * (1 - SC_PIT_LOSS_FACTOR)

        # If typical SC lap is known, calculate optimal pit lap to align
        if typical_sc_lap is not None:
            # Ideally pit just before SC to minimize time loss
            optimal_pit = max(1, typical_sc_lap - 2)
            analysis["optimal_sc_pit_lap"] = optimal_pit

        analysis["time_saved_under_sc"] = round(time_saved, 2)

        if sc_probability > 0.3:
            analysis["recommendation"] = (
                f"Consider pitting under SC (saves ~{time_saved:.1f}s). "
                "Early pit stops can be advantageous."
            )
        else:
            analysis["recommendation"] = (
                f"SC possible ({sc_probability:.0%}), "
                "be ready to adapt strategy opportunistically."
            )

        return analysis


# ── Telemetry Pace Delta Estimator ──────────────────────────────────────────

class TelemetryPaceEstimator:
    """
    Estimates per-lap pace deltas from telemetry data.

    Uses OpenF1 data to calculate:
    - Long-run pace (race simulations)
    - Qualifying pace
    - Tire degradation rates from actual telemetry
    - Driver-specific stint performance
    """

    def __init__(self, circuit_id: str):
        self.circuit_id = circuit_id

    def estimate_long_run_deltas(
        self,
        driver_id: str,
        stint_data: Optional[List[Dict]] = None,
    ) -> Dict[str, float]:
        """
        Estimate long-run pace deltas from telemetry or historical data.

        Args:
            driver_id: Driver identifier
            stint_data: Optional telemetry stint data

        Returns:
            Dict with pace metrics
        """
        from data.driver_data import get_driver

        try:
            driver = get_driver(driver_id)
            tire_mgmt = driver.get("tire_management", 7.0) / 10.0
            elo_score = driver.get("elo", 1500)
            experience = driver.get("experience_races", 0)
        except Exception:
            tire_mgmt = 0.7
            elo_score = 1500
            experience = 50

        # Estimate telemetry deltas based on driver profile
        return {
            "long_run_pace_delta": round(-0.1 + (elo_score - 1500) / 1000, 3),
            "tire_deg_advantage": round((tire_mgmt - 0.7) * 0.5, 3),
            "qualifying_vs_race_ratio": round(0.6 + experience / 500, 3),
            "consistency_score": round(min(1.0, tire_mgmt + (elo_score - 1400) / 300), 3),
            "estimated_race_pace": round(80.0 - (elo_score - 1400) * 0.02, 2),
        }

    def calculate_long_run_pace(
        self,
        telemetry_data: List[Dict],
    ) -> Dict[str, float]:
        """
        Calculate long-run pace from actual telemetry data.

        Args:
            telemetry_data: List of lap telemetry dicts

        Returns:
            Dict with pace statistics
        """
        if not telemetry_data:
            return {"avg_pace": 0.0, "degradation_rate": 0.0, "peak_pace": 0.0}

        lap_times = [lap.get("lap_time", 0) for lap in telemetry_data if lap.get("lap_time")]
        if len(lap_times) < 3:
            return {"avg_pace": 0.0, "degradation_rate": 0.0, "peak_pace": 0.0}

        # Filter outliers
        lap_times = sorted(lap_times)[1:-1]  # Remove fastest and slowest

        avg_pace = sum(lap_times) / len(lap_times)
        peak_pace = min(lap_times)

        # Calculate degradation rate from last 5 laps vs first 5 laps
        if len(lap_times) >= 10:
            first_5 = sum(lap_times[:5]) / 5
            last_5 = sum(lap_times[-5:]) / 5
            degradation_rate = (last_5 - first_5) / 5  # seconds per lap
        else:
            degradation_rate = 0.0

        return {
            "avg_pace": round(avg_pace, 3),
            "degradation_rate": round(degradation_rate, 3),
            "peak_pace": round(peak_pace, 3),
            "consistency": round(1.0 - np.std(lap_times) / max(avg_pace, 0.001), 3),
        }


# ── Main Strategy Analysis ──────────────────────────────────────────────────

def analyze_race_strategy(
    circuit_id: str,
    race_laps: int,
    driver_id: str = "",
    available_compounds: Optional[List[str]] = None,
    temperature: float = 25.0,
    sc_probability: float = 0.3,
) -> PitStrategyResult:
    """
    Comprehensive pit strategy analysis for a race.

    Args:
        circuit_id: Circuit identifier
        race_laps: Total race laps
        driver_id: Optional specific driver to analyze
        available_compounds: Optional list of available compound names
        temperature: Expected track temperature
        sc_probability: Safety car probability

    Returns:
        PitStrategyResult with all strategy analyses
    """
    # Parse compounds
    if available_compounds:
        compounds = [TireCompound(c) for c in available_compounds]
    else:
        compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]

    # Initialize simulator
    simulator = PitStrategySimulator(circuit_id, race_laps)

    # Get driver tire management
    driver_tire_mgmt = 0.7
    if driver_id:
        try:
            from data.driver_data import get_driver
            driver = get_driver(driver_id)
            driver_tire_mgmt = driver.get("tire_management", 7.0) / 10.0
        except Exception:
            pass

    # Evaluate all strategies
    all_strategies = simulator.generate_strategies(
        compounds, driver_tire_mgmt, temperature
    )
    optimal = all_strategies[0] if all_strategies else simulator._default_strategy()

    # Undercut/overcut analysis
    undercut = simulator.analyze_undercut(
        pitting_driver_lap=optimal.stints[0].end_lap if optimal.stints else race_laps // 2
    )
    overcut = simulator.analyze_overcut(
        target_pit_lap=optimal.stints[0].end_lap if optimal.stints else race_laps // 2
    )

    # SC window analysis
    sc_analysis = simulator.analyze_sc_windows(sc_probability)

    # Driver recommendations
    driver_recs = {
        "top_positions": "Conservative 1-stop, protect track position",
        "midfield": "Balanced 2-stop, look for undercut opportunities",
        "backmarker": "Aggressive strategy, alternative tire choice",
    }

    # Telemetry deltas
    telemetry = TelemetryPaceEstimator(circuit_id)
    telemetry_deltas = telemetry.estimate_long_run_deltas(driver_id) if driver_id else {}

    return PitStrategyResult(
        circuit_id=circuit_id,
        race_laps=race_laps,
        optimal_strategy=optimal,
        alternative_strategies=all_strategies[1:5] if len(all_strategies) > 1 else [],
        undercut_analysis=undercut,
        overcut_analysis=overcut,
        sc_window_analysis=sc_analysis,
        driver_recommendations=driver_recs,
        telemetry_deltas=telemetry_deltas,
    )


def strategy_to_dict(result: PitStrategyResult) -> Dict:
    """Convert PitStrategyResult to serializable dict."""
    return {
        "circuit_id": result.circuit_id,
        "race_laps": result.race_laps,
        "optimal_strategy": {
            "name": result.optimal_strategy.strategy_name,
            "pit_stops": result.optimal_strategy.total_pit_stops,
            "pit_time_loss": result.optimal_strategy.total_pit_time_loss,
            "tire_time_loss": result.optimal_strategy.total_tire_time_loss,
            "total_time_loss": result.optimal_strategy.total_time_loss,
            "avg_lap_delta": result.optimal_strategy.avg_lap_time_delta,
            "risk_level": result.optimal_strategy.risk_level,
            "stints": [
                {
                    "compound": s.compound.value,
                    "start_lap": s.start_lap,
                    "end_lap": s.end_lap,
                    "avg_delta": s.avg_lap_time_delta,
                }
                for s in result.optimal_strategy.stints
            ],
        },
        "alternative_strategies": [
            {
                "name": s.strategy_name,
                "total_time_loss": s.total_time_loss,
                "risk_level": s.risk_level,
            }
            for s in result.alternative_strategies
        ],
        "undercut": {
            "possible": result.undercut_analysis.possible,
            "time_advantage": result.undercut_analysis.time_advantage,
            "success_probability": result.undercut_analysis.success_probability,
            "risk": result.undercut_analysis.risk_factor,
        },
        "overcut": {
            "possible": result.overcut_analysis.possible,
            "time_advantage": result.overcut_analysis.time_advantage,
            "success_probability": result.overcut_analysis.success_probability,
            "risk": result.overcut_analysis.risk_factor,
        },
        "safety_car": result.sc_window_analysis,
        "recommendations": result.driver_recommendations,
        "telemetry": result.telemetry_deltas,
    }


__all__ = [
    "TireCompound",
    "TireDegradationModel",
    "PitStrategySimulator",
    "TelemetryPaceEstimator",
    "StintResult",
    "StrategyEvaluation",
    "UndercutAnalysis",
    "PitStrategyResult",
    "analyze_race_strategy",
    "strategy_to_dict",
]

