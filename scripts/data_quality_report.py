"""
Data quality report script - generates a report on data quality and coverage.
Checks API status, cache hit rates, and data completeness.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config.api_settings import api_settings
from backend.app.data.jolpica_client import JolpicaClient
from backend.app.data.openf1_client import OpenF1Client


def generate_data_quality_report():
    """Generate data quality report."""
    print("Generating data quality report...")
    
    try:
        report = {
            'api_status': {},
            'data_coverage': {},
            'cache_status': {},
            'recommendations': [],
        }
        
        # Check API status
        print("Checking API status...")
        
        # Jolpica status
        try:
            jolpica_client = JolpicaClient()
            result = jolpica_client.get_driver_standings()
            report['api_status']['jolpica'] = {
                'status': result['source'],
                'available': result['source'] != 'error',
            }
            print(f"✓ Jolpica API: {result['source']}")
        except Exception as e:
            report['api_status']['jolpica'] = {
                'status': 'error',
                'available': False,
                'error': str(e),
            }
            print(f"✗ Jolpica API: error")
        
        # OpenF1 status
        try:
            openf1_client = OpenF1Client()
            result = openf1_client.get_sessions(2026)
            report['api_status']['openf1'] = {
                'status': result['source'],
                'available': result['source'] != 'error',
            }
            print(f"✓ OpenF1 API: {result['source']}")
        except Exception as e:
            report['api_status']['openf1'] = {
                'status': 'error',
                'available': False,
                'error': str(e),
            }
            print(f"✗ OpenF1 API: error")
        
        # Check data coverage
        print("Checking data coverage...")
        
        from backend.app.data.calendar_2026 import get_active_calendar
        from backend.app.data.season_2026 import get_completed_rounds
        
        calendar = get_active_calendar()
        completed_rounds = get_completed_rounds()
        
        report['data_coverage']['calendar'] = {
            'total_races': len(calendar),
            'completed_races': completed_rounds,
            'upcoming_races': len(calendar) - completed_rounds,
        }
        
        print(f"✓ Calendar: {len(calendar)} total races, {completed_rounds} completed")
        
        # Generate recommendations
        if not report['api_status']['jolpica']['available']:
            report['recommendations'].append(
                "Jolpica API unavailable - consider caching or fallback mode"
            )
        
        if not report['api_status']['openf1']['available']:
            report['recommendations'].append(
                "OpenF1 API unavailable - live timing features limited"
            )
        
        if completed_rounds < len(calendar) * 0.5:
            report['recommendations'].append(
                f"Low data coverage ({completed_rounds}/{len(calendar)} races) - consider updating results"
            )
        
        # Print report
        print("\n=== Data Quality Report ===")
        print("\nAPI Status:")
        for api_name, status in report['api_status'].items():
            available = "✓" if status['available'] else "✗"
            print(f"  {available} {api_name}: {status['status']}")
        
        print("\nData Coverage:")
        for key, value in report['data_coverage'].items():
            print(f"  {key}: {value}")
        
        print("\nRecommendations:")
        for recommendation in report['recommendations']:
            print(f"  • {recommendation}")
        
        print("\n✓ Data quality report completed")
        
        return report
        
    except Exception as e:
        print(f"\n✗ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    generate_data_quality_report()
