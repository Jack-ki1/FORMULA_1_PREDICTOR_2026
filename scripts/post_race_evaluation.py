"""
Post-race evaluation script - resolves pending user picks after a real race.
Updates UserPick and LeaderboardEntry tables with points.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database.connection import db
from backend.app.database.models import UserPick, LeaderboardEntry, RaceResult
from backend.app.engine.fantasy_scoring import fantasy_scoring
from datetime import datetime


def post_race_evaluation(race_id: int):
    """
    Evaluate user picks after a race completes.
    
    Args:
        race_id: Race identifier
    """
    print(f"Running post-race evaluation for race {race_id}...")
    
    try:
        # Connect to database
        db.connect()
        print("✓ Database connection established")
        
        with db.session_scope() as session:
            # Get actual race results
            race_results = session.query(RaceResult).filter(
                RaceResult.race_id == race_id
            ).all()
            
            if not race_results:
                print(f"✗ No race results found for race {race_id}")
                return
            
            print(f"✓ Found {len(race_results)} race results")
            
            # Build race results dictionary
            results_dict = {}
            for result in race_results:
                driver_code = result.driver_id
                results_dict[driver_code] = {
                    'race_position': result.position,
                    'qualifying_position': result.grid,
                    'fastest_lap': result.fastest_lap,
                    'dnf': result.status != 'Finished',
                }
            
            # Get pending user picks for this race
            pending_picks = session.query(UserPick).filter(
                UserPick.race_id == race_id,
                UserPick.status == 'pending'
            ).all()
            
            print(f"✓ Found {len(pending_picks)} pending user picks")
            
            # Evaluate each user pick
            for pick in pending_picks:
                driver_result = results_dict.get(pick.driver_id)
                
                if driver_result:
                    # Calculate fantasy points
                    points_breakdown = fantasy_scoring.calculate_driver_fantasy_points(
                        pick.driver_id,
                        **driver_result
                    )
                    
                    # Update user pick
                    pick.points = points_breakdown['total_points']
                    pick.status = 'resolved'
                    
                    print(f"✓ Resolved pick: {pick.user_nickname} - {pick.driver_id} ({pick.points} points)")
                    
                    # Update leaderboard
                    leaderboard_entry = session.query(LeaderboardEntry).filter(
                        LeaderboardEntry.nickname == pick.user_nickname
                    ).first()
                    
                    if leaderboard_entry:
                        leaderboard_entry.total_score += pick.points
                        leaderboard_entry.updated_at = datetime.utcnow()
                    else:
                        new_entry = LeaderboardEntry(
                            nickname=pick.user_nickname,
                            total_score=pick.points,
                        )
                        session.add(new_entry)
            
            print(f"✓ Evaluated {len(pending_picks)} user picks")
        
        print("\n✓ Post-race evaluation completed")
        
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.disconnect()


if __name__ == "__main__":
    # Get race ID from command line or use latest
    if len(sys.argv) > 1:
        race_id = int(sys.argv[1])
    else:
        # Get latest completed race
        print("No race ID provided, use latest completed race")
        # In production, query database for latest completed race
        race_id = 1  # Placeholder
    
    post_race_evaluation(race_id)
