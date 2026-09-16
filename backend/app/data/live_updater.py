"""
Live data updater - background poller that refreshes cache on an interval.
Runs as a background thread/scheduler to keep data fresh.
"""
import threading
import time
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    schedule = None
from typing import Callable
from backend.app.config.settings import settings
from backend.app.config.api_settings import api_settings


class LiveUpdater:
    """Background scheduler for live data updates."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.update_interval = settings.LIVE_UPDATE_INTERVAL
        self.update_callbacks = []
    
    def add_update_callback(self, callback: Callable):
        """
        Add a callback function to be called on each update cycle.
        
        Args:
            callback: Function to call during update cycle
        """
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable):
        """
        Remove a callback function.
        
        Args:
            callback: Function to remove
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def _update_jolpica_data(self):
        """Update data from Jolpica API."""
        try:
            from backend.app.data.jolpica_client import JolpicaClient
            
            client = JolpicaClient()
            
            # Update driver standings
            client.get_driver_standings(settings.SEASON_YEAR)
            
            # Update constructor standings
            client.get_constructor_standings(settings.SEASON_YEAR)
            
            print("Jolpica data updated successfully")
            
        except Exception as e:
            print(f"Error updating Jolpica data: {e}")
    
    def _update_openf1_data(self):
        """Update data from OpenF1 API."""
        try:
            from backend.app.data.openf1_client import OpenF1Client
            
            client = OpenF1Client()
            
            # Get current year sessions
            client.get_sessions(settings.SEASON_YEAR)
            
            print("OpenF1 data updated successfully")
            
        except Exception as e:
            print(f"Error updating OpenF1 data: {e}")
    
    def _update_fastf1_data(self):
        """Update data from FastF1."""
        try:
            from backend.app.data.fastf1_integration import FastF1Integration
            
            integration = FastF1Integration()
            
            # Get latest completed race data
            from backend.app.data.calendar_2026 import get_completed_races
            completed = get_completed_races()
            
            if completed:
                latest_race = completed[-1]
                integration.get_session_results(
                    settings.SEASON_YEAR,
                    latest_race['round'],
                    'R'
                )
            
            print("FastF1 data updated successfully")
            
        except Exception as e:
            print(f"Error updating FastF1 data: {e}")
    
    def _run_update_cycle(self):
        """Run a single update cycle for all data sources."""
        print(f"Starting update cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update all enabled data sources
        if api_settings.is_enabled('jolpica'):
            self._update_jolpica_data()
        
        if api_settings.is_enabled('openf1'):
            self._update_openf1_data()
        
        if api_settings.is_enabled('fastf1'):
            self._update_fastf1_data()
        
        # Call registered callbacks
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in update callback: {e}")
        
        print(f"Update cycle completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        if not SCHEDULE_AVAILABLE:
            print("Schedule library not available, using simple interval loop")
            while self.running:
                self._run_update_cycle()
                time.sleep(self.update_interval)
        else:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
    
    def start(self):
        """Start the background updater — non-blocking (initial cycle in background)."""
        if self.running:
            print("Live updater is already running")
            return
        
        self.running = True
        
        # Schedule regular updates (if schedule library is available)
        if SCHEDULE_AVAILABLE:
            schedule.every(self.update_interval).seconds.do(self._run_update_cycle)
        
        # Start scheduler thread that runs initial update in background
        # so Flask health endpoint is available immediately (previously blocked ~20s)
        def _background_initial_and_loop():
            try:
                # small delay so Flask can bind port before heavy FastF1 fetch
                time.sleep(0.5)
                self._run_update_cycle()
            except Exception as e:
                print(f"Initial live update failed (non-fatal): {e}")
            # then enter normal scheduler loop
            self._scheduler_loop()

        self.thread = threading.Thread(target=_background_initial_and_loop, daemon=True)
        self.thread.start()
        
        print(f"Live updater started with {self.update_interval}s interval (initial sync in background)")
    
    def stop(self):
        """Stop the background updater."""
        if not self.running:
            print("Live updater is not running")
            return
        
        self.running = False
        
        if SCHEDULE_AVAILABLE:
            schedule.clear()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("Live updater stopped")
    
    def force_update(self):
        """Force an immediate update cycle."""
        self._run_update_cycle()
    
    def is_running(self) -> bool:
        """Check if the updater is running."""
        return self.running


# Global live updater instance
live_updater = LiveUpdater()


def start_live_updater():
    """Start the global live updater."""
    live_updater.start()


def stop_live_updater():
    """Stop the global live updater."""
    live_updater.stop()


def force_live_update():
    """Force an immediate update."""
    live_updater.force_update()
