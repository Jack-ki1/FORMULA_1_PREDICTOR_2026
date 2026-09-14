"""Vectorised, rank-safe Monte Carlo race simulator."""
from __future__ import annotations

from typing import Any, Dict
import numpy as np

from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.config.constants import grid_prior_multiplier


class MonteCarloSimulator:
    """Simulate complete finishing orders; every run has exactly one winner."""

    def __init__(self, num_simulations: int = 1000):
        self.num_simulations = num_simulations
        self.drivers = get_all_drivers()
        self.driver_map = {driver['code']: driver for driver in self.drivers}

    def simulate_race(self, race_id: str, grid_positions: Dict[str, int] | None,
                      weather: str = 'dry', safety_car_prob: float = 0.3,
                      chaos_level: float = 50, num_simulations: int | None = None,
                      seed: int | None = None) -> Dict[str, Any]:
        """Sample pace, grid, weather and DNF risk into full race orders."""
        n = max(100, min(int(num_simulations or self.num_simulations), 100_000))
        codes = list(self.driver_map)
        grid = self._complete_grid(grid_positions or {}, codes)
        rng = np.random.default_rng(seed)
        strength = np.array([self.driver_map[c]['strength'] / 100 for c in codes])
        reliability = np.array([self.driver_map[c]['reliability'] / 100 for c in codes])
        wet_skill = np.array([self.driver_map[c]['wet_skill'] / 100 for c in codes])
        grid_effect = np.array([grid_prior_multiplier(grid[c]) for c in codes])
        weather_effect = 0.0
        if weather == 'wet':
            weather_effect = (wet_skill - wet_skill.mean()) * .22
        elif weather == 'mixed':
            weather_effect = (wet_skill - wet_skill.mean()) * .11
        base = strength * .72 + grid_effect * .28 + weather_effect
        score = base + rng.normal(0, .025 + chaos_level / 5000, (n, len(codes))) + rng.normal(0, .045 + chaos_level / 1400, (n, len(codes)))
        dnf_rate = (1 - reliability) * (.09 + chaos_level / 1500)
        if weather == 'wet': dnf_rate *= 1.6
        elif weather == 'mixed': dnf_rate *= 1.25
        dnf_rate *= 1 + max(0., min(1., safety_car_prob)) * .35
        dnf = rng.random((n, len(codes))) < dnf_rate
        score[dnf] = -np.inf
        order = np.argsort(-score, axis=1)
        positions = np.empty_like(order)
        positions[np.arange(n)[:, None], order] = np.arange(1, len(codes) + 1)
        positions[dnf] = len(codes) + 1
        probabilities: Dict[str, Dict[str, float]] = {}
        for index, code in enumerate(codes):
            driver_positions = positions[:, index]
            classified = driver_positions <= len(codes)
            probabilities[code] = {
                'win_prob': float(np.mean(driver_positions == 1)),
                'podium_prob': float(np.mean(driver_positions <= 3)),
                'points_prob': float(np.mean(driver_positions <= 10)),
                'dnf_prob': float(np.mean(~classified)),
                'avg_position': float(np.mean(driver_positions[classified])) if np.any(classified) else float(len(codes) + 1),
            }
        wins = np.array([p['win_prob'] for p in probabilities.values()])
        entropy = -sum(p * np.log2(p) for p in wins if p > 0)
        confidence = float(1 - entropy / np.log2(len(codes))) if len(codes) > 1 else 1.
        return {'race_id': race_id, 'num_simulations': n, 'weather': weather,
                'safety_car_prob': safety_car_prob, 'chaos_level': chaos_level,
                'results': {'probabilities': probabilities, 'confidence': confidence, 'num_valid_simulations': n}}

    @staticmethod
    def _complete_grid(grid_positions: Dict[str, int], codes: list[str]) -> Dict[str, int]:
        """Sanitise supplied grid and fill missing drivers without collisions."""
        def grid_value(code: str) -> int:
            try: return int(grid_positions.get(code, 99))
            except (TypeError, ValueError): return 99
        ordered = sorted(codes, key=lambda code: (grid_value(code), code))
        return {code: position for position, code in enumerate(ordered, start=1)}

    def get_confidence_intervals(self, race_id: str, grid_positions: Dict[str, int], confidence_level: float = .95) -> Dict[str, Dict[str, float]]:
        results = self.simulate_race(race_id, grid_positions)
        z_score, n = (1.96 if confidence_level >= .95 else 1.64), results['num_simulations']
        intervals = {}
        for code, values in results['results']['probabilities'].items():
            probability = values['win_prob']
            margin = z_score * np.sqrt(probability * (1 - probability) / n)
            intervals[code] = {'win_prob_lower': max(0., probability-margin), 'win_prob_upper': min(1., probability+margin),
                               'avg_position_lower': max(1., values['avg_position']-2), 'avg_position_upper': min(22., values['avg_position']+2)}
        return intervals


monte_carlo = MonteCarloSimulator()
