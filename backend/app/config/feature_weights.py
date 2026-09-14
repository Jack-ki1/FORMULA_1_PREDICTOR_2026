"""
Feature weights and model tuning parameters.
These parameters directly correspond to the sliders in the JSX Model Tuning tab.
Each parameter is stored as (default, min, max, step) for consistent UI rendering.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class FeatureWeights:
    """Model tuning parameters that match the JSX's Model Tuning tab."""
    
    # Chaos Level: Controls prediction uncertainty (0 = dominant favorites, 100 = chaotic)
    # Affects the exponent in probability distribution
    CHAOS_LEVEL = {
        'default': int(os.getenv('CHAOS_LEVEL_DEFAULT', '50')),
        'min': 0,
        'max': 100,
        'step': 1,
        'description': 'Controls prediction uncertainty. Lower values favor dominant favorites, higher values allow more upsets.',
    }
    
    # Wet Weather Influence: How much wet-weather skill matters in rain/mixed conditions
    # 0 = ignore wet skill, 100 = full wet skill dominance
    WET_INFLUENCE = {
        'default': int(os.getenv('WET_INFLUENCE_DEFAULT', '50')),
        'min': 0,
        'max': 100,
        'step': 1,
        'description': 'Weight given to driver wet-weather skill in rain/mixed conditions.',
    }
    
    # Reliability Influence: How much reliability affects DNF risk and predictions
    # 0 = ignore reliability, 100 = full reliability impact
    RELIABILITY_INFLUENCE = {
        'default': int(os.getenv('RELIABILITY_INFLUENCE_DEFAULT', '50')),
        'min': 0,
        'max': 100,
        'step': 1,
        'description': 'Weight given to driver/team reliability in DNF risk calculations.',
    }
    
    # Strategy Aggressiveness: Tendency to predict 2-stop vs 1-stop strategies
    # 0 = conservative (more 1-stops), 100 = aggressive (more 2-stops)
    STRATEGY_AGGRESSIVENESS = {
        'default': int(os.getenv('STRATEGY_AGGRESSIVENESS_DEFAULT', '50')),
        'min': 0,
        'max': 100,
        'step': 1,
        'description': 'Strategy prediction aggressiveness. Higher values predict more 2-stop strategies.',
    }
    
    # Grid Weight: How much starting grid position affects race predictions
    # 0 = ignore grid position, 100 = full empirical grid weight
    # Based on ~43% historical pole-to-win rate
    GRID_WEIGHT = {
        'default': int(os.getenv('GRID_WEIGHT_DEFAULT', '55')),
        'min': 0,
        'max': 100,
        'step': 1,
        'description': 'Weight given to starting grid position in race predictions. Based on historical pole-to-win rate.',
    }
    
    @classmethod
    def get_all_weights(cls):
        """Return all feature weights as a dictionary."""
        return {
            'chaos_level': cls.CHAOS_LEVEL,
            'wet_influence': cls.WET_INFLUENCE,
            'reliability_influence': cls.RELIABILITY_INFLUENCE,
            'strategy_aggressiveness': cls.STRATEGY_AGGRESSIVENESS,
            'grid_weight': cls.GRID_WEIGHT,
        }
    
    @classmethod
    def get_defaults(cls):
        """Return default values for all weights."""
        return {
            'chaos_level': cls.CHAOS_LEVEL['default'],
            'wet_influence': cls.WET_INFLUENCE['default'],
            'reliability_influence': cls.RELIABILITY_INFLUENCE['default'],
            'strategy_aggressiveness': cls.STRATEGY_AGGRESSIVENESS['default'],
            'grid_weight': cls.GRID_WEIGHT['default'],
        }
    
    @classmethod
    def validate_weight(cls, weight_name, value):
        """Validate a weight value against its constraints."""
        weight_config = getattr(cls, weight_name.upper(), None)
        if not weight_config:
            raise ValueError(f"Unknown weight: {weight_name}")
        
        if not isinstance(value, (int, float)):
            raise ValueError(f"Weight must be numeric: {weight_name}")
        
        if value < weight_config['min'] or value > weight_config['max']:
            raise ValueError(
                f"{weight_name} must be between {weight_config['min']} and {weight_config['max']}"
            )
        
        return True
    
    @classmethod
    def get_chaos_factor(cls, chaos_level):
        """
        Convert chaos level to chaos factor for probability calculations.
        chaos_level 0 = "dominant favorites" (sharper concentration)
        chaos_level 100 = "chaotic" (flatter, more upset-prone)
        Returns factor between 0.35 and 1.6
        """
        return max(0.35, 1.6 - (chaos_level / 100) * 1.2)

# Global feature weights instance
feature_weights = FeatureWeights()
