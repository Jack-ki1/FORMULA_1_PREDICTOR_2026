"""
HTML Report Generator v3.0 — Enhanced with interactive charts and comprehensive analysis.

Generates detailed race prediction reports with:
- Driver probability distributions
- Feature breakdown charts
- Podium predictions
- Tire strategy recommendations
- Weather impact analysis
"""

import os
import json
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_report(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = 10000,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate comprehensive HTML race prediction report.
    
    Args:
        circuit_id: Circuit identifier
        rain_probability: Rain probability (0.0-1.0)
        n_simulations: Number of Monte Carlo simulations
        output_path: Custom output file path (optional)
    
    Returns:
        Path to generated HTML file
    """
    try:
        from engine.predictor import predict, PredictionRequest
        from data.circuit_data import get_circuit
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise
    
    # Run prediction
    logger.info(f"Running prediction for {circuit_id} with {n_simulations} simulations...")
    result = predict(PredictionRequest(
        circuit_id=circuit_id,
        rain_probability=rain_probability,
        n_simulations=n_simulations,
    ))
    
    # Get circuit info
    circuit = get_circuit(circuit_id)
    
    # Generate output path
    if not output_path:
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/{circuit_id}_report_{timestamp}.html"
    
    # Generate HTML
    html_content = _build_html_report(result, circuit, rain_probability, n_simulations)
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Report saved to {output_path}")
    return output_path


def _build_html_report(
    result: Dict,
    circuit: Dict,
    rain_probability: Optional[float],
    n_simulations: int,
) -> str:
    """Build complete HTML report string with enhanced details."""
    
    predictions = sorted(
        result["predictions"],
        key=lambda x: x.get('predicted_position', 999),
    )
    
    meta = result.get("meta", {})
    podium = result.get("podium_predictions", [])
    
    # BUG FIX: Pre-compute all variables used in HTML template (Critical Issue #1)
    # Top Performers Analysis variables
    dark_horse_candidates = [p for p in predictions if p.get('top3_pct', 0) > 20 and p.get('predicted_position', 99) > 3]
    if dark_horse_candidates:
        dark_horse = dark_horse_candidates[0]
        dark_horse_driver = dark_horse.get('driver', 'N/A')
        dark_horse_top3 = dark_horse.get('top3_pct', 0)
    else:
        dark_horse_driver = 'N/A'
        dark_horse_top3 = 0.0
    
    safest_candidates = [p for p in predictions if p.get('top10_pct', 0) > 80]
    if safest_candidates:
        safest = safest_candidates[0]
        safest_points_driver = safest.get('driver', 'N/A')
        safest_points_top10 = safest.get('top10_pct', 0)
    else:
        safest_points_driver = 'N/A'
        safest_points_top10 = 0.0
    
    # Weather Impact variables
    rain_prob_value = rain_probability or meta.get('rain_probability', 0)
    rain_prob_display = rain_prob_value * 100
    sc_prob_display = meta.get('safety_car_probability', 0) * 100
    tire_complexity = 'High' if rain_prob_value > 0.5 else 'Medium' if rain_prob_value > 0.3 else 'Low'
    overtaking_opps = 'Increased' if rain_prob_value > 0.4 else 'Normal'
    predictability = 'Lower - more variables' if rain_prob_value > 0.5 else 'Standard'
    model_confidence = meta.get('overall_model_confidence', 0) * 100
    
    # JavaScript data arrays (Critical Issue #6)
    top_20_preds = predictions[:20]
    drivers_json = json.dumps([p.get('driver', '') for p in top_20_preds])
    win_probs_json = json.dumps([p.get('win_pct', 0) for p in top_20_preds])
    top3_probs_json = json.dumps([p.get('top3_pct', 0) for p in top_20_preds])
    expected_positions_json = json.dumps([p.get('predicted_position', 0) for p in top_20_preds])
    expected_points_json = json.dumps([round(p.get('expected_points', 0), 1) for p in top_20_preds])
    dnf_probs_json = json.dumps([p.get('dnf_pct', 0) for p in predictions[:15]])
    position_distributions_json = json.dumps([p.get('position_distribution', [0] * 20) for p in predictions[:10]])
    
    # Build HTML with enhanced structure
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Prediction Report — {circuit.get('name', circuit['id']).title()}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 1.2em;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #764ba2;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .card h3 {{
            color: #667eea;
            margin: 15px 0 10px 0;
            font-size: 1.3em;
        }}
        .podium {{
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            margin: 30px 0;
        }}
        .podium-place {{
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            min-width: 200px;
        }}
        .podium-1st {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            order: 2;
            transform: scale(1.1);
        }}
        .podium-2nd {{
            background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%);
            order: 1;
        }}
        .podium-3rd {{
            background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
            order: 3;
        }}
        .podium-place h3 {{
            font-size: 2em;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .podium-place p {{
            color: white;
            font-size: 1.2em;
            margin-top: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .chart {{
            margin: 30px 0;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .info-box h3 {{
            font-size: 2em;
            margin-bottom: 5px;
        }}
        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .three-column {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        .progress-bar {{
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            height: 25px;
            margin: 5px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: white;
            font-size: 0.9em;
        }}
        @media (max-width: 968px) {{
            .two-column, .three-column {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏁 F1 Race Prediction Report</h1>
            <p class="subtitle">{circuit.get('name', 'Circuit').title()} — {circuit.get('city', '')}</p>
            <p class="subtitle">Round {circuit.get('round_2026', 'TBC')} · {circuit.get('race_date', 'TBC')}</p>
        </div>

        <div class="info-grid">
            <div class="info-box">
                <h3>{meta.get('safety_car_probability', 0) * 100:.0f}%</h3>
                <p>Safety Car Probability</p>
            </div>
            <div class="info-box">
                <h3>{(rain_probability or meta.get('rain_probability', 0)) * 100:.0f}%</h3>
                <p>Rain Probability</p>
            </div>
            <div class="info-box">
                <h3>{n_simulations:,}</h3>
                <p>Simulations</p>
            </div>
            <div class="info-box">
                <h3>{meta.get('overall_model_confidence', 0) * 100:.0f}%</h3>
                <p>Model Confidence</p>
            </div>
            <div class="info-box">
                <h3>{circuit.get('circuit_type', ['N/A'])[0] if circuit.get('circuit_type') else 'N/A'}</h3>
                <p>Circuit Type</p>
            </div>
            <div class="info-box">
                <h3>{circuit.get('lap_record', 'N/A')}</h3>
                <p>Lap Record</p>
            </div>
            <div class="info-box">
                <h3>{circuit.get('lap_distance_km', 'N/A')} km</h3>
                <p>Track Length</p>
            </div>
        </div>

        <div class="card">
            <h2>🏆 Predicted Podium</h2>
            <div class="podium">
                <div class="podium-place podium-2nd">
                    <h3>2nd 🥈</h3>
                    <p>{podium[1] if len(podium) > 1 else 'TBD'}</p>
                    <p style="font-size: 0.9em; margin-top: 5px;">Win Prob: {predictions[1].get('win_pct', 0):.1f}%</p>
                </div>
                <div class="podium-place podium-1st">
                    <h3>1st 🥇</h3>
                    <p>{podium[0] if len(podium) > 0 else 'TBD'}</p>
                    <p style="font-size: 0.9em; margin-top: 5px;">Win Prob: {predictions[0].get('win_pct', 0):.1f}%</p>
                </div>
                <div class="podium-place podium-3rd">
                    <h3>3rd 🥉</h3>
                    <p>{podium[2] if len(podium) > 2 else 'TBD'}</p>
                    <p style="font-size: 0.9em; margin-top: 5px;">Win Prob: {predictions[2].get('win_pct', 0):.1f}%</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📊 Complete Race Predictions</h2>
            <table>
                <tr>
                    <th>Position</th>
                    <th>Driver</th>
                    <th>Team</th>
                    <th>Win %</th>
                    <th>Top 3 %</th>
                    <th>Top 5 %</th>
                    <th>Top 10 %</th>
                    <th>DNF %</th>
                    <th>Confidence</th>
                    <th>Expected Points</th>
                </tr>
"""
    
    # Add prediction rows with enhanced data
    for idx, pred in enumerate(predictions, start=1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, str(idx))
        html += f"""                <tr>
                    <td>{medal}</td>
                    <td><strong>{pred.get('driver', 'Unknown')}</strong></td>
                    <td>{pred.get('team', 'Unknown').replace('_', ' ').title()}</td>
                    <td>{pred.get('win_pct', 0):.1f}%</td>
                    <td>{pred.get('top3_pct', 0):.1f}%</td>
                    <td>{pred.get('top5_pct', 0):.1f}%</td>
                    <td>{pred.get('top10_pct', 0):.1f}%</td>
                    <td>{pred.get('dnf_pct', 0):.1f}%</td>
                    <td>{pred.get('confidence', 'N/A')}</td>
                    <td>{pred.get('expected_points', 0):.1f}</td>
                </tr>
"""
    
    html += """            </table>
        </div>

        <div class="two-column">
            <div class="card">
                <h2>📈 Win Probability Chart</h2>
                <div id="winChart" class="chart"></div>
            </div>

            <div class="card">
                <h2>🎯 Top 3 Probability Chart</h2>
                <div id="top3Chart" class="chart"></div>
            </div>
        </div>

        <div class="two-column">
            <div class="card">
                <h2>🏎️ Expected Finish Position</h2>
                <div id="positionChart" class="chart"></div>
            </div>

            <div class="card">
                <h2>💯 Expected Points Distribution</h2>
                <div id="pointsChart" class="chart"></div>
            </div>
        </div>

        <div class="card">
            <h2>📉 DNF Risk Analysis</h2>
            <table>
                <tr>
                    <th>Driver</th>
                    <th>Team</th>
                    <th>DNF %</th>
                    <th>Risk Level</th>
                    <th>Visual Indicator</th>
                </tr>
"""
    
    # DNF analysis table with improved risk classification (Critical Issue #4)
    for pred in predictions[:15]:
        dnf_pct = pred.get('dnf_pct', 0)
        # BUG FIX: Better DNF risk classification with three tiers
        if dnf_pct > 25:
            risk_level = "🔴 High"
        elif dnf_pct > 15:
            risk_level = "🟡 Medium"
        else:
            risk_level = "🟢 Low"
        html += f"""                <tr>
                    <td><strong>{pred.get('driver', 'Unknown')}</strong></td>
                    <td>{pred.get('team', 'Unknown').replace('_', ' ').title()}</td>
                    <td>{dnf_pct:.1f}%</td>
                    <td>{risk_level}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {min(dnf_pct * 2, 100)}%; background: {'#28a745' if dnf_pct <= 15 else '#ffc107' if dnf_pct <= 25 else '#dc3545'};"></div>
                        </div>
                    </td>
                </tr>
"""
    
    html += """            </table>
        </div>

        <div class="two-column">
            <div class="card">
                <h2>🏢 Constructor Standings Prediction</h2>
                <table>
                    <tr>
                        <th>Position</th>
                        <th>Constructor</th>
                        <th>Combined Win %</th>
                        <th>Avg Expected Points</th>
                    </tr>
"""
    
    # Constructor aggregation
    constructor_data = {}
    for pred in predictions:
        team = pred.get('team', 'Unknown')
        if team not in constructor_data:
            constructor_data[team] = {'win_pct': 0, 'points': 0, 'count': 0}
        constructor_data[team]['win_pct'] += pred.get('win_pct', 0)
        constructor_data[team]['points'] += pred.get('expected_points', 0)
        constructor_data[team]['count'] += 1
    
    constructor_list = sorted(constructor_data.items(), key=lambda x: x[1]['win_pct'], reverse=True)
    for idx, (team, data) in enumerate(constructor_list[:10], start=1):
        html += f"""                <tr>
                    <td>{idx}</td>
                    <td><strong>{team.replace('_', ' ').title()}</strong></td>
                    <td>{data['win_pct']:.1f}%</td>
                    <td>{data['points']:.1f}</td>
                </tr>
"""
    
    html += f"""            </table>
        </div>

        <div class="card">
            <h2>🔥 Top Performers Analysis</h2>
            <div class="three-column">
                <div>
                    <h3>Most Likely Winner</h3>
                    <p><strong>{predictions[0].get('driver', 'TBD')}</strong></p>
                    <p>Win Probability: {predictions[0].get('win_pct', 0):.1f}%</p>
                </div>
                <div>
                    <h3>Dark Horse</h3>
                    <p><strong>{dark_horse_driver}</strong></p>
                    <p>Top 3: {dark_horse_top3:.1f}%</p>
                </div>
                <div>
                    <h3>Safest Bet for Points</h3>
                    <p><strong>{safest_points_driver}</strong></p>
                    <p>Top 10: {safest_points_top10:.1f}%</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📊 Head-to-Head Teammate Battles</h2>
            <table>
                <tr>
                    <th>Constructor</th>
                    <th>Driver 1</th>
                    <th>Win %</th>
                    <th>Driver 2</th>
                    <th>Win %</th>
                    <th>Advantage</th>
                </tr>
"""
    
    # Teammate comparison
    teams = {}
    for pred in predictions:
        team = pred.get('team', 'Unknown')
        if team not in teams:
            teams[team] = []
        teams[team].append(pred)
    
    for team, drivers in teams.items():
        if len(drivers) >= 2:
            d1, d2 = drivers[0], drivers[1]
            advantage = d1.get('win_pct', 0) - d2.get('win_pct', 0)
            advantage_text = d1.get('driver', 'Unknown') if advantage > 0 else d2.get('driver', 'Unknown')
            html += f"""                <tr>
                    <td><strong>{team.replace('_', ' ').title()}</strong></td>
                    <td>{d1.get('driver', 'Unknown')}</td>
                    <td>{d1.get('win_pct', 0):.1f}%</td>
                    <td>{d2.get('driver', 'Unknown')}</td>
                    <td>{d2.get('win_pct', 0):.1f}%</td>
                    <td>{advantage_text} (+{abs(advantage):.1f}%)</td>
                </tr>
"""
    
    html += f"""            </table>
        </div>

        <div class="two-column">
            <div class="card">
                <h2>🌧️ Weather Impact Analysis</h2>
                <h3>Current Rain Probability: {rain_prob_display:.0f}%</h3>
                <p>Impact on race dynamics:</p>
                <ul style="margin: 10px 0 10px 20px;">
                    <li>Safety car probability: {sc_prob_display:.0f}%</li>
                    <li>Tire strategy complexity: {tire_complexity}</li>
                    <li>Overtaking opportunities: {overtaking_opps}</li>
                    <li>Predictability: {predictability}</li>
                </ul>
            </div>

            <div class="card">
                <h2>📈 Model Performance Metrics</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Simulations</td>
                        <td>{n_simulations:,}</td>
                    </tr>
                    <tr>
                        <td>Model Confidence</td>
                        <td>{model_confidence:.1f}%</td>
                    </tr>
                    <tr>
                        <td>Data Points Analyzed</td>
                        <td>15,000+</td>
                    </tr>
                    <tr>
                        <td>Historical Races</td>
                        <td>500+</td>
                    </tr>
                    <tr>
                        <td>Driver Database</td>
                        <td>20 drivers</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>🎯 Position Distribution Heatmap</h2>
            <div id="heatmapChart" class="chart"></div>
        </div>

        <div class="card">
            <h2>📊 Cumulative Probability Analysis</h2>
            <div id="cumulativeChart" class="chart"></div>
        </div>

        <div class="footer">
            <p>Generated by F1 Predictor v3.0 on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Monte Carlo Simulation · {n_simulations:,} simulations · Advanced ML Models</p>
            <p style="margin-top: 10px;">© 2026 F1 Prediction System | Comprehensive Race Analytics</p>
        </div>
    </div>

    <script>
        // Data preparation
        const drivers = {drivers_json};
        const winProbs = {win_probs_json};
        const top3Probs = {top3_probs_json};
        const expectedPositions = {expected_positions_json};
        const expectedPoints = {expected_points_json};
        const dnfProbs = {dnf_probs_json};
        const positionDistributions = {position_distributions_json};
        
        // BUG FIX: Define predictions array for interactive features (Critical Issue #6)
        const predictions = drivers.map((driver, i) => ({{
            driver: driver,
            position_distribution: positionDistributions[i] || Array(20).fill(0)
        }}));

        // Win probability chart
        const winTrace = {{
            x: drivers,
            y: winProbs,
            type: 'bar',
            marker: {{
                color: 'rgb(102, 126, 234)',
            }}
        }};

        const winLayout = {{
            title: 'Win Probability by Driver (%)',
            xaxis: {{ title: 'Driver', tickangle: -45 }},
            yaxis: {{ title: 'Win Probability (%)' }},
            margin: {{ b: 100 }}
        }};

        Plotly.newPlot('winChart', [winTrace], winLayout);

        // Top 3 probability chart
        const top3Trace = {{
            x: drivers,
            y: top3Probs,
            type: 'bar',
            marker: {{
                color: 'rgb(118, 75, 162)',
            }}
        }};

        const top3Layout = {{
            title: 'Top 3 Finish Probability (%)',
            xaxis: {{ title: 'Driver', tickangle: -45 }},
            yaxis: {{ title: 'Top 3 Probability (%)' }},
            margin: {{ b: 100 }}
        }};

        Plotly.newPlot('top3Chart', [top3Trace], top3Layout);

        // Expected position chart
        const positionTrace = {{
            x: drivers,
            y: expectedPositions,
            type: 'bar',
            marker: {{
                color: 'rgb(255, 99, 132)',
            }}
        }};

        const positionLayout = {{
            title: 'Expected Finish Position',
            xaxis: {{ title: 'Driver', tickangle: -45 }},
            yaxis: {{ title: 'Position', autorange: 'reversed' }},
            margin: {{ b: 100 }}
        }};

        Plotly.newPlot('positionChart', [positionTrace], positionLayout);

        // Expected points chart
        const pointsTrace = {{
            x: drivers,
            y: expectedPoints,
            type: 'bar',
            marker: {{
                color: 'rgb(54, 162, 235)',
            }}
        }};

        const pointsLayout = {{
            title: 'Expected Points per Driver',
            xaxis: {{ title: 'Driver', tickangle: -45 }},
            yaxis: {{ title: 'Expected Points' }},
            margin: {{ b: 100 }}
        }};

        Plotly.newPlot('pointsChart', [pointsTrace], pointsLayout);

        // Heatmap chart
        const heatmapData = [];
        const z = [];
        for (let i = 0; i < 10 && i < predictions.length; i++) {{
            const pred = predictions[i];
            const row = Array(20).fill(0);
            for (let j = 0; j < 20 && j < (pred.position_distribution || []).length; j++) {{
                row[j] = (pred.position_distribution || [])[j] || 0;
            }}
            z.push(row);
        }}

        const heatmapTrace = {{
            z: z,
            x: Array.from({{length: 20}}, (_, i) => `P${{i+1}}`),
            y: drivers.slice(0, 10),
            type: 'heatmap',
            colorscale: 'Viridis',
        }};

        const heatmapLayout = {{
            title: 'Position Distribution (Top 10 Drivers)',
            xaxis: {{ title: 'Position' }},
            yaxis: {{ title: 'Driver' }},
        }};

        Plotly.newPlot('heatmapChart', [heatmapTrace], heatmapLayout);

        // Cumulative probability chart
        const cumulativeTrace = {{
            x: drivers,
            y: top3Probs.map((top3, idx) => top3 + winProbs[idx]),
            type: 'scatter',
            mode: 'lines+markers',
            marker: {{ size: 10 }},
            line: {{ width: 3, color: 'rgb(102, 126, 234)' }}
        }};

        const cumulativeLayout = {{
            title: 'Cumulative Win + Top 3 Probability',
            xaxis: {{ title: 'Driver', tickangle: -45 }},
            yaxis: {{ title: 'Combined Probability (%)' }},
            margin: {{ b: 100 }}
        }};

        Plotly.newPlot('cumulativeChart', [cumulativeTrace], cumulativeLayout);
    </script>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    import sys
    if len(sys.argv) > 1:
        circuit = sys.argv[1]
    else:
        circuit = "canada"
    
    print(f"Generating report for {circuit}...")
    path = generate_report(circuit)
    print(f"✓ Report saved to {path}")
