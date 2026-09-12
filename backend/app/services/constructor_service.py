from data.team_data import get_all_enhanced_teams, get_team_power_rankings
class ConstructorService:
    def get_teams(self):
        return get_all_enhanced_teams()
    def get_power_rankings(self):
        return get_team_power_rankings()
constructor_service = ConstructorService()
