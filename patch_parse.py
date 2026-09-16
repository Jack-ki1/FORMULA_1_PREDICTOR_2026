import pathlib, ast

p = pathlib.Path("backend/app/data/jolpica_client.py")
s = p.read_text()

helper = '''
    @staticmethod
    def _extract_standings_rows(payload, kind):
        """Flatten an Ergast StandingsTable envelope into plain rows.

        The upstream response nests everything under
        MRData.StandingsTable.StandingsLists[0].DriverStandings (or
        ConstructorStandings). Nothing previously extracted that, so the raw
        envelope was returned and every consumer saw `standings` as missing -
        which is why the UI showed an empty championship table even though the
        API was returning 23 drivers at round 14.
        """
        rows = []
        if not isinstance(payload, dict):
            return rows
        lists = (payload.get('MRData', {})
                        .get('StandingsTable', {})
                        .get('StandingsLists', []))
        if not lists:
            inner = payload.get('StandingsLists') or payload.get('standings')
            if isinstance(inner, list) and inner and isinstance(inner[0], dict) \\
                    and 'DriverStandings' in inner[0]:
                lists = inner
        if not lists:
            return rows

        latest = lists[-1]
        if kind == 'driver':
            for r in (latest.get('DriverStandings') or []):
                d = r.get('Driver', {}) or {}
                cons = (r.get('Constructors') or [{}])[0]
                rows.append({
                    'position': int(r.get('position', 0) or 0),
                    'driver_code': d.get('code') or (d.get('familyName') or '')[:3].upper(),
                    'driver_name': f"{d.get('givenName','')} {d.get('familyName','')}".strip(),
                    'driver_id': d.get('driverId'),
                    'nationality': d.get('nationality'),
                    'team': (cons.get('constructorId') or '').lower(),
                    'team_name': cons.get('name'),
                    'points': float(r.get('points', 0) or 0),
                    'wins': int(r.get('wins', 0) or 0),
                })
        else:
            for r in (latest.get('ConstructorStandings') or []):
                c = r.get('Constructor', {}) or {}
                rows.append({
                    'position': int(r.get('position', 0) or 0),
                    'team_id': (c.get('constructorId') or '').lower(),
                    'team_name': c.get('name'),
                    'nationality': c.get('nationality'),
                    'points': float(r.get('points', 0) or 0),
                    'wins': int(r.get('wins', 0) or 0),
                })
        rows.sort(key=lambda x: x['position'])
        return rows

'''

anchor = "    def get_driver_standings(self, season_year: int) -> Dict[str, Any]:"
assert anchor in s, "driver-standings anchor missing"
s = s.replace(anchor, helper.lstrip('\n') + anchor, 1)

old_driver = """            return response
        except Exception:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_standings_fallback()
            return {
                'data': fallback_data,
                'source': 'fallback',"""
new_driver = """            rows = self._extract_standings_rows(response.get('data'), 'driver')
            if rows:
                response['standings'] = rows
                response['data'] = rows
                return response
            # Envelope arrived but carried no rows - treat as a failed fetch so
            # the caller can fall back rather than caching an empty table.
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_standings_fallback()
            return {
                'data': fallback_data,
                'standings': fallback_data,
                'source': 'fallback',"""
assert old_driver in s, "driver-return anchor missing"
s = s.replace(old_driver, new_driver, 1)

p.write_text(s)
ast.parse(s)
print("jolpica_client: driver standings parser added, file parses OK")
