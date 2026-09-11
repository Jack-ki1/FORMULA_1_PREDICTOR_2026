"""
Grid model - real qualifying → grid, simulated fallback, manual override.
Implements the gridPriorMultiplier based on ~43% historical pole-to-win rate.
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from config.constants import grid_prior_multiplier
from config.settings import settings
from data.jolpica_client import JolpicaClient
from config.team_driver_lineup_2026 import get_all_drivers
from data.openf1_client import OpenF1Client
from data.fastf1_integration import FastF1Integration
from data.session_context import build_session_context
from data.validation import DataValidator
from data.fallback import FallbackStrategy
from models.prediction import Prediction, SessionData
from database.db import get_session

logger = logging.getLogger(__name__)


def generate_fallback_grid(all_drivers, session_context=None):
    """Generate a fallback grid based on driver strength when session context is incomplete."""
    grid = {}
    sorted_drivers = sorted(all_drivers, key=lambda d: d.get('strength', 50), reverse=True)
    for i, driver in enumerate(sorted_drivers):
        grid[driver['code']] = i + 1
    return grid


def calculate_grid_positions(race_id: str, session_type: str) -> Dict[str, int]:
    """
    Calculate grid positions for a race session.
    
    Returns:
        Dictionary mapping driver codes to grid positions
    """
    try:
        logger.info(f"Calculating grid positions for race {race_id}, session {session_type}")
        
        # Build session context with all available data sources
        session_context = build_session_context(race_id, session_type)
        
        # Get all drivers for the season
        all_drivers = get_all_drivers()
        driver_codes = [d['code'] for d in all_drivers]
        
        # Initialize grid positions
        grid_positions = {}
        
        # Apply grid prior multiplier (default 1.0 if not defined)
        grid_prior_multiplier = getattr(settings, 'GRID_PRIOR_MULTIPLIER', 1.0)
        
        # Process each driver
        for driver_code in driver_codes:
            # Get driver-specific data from session context
            strength = session_context.get('strength_adjustments', {}).get(driver_code, 0.0)
            
            # Calculate grid position based on strength and available data
            base_position = 11  # midfield default
            performance_factor = 1.0 - strength  # higher strength = lower (better) position
            
            # Apply grid prior multiplier
            adjusted_position = base_position * performance_factor * grid_prior_multiplier
            
            # Round to nearest integer and ensure it's within valid range
            grid_position = max(1, min(20, round(adjusted_position)))
            
            # Store in grid positions
            grid_positions[driver_code] = grid_position
        
        # If we don't have positions for all drivers, use fallback
        if len(grid_positions) < len(driver_codes):
            fallback_grid = generate_fallback_grid(all_drivers, session_context)
            grid_positions.update(fallback_grid)
        
        logger.info(f"Calculated grid positions for {len(grid_positions)} drivers")
        return grid_positions
        
    except Exception as e:
        logger.error(f"Error calculating grid positions: {e}")
        raise


def save_session_data_to_database(race_id: str, session_type: str, session_context: Dict[str, Any]):
    """Save session context data to database."""
    try:
        # Create session data record
        session_data = SessionData(
            race_id=race_id,
            session_type=session_type,
            strength_adjustments=session_context['strength_adjustments'],
            grid_positions=session_context['grid_positions'],
            sources=session_context['sources']
        )
        
        # Save to database
        with get_session() as db:
            db.add(session_data)
            db.commit()
            db.refresh(session_data)
        
        logger.info(f"Saved session data for race {race_id}, session {session_type}")
        
    except Exception as e:
        logger.error(f"Error saving session data for race {race_id}: {e}")
        raise

class GridModel:
    """
    Grid position model with three-tier fallback:
    1. Real qualifying results
    2. Simulated Q1-Q3 based on driver strength
    3. Manual override
    """
    
    def __init__(self):
        self.drivers = get_all_drivers()
        self.driver_map = {d['code']: d for d in self.drivers}
        self.manual_overrides = {}
    
    def get_grid_positions(
        self,
        season: int,
        round_number: int,
        use_real_qualifying: bool = True,
        manual_overrides: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Get grid positions with three-tier fallback.
        
        Args:
            season: Season year
            round_number: Round number
            use_real_qualifying: Whether to try real qualifying data
            manual_overrides: Manual grid position overrides
        
        Returns:
            Grid positions with source information
        """
        # Apply manual overrides
        if manual_overrides:
            self.manual_overrides.update(manual_overrides)
        
        # Try real qualifying first
        if use_real_qualifying:
            try:
                real_grid = self._get_real_qualifying(season, round_number)
                if real_grid:
                    # Apply manual overrides to real grid
                    if self.manual_overrides:
                        real_grid.update(self.manual_overrides)
                    return {
                        'grid': real_grid,
                        'source': 'live',
                        'method': 'real_qualifying',
                    }
            except Exception as e:
                print(f"Could not get real qualifying: {e}")
        
        # Fallback to simulated qualifying
        simulated_grid = self._simulate_qualifying()
        
        # Apply manual overrides
        if self.manual_overrides:
            simulated_grid.update(self.manual_overrides)
        
        return {
            'grid': simulated_grid,
            'source': 'simulated',
            'method': 'simulated_qualifying',
        }
    
    def _get_real_qualifying(self, season: int, round_number: int) -> Optional[Dict[str, int]]:
        """Get real qualifying results from Jolpica API."""
        try:
            client = JolpicaClient()
            result = client.get_qualifying_result(season, round_number)
            
            if result['source'] == 'live' and result['data']:
                # Parse qualifying results
                grid = {}
                qualifying_data = result['data']
                
                # Handle different data formats
                if isinstance(qualifying_data, dict) and 'grid' in qualifying_data:
                    return qualifying_data['grid']
                elif isinstance(qualifying_data, list):
                    for i, entry in enumerate(qualifying_data):
                        driver_code = entry.get('driverCode') or entry.get('DriverCode')
                        position = entry.get('position') or entry.get('Position') or (i + 1)
                        if driver_code:
                            grid[driver_code.upper()] = position
                
                return grid if grid else None
            
            return None
            
        except Exception as e:
            print(f"Error fetching real qualifying: {e}")
            return None
    
    def _simulate_qualifying(self) -> Dict[str, int]:
        """
        Simulate qualifying session based on driver strength.
        Simulates Q1, Q2, Q3 elimination format.
        """
        # Start with all drivers
        current_drivers = self.drivers.copy()
        grid_positions = {}
        
        # With the 22-car 2026 field the three sessions are 22→16→10.
        # This preserves the familiar ten-car Q3 and assigns every grid slot.
        q1_results = self._simulate_session(current_drivers, session_variance=0.8)
        eliminated_q1 = q1_results[-6:]
        for position, driver in enumerate(eliminated_q1, start=17):
            grid_positions[driver['code']] = position
        
        # Q2 participants
        q2_drivers = [d for d in current_drivers if d not in eliminated_q1]
        
        # Simulate Q2 (eliminate slowest 6)
        q2_results = self._simulate_session(q2_drivers, session_variance=0.6)
        eliminated_q2 = q2_results[-6:]
        for position, driver in enumerate(eliminated_q2, start=11):
            grid_positions[driver['code']] = position
        
        # Q3 participants
        q3_drivers = [d for d in q2_drivers if d not in eliminated_q2]
        
        # Simulate Q3 (determine positions 1-10)
        q3_results = self._simulate_session(q3_drivers, session_variance=0.4)
        for i, driver in enumerate(q3_results):
            grid_positions[driver['code']] = i + 1  # Positions 1-10
        
        return grid_positions
    
    def _simulate_session(self, drivers: List[Dict], session_variance: float = 0.5) -> List[Dict]:
        """
        Simulate a qualifying session for given drivers.
        
        Args:
            drivers: List of driver dictionaries
            session_variance: Random variance factor
        
        Returns:
            Sorted list of drivers by simulated lap time
        """
        lap_times = []
        
        for driver in drivers:
            # Base lap time based on strength (inverse - lower strength = slower)
            base_time = 90.0 - (driver['strength'] * 0.15)
            
            # Add random variance
            variance = (np.random.random() - 0.5) * session_variance * 2.0
            lap_time = base_time + variance
            
            lap_times.append({
                'driver': driver,
                'lap_time': lap_time,
            })
        
        # Sort by lap time
        lap_times.sort(key=lambda x: x['lap_time'])
        
        return [item['driver'] for item in lap_times]
    
    def apply_grid_penalties(
        self,
        grid_positions: Dict[str, int],
        penalties: Dict[str, int],
    ) -> Dict[str, int]:
        """
        Apply grid penalties to positions.
        
        Args:
            grid_positions: Current grid positions
            penalties: Dictionary of driver codes to penalty positions
        
        Returns:
            Updated grid positions
        """
        # Sort by current position
        sorted_positions = sorted(grid_positions.items(), key=lambda x: x[1])
        
        # Apply penalties
        updated_positions = {}
        position_queue = list(range(1, 23))
        
        for driver_code, current_pos in sorted_positions:
            penalty = penalties.get(driver_code, 0)
            
            if penalty > 0:
                # Apply penalty (move back)
                new_pos = current_pos + penalty
                # Ensure position doesn't exceed 22
                new_pos = min(22, new_pos)
                updated_positions[driver_code] = new_pos
            else:
                # Keep original position
                updated_positions[driver_code] = current_pos
        
        # Resolve position conflicts
        updated_positions = self._resolve_position_conflicts(updated_positions)
        
        return updated_positions
    
    def _resolve_position_conflicts(self, positions: Dict[str, int]) -> Dict[str, int]:
        """Resolve conflicts where multiple drivers have the same position."""
        # Count occurrences of each position
        position_counts = {}
        for pos in positions.values():
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Resolve conflicts
        resolved = {}
        used_positions = set()
        
        # Sort drivers by position (ascending)
        sorted_drivers = sorted(positions.items(), key=lambda x: x[1])
        
        for driver_code, position in sorted_drivers:
            # Find next available position
            while position in used_positions:
                position += 1
            
            resolved[driver_code] = position
            used_positions.add(position)
        
        return resolved
    
    def set_manual_override(self, driver_code: str, position: int):
        """Set a manual grid position override."""
        self.manual_overrides[driver_code.upper()] = position
    
    def clear_manual_overrides(self):
        """Clear all manual overrides."""
        self.manual_overrides = {}
    
    def get_grid_multiplier(self, position: int) -> float:
        """Get grid position multiplier using the empirical formula."""
        return grid_prior_multiplier(position)
    
    def analyze_grid_impact(
        self,
        grid_positions: Dict[str, int],
        predicted_winner: str,
    ) -> Dict[str, Any]:
        """
        Analyze the impact of grid position on predicted winner.
        
        Args:
            grid_positions: Grid positions
            predicted_winner: Predicted race winner
        
        Returns:
            Grid impact analysis
        """
        winner_grid = grid_positions.get(predicted_winner, 12)
        grid_multiplier = self.get_grid_multiplier(winner_grid)
        
        # Historical context
        pole_win_rate = 0.43  # ~43% historical pole-to-win rate
        
        return {
            'predicted_winner': predicted_winner,
            'grid_position': winner_grid,
            'grid_multiplier': grid_multiplier,
            'pole_win_rate': pole_win_rate,
            'win_probability_adjustment': grid_multiplier * pole_win_rate,
            'grid_impact_factor': grid_multiplier,
        }


# Global grid model instance
grid_model = GridModel()
