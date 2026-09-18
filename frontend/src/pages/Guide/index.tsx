import { useState } from 'react'
import { Link } from 'react-router-dom'

type GuideSection = 'getting-started' | 'predictions' | 'standings' | 'h2h' | 'fantasy' | 'models' | 'settings' | 'faq'

export function GuidePage() {
  const [activeSection, setActiveSection] = useState<GuideSection>('getting-started')

  const sections: Record<GuideSection, { title: string; icon: string; content: JSX.Element }> = {
    'getting-started': {
      title: 'Getting Started',
      icon: '🚀',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Welcome to F1 Predictor 2026</h2>
            <p className="fs-11 text-sub leading-relaxed">
              This is your ultimate Formula 1 prediction platform powered by Monte Carlo simulations and machine learning. 
              Whether you're a casual fan or a data enthusiast, this guide will help you navigate every feature.
            </p>
            
            <div className="mt-4 grid md:grid-cols-3 gap-3">
              <div className="surface-alt p-4 rounded-lg">
                <div className="text-2xl mb-2">🎯</div>
                <div className="fs-11 font-bold">Predict Race Outcomes</div>
                <div className="fs-11 text-sub mt-1">Get win/podium/points probabilities for any race</div>
              </div>
              <div className="surface-alt p-4 rounded-lg">
                <div className="text-2xl mb-2">📊</div>
                <div className="fs-11 font-bold">Track Standings</div>
                <div className="fs-11 text-sub mt-1">Live driver and constructor championship tables</div>
              </div>
              <div className="surface-alt p-4 rounded-lg">
                <div className="text-2xl mb-2">⚔️</div>
                <div className="fs-11 font-bold">Compare Drivers</div>
                <div className="fs-11 text-sub mt-1">Head-to-head performance analysis</div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="f1-display font-bold mb-3">How It Works — The Engine</h3>
            <ol className="space-y-3 fs-11 text-sub list-decimal list-inside">
              <li><strong className="text-current">Monte Carlo Simulations:</strong> We run 100-50,000 race simulations using vectorized NumPy operations (~80ms for 10k sims)</li>
              <li><strong className="text-current">Feature Engineering:</strong> Driver strength, team pace, weather, track characteristics, tyre degradation</li>
              <li><strong className="text-current">Probability Model:</strong> Ensemble predictions calibrated with isotonic regression on historical data</li>
              <li><strong className="text-current">Real-time Updates:</strong> Live data from Jolpica, OpenF1, FastF1 APIs with Redis caching</li>
            </ol>
            <div className="mt-4 p-3 rounded-lg bg-black text-white fs-11">
              <strong>Pro Tip:</strong> All predictions include confidence intervals and provenance tracking. Check the Reports section at the bottom of each prediction for full transparency.
            </div>
          </div>
        </div>
      )
    },

    'predictions': {
      title: 'Predictions Dashboard',
      icon: '🏁',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Making Predictions</h2>
            <p className="fs-11 text-sub mb-4">The Predictions page is the heart of the app. Here's how to use it effectively:</p>
            
            <div className="space-y-4">
              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-8 h-8 rounded-full flex items-center justify-center font-black text-white" style={{ background: 'var(--red)' }}>1</span>
                  <div className="fs-11 font-bold">Select Race & Session</div>
                </div>
                <div className="fs-11 text-sub ml-10">
                  Choose from 23 Grand Prix races. Then pick Friday (Practice), Saturday (Qualifying), or Sunday (Race). 
                  Each session has different dynamics — qualifying favors grid position, racing rewards strategy.
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-8 h-8 rounded-full flex items-center justify-center font-black text-white" style={{ background: 'var(--red)' }}>2</span>
                  <div className="fs-11 font-bold">Adjust Conditions (Optional)</div>
                </div>
                <div className="fs-11 text-sub ml-10 space-y-2">
                  <div><strong>Weather:</strong> Dry, Light Rain, Heavy Rain — affects reliability and overtaking</div>
                  <div><strong>Chaos Level:</strong> 0 (predictable) to 100 (anything can happen). Higher chaos = more upsets</div>
                  <div><strong>Grid Weight:</strong> How much starting position matters. 2026 cars have active aero reducing this</div>
                  <div><strong>Tyre Strategy:</strong> Soft/Medium/Hard compounds with different degradation curves</div>
                  <div><strong>Temperature:</strong> Track temp affects tyre wear and engine performance</div>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-8 h-8 rounded-full flex items-center justify-center font-black text-white" style={{ background: '#16a34a' }}>3</span>
                  <div className="fs-11 font-bold">Run Simulation</div>
                </div>
                <div className="fs-11 text-sub ml-10">
                  Click the green "Run Prediction" button. The engine executes Monte Carlo simulations and generates:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Win/Podium/Points probabilities for all 22 drivers</li>
                    <li>Predicted finishing order with confidence bands</li>
                    <li>16 interactive charts showing various metrics</li>
                    <li>Tire strategy visualization</li>
                    <li>Full report exportable as CSV/JSON/PDF</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(22,163,74,0.08)', border: '1px solid #16a34a' }}>
              <div className="fs-11 font-bold" style={{ color: '#16a34a' }}>💡 Expert Tip</div>
              <div className="fs-11 text-sub mt-1">
                Try different chaos levels to see how uncertainty affects predictions. Low chaos (20-30) shows the "expected" outcome. 
                High chaos (70-80) reveals potential upsets and dark horse candidates.
              </div>
            </div>
          </div>
        </div>
      )
    },

    'standings': {
      title: 'Championship Standings',
      icon: '🏆',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Tracking the Championship</h2>
            <p className="fs-11 text-sub mb-4">
              The Standings page shows real-time driver and constructor championship positions with points, wins, and podiums.
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="surface-alt p-4 rounded-lg">
                <div className="fs-11 font-bold mb-2">Driver Standings</div>
                <div className="fs-11 text-sub">
                  Shows all 22 drivers ranked by championship points. Includes:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Current position and points total</li>
                    <li>Wins and podium finishes</li>
                    <li>Points gap to leader</li>
                    <li>Team affiliation with color coding</li>
                  </ul>
                </div>
              </div>

              <div className="surface-alt p-4 rounded-lg">
                <div className="fs-11 font-bold mb-2">Constructor Standings</div>
                <div className="fs-11 text-sub">
                  Team championship table with:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Combined points from both drivers</li>
                    <li>Team wins and podiums</li>
                    <li>Form indicator (recent performance trend)</li>
                    <li>2026 newcomers highlighted (Audi, Cadillac)</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
              <div className="fs-11 font-bold mb-2">📈 Points Progression Chart</div>
              <div className="fs-11 text-sub">
                The top section shows how the top 3 drivers' points have accumulated through the season. 
                Use the round slider to see standings at different points in the championship.
              </div>
            </div>
          </div>
        </div>
      )
    },

    'h2h': {
      title: 'Head-to-Head Comparison',
      icon: '⚔️',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Driver vs Driver Analysis</h2>
            <p className="fs-11 text-sub mb-4">
              Compare any two drivers across multiple dimensions to see who really has the edge.
            </p>

            <div className="space-y-3">
              <div className="p-4 rounded-lg surface-alt">
                <div className="fs-11 font-bold mb-2">What You Can Compare</div>
                <ul className="fs-11 text-sub list-disc list-inside space-y-1">
                  <li><strong>Qualifying Performance:</strong> Average grid position, Q3 appearances, pole positions</li>
                  <li><strong>Race Results:</strong> Finishing positions, points scored, DNF rate</li>
                  <li><strong>Consistency:</strong> Standard deviation in results, recovery drives</li>
                  <li><strong>Team Battle:</strong> How they stack up against their teammate</li>
                  <li><strong>Track Records:</strong> Performance at specific circuits</li>
                </ul>
              </div>

              <div className="p-4 rounded-lg surface-alt">
                <div className="fs-11 font-bold mb-2">How to Use</div>
                <ol className="fs-11 text-sub list-decimal list-inside space-y-2">
                  <li>Select Driver A from the dropdown (e.g., Verstappen)</li>
                  <li>Select Driver B (e.g., Hamilton)</li>
                  <li>Choose comparison type: Overall, Qualifying, Race, or Specific Track</li>
                  <li>View side-by-side stats and visual comparisons</li>
                </ol>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-black text-white fs-11">
              <strong>Insight:</strong> Head-to-head reveals hidden strengths. A driver might qualify worse but race better, 
              or excel in wet conditions. Use this to find betting value or fantasy picks.
            </div>
          </div>
        </div>
      )
    },

    'fantasy': {
      title: 'Fantasy League',
      icon: '🎮',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Build Your Fantasy Team</h2>
            <p className="fs-11 text-sub mb-4">
              Create the ultimate F1 fantasy team within a $100M budget. Pick 5 drivers and 2 constructors, then earn points based on real race results.
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="fs-11 font-bold mb-2">👥 Select 5 Drivers</div>
                <div className="fs-11 text-sub">
                  Each driver has a price based on their expected performance. Mix expensive stars with value picks:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>Stars ($18-25M):</strong> Verstappen, Norris, Leclerc — high points but expensive</li>
                    <li><strong>Mids ($12-17M):</strong> Piastri, Russell, Sainz — good balance</li>
                    <li><strong>Value ($8-11M):</strong> Rookie drivers, backmarkers — low cost, differential potential</li>
                  </ul>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="fs-11 font-bold mb-2">🏭 Select 2 Constructors</div>
                <div className="fs-11 text-sub">
                  Teams score points from both drivers. Top teams (Red Bull, McLaren) cost more but deliver consistent points.
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 rounded-lg surface-alt">
              <div className="fs-11 font-bold mb-2">Special Features</div>
              <ul className="fs-11 text-sub list-disc list-inside space-y-2">
                <li><strong>2× Boost:</strong> Double one driver's points each race — choose wisely!</li>
                <li><strong>Extra DRS Chip:</strong> Activate once per season for bonus points</li>
                <li><strong>Optimal Team Solver:</strong> Backend algorithm suggests best team based on predictions</li>
                <li><strong>PPM Calculator:</strong> Points Per Million shows value for money</li>
              </ul>
            </div>

            <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(22,163,74,0.08)', border: '1px solid #16a34a' }}>
              <div className="fs-11 font-bold" style={{ color: '#16a34a' }}>🎯 Strategy Tip</div>
              <div className="fs-11 text-sub mt-1">
                Don't just pick the most expensive drivers! Use the PPM (Points Per Million) metric to find undervalued picks. 
                A $10M driver scoring 15 pts (1.5 PPM) beats a $20M driver scoring 25 pts (1.25 PPM).
              </div>
            </div>
          </div>
        </div>
      )
    },

    'models': {
      title: 'Prediction Models',
      icon: '🤖',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Understanding Our Models</h2>
            <p className="fs-11 text-sub mb-4">
              F1 Predictor 2026 uses two main approaches. You can switch between them in Settings → Models.
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-5 rounded-lg border-2" style={{ borderColor: '#0ea5e9', background: 'rgba(14,165,233,0.05)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">⚙️</span>
                  <div className="fs-11 font-black">Machine Learning (ML)</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>What it is:</strong> Traditional statistical models using engineered features</p>
                  <p><strong>Techniques:</strong></p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Elo ratings for driver strength</li>
                    <li>GridModel for qualifying predictions</li>
                    <li>Linear regression for lap times</li>
                    <li>Logistic regression for DNF probability</li>
                  </ul>
                  <p><strong>Best for:</strong> Fast predictions, interpretable results, lower computational cost</p>
                  <p><strong>Speed:</strong> ~50-100ms per prediction</p>
                </div>
              </div>

              <div className="p-5 rounded-lg border-2" style={{ borderColor: '#8b5cf6', background: 'rgba(139,92,246,0.05)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🧠</span>
                  <div className="fs-11 font-black">Deep Learning (DL)</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>What it is:</strong> Neural networks that learn complex patterns from raw data</p>
                  <p><strong>Techniques:</strong></p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>LSTM networks for time series (lap progression)</li>
                    <li>Gradient boosting (XGBoost) for feature importance</li>
                    <li>Ensemble methods combining multiple models</li>
                    <li>Attention mechanisms for driver interactions</li>
                  </ul>
                  <p><strong>Best for:</strong> Capturing non-linear relationships, higher accuracy potential</p>
                  <p><strong>Speed:</strong> ~200-500ms per prediction</p>
                </div>
              </div>
            </div>

            <div className="mt-4 p-4 rounded-lg surface-alt">
              <div className="fs-11 font-bold mb-2">📊 Model Comparison</div>
              <div className="overflow-x-auto">
                <table className="f1-table w-full fs-11">
                  <thead>
                    <tr>
                      <th>Aspect</th>
                      <th>ML Models</th>
                      <th>DL Models</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="font-bold">Accuracy</td>
                      <td>Good (baseline + 15-25%)</td>
                      <td>Better (baseline + 20-35%)</td>
                    </tr>
                    <tr>
                      <td className="font-bold">Speed</td>
                      <td>Fast ⚡</td>
                      <td>Moderate 🐢</td>
                    </tr>
                    <tr>
                      <td className="font-bold">Interpretability</td>
                      <td>High ✅</td>
                      <td>Medium ⚠️</td>
                    </tr>
                    <tr>
                      <td className="font-bold">Data Needs</td>
                      <td>Less (100s of races)</td>
                      <td>More (1000s of races)</td>
                    </tr>
                    <tr>
                      <td className="font-bold">Maintenance</td>
                      <td>Easy</td>
                      <td>Complex</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-black text-white fs-11">
              <strong>Recommendation:</strong> Start with ML models for speed and clarity. Switch to DL if you want maximum accuracy 
              and don't mind slightly slower predictions. Both are calibrated and validated on historical data.
            </div>
          </div>
        </div>
      )
    },

    'settings': {
      title: 'Engine Control Center',
      icon: '⚙️',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Tuning the Prediction Engine</h2>
            <p className="fs-11 text-sub mb-4">
              The Settings page is your complete control center for the prediction engine. Adjust every parameter that influences race outcomes.
            </p>

            <div className="space-y-4">
              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🎨</span>
                  <div className="fs-11 font-bold">Appearance</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>Theme Colors:</strong> Customize primary color, background, surfaces, text colors</p>
                  <p><strong>Live Preview:</strong> See changes instantly as you adjust colors</p>
                  <p><strong>Presets:</strong> Quick-switch between Dark, Light, Performance themes</p>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🎲</span>
                  <div className="fs-11 font-bold">Monte Carlo Engine</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>Simulations:</strong> 100 to 50,000 race scenarios (vectorized NumPy ~80ms per 10k)</p>
                  <p><strong>Chaos Level:</strong> Race unpredictability 0-100. Higher = more upsets and surprises</p>
                  <p><strong>Grid Weight:</strong> Starting position importance. Lower = closer 2026 racing with active aero</p>
                  <p><strong>Weather Impact:</strong> Rain effect on DNF rates and overtaking probability</p>
                  <p><strong>Reliability:</strong> Mechanical failure risk factor based on historical data</p>
                  <p><strong>Strategy Aggressiveness:</strong> Pit stop strategy boldness affecting tire choices</p>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">⚙️</span>
                  <div className="fs-11 font-bold">Feature Engineering Weights</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>Driver Strength:</strong> Elo-based rating from historical performance (70 default)</p>
                  <p><strong>Team Pace:</strong> Constructor competitiveness and car development level (65 default)</p>
                  <p><strong>Track Characteristics:</strong> Circuit layout influence — power vs technical tracks (55 default)</p>
                  <p><strong>Weather Impact:</strong> Temperature, rain, wind effects on lap times (60 default)</p>
                  <p><strong>Tyre Degradation:</strong> Compound wear and pit strategy optimization (50 default)</p>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">📊</span>
                  <div className="fs-11 font-bold">Elo Rating System</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>K-Factor:</strong> How quickly driver ratings change after races (32 default). Higher = faster adaptation to form</p>
                  <p><strong>Initial Rating:</strong> Starting Elo for rookies and new drivers (1500 default)</p>
                  <p><strong>Home Advantage:</strong> Bonus points for racing at home circuits like Hamilton at Silverstone (+25 default)</p>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🎯</span>
                  <div className="fs-11 font-bold">Probability Model</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>Ensemble Weights:</strong> Balance between ML (45%) and Monte Carlo (55%) predictions</p>
                  <p><strong>Calibration Method:</strong> Isotonic regression, Platt scaling, or raw probabilities</p>
                  <p><strong>Confidence Intervals:</strong> Prediction uncertainty range (95% default)</p>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">💾</span>
                  <div className="fs-11 font-bold">Data Sources & Caching</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>Primary Source:</strong> Jolpica (official timing), OpenF1 (live telemetry), FastF1 (historical), or local cache</p>
                  <p><strong>Cache TTL:</strong> API response lifetime in seconds (300s = 5 minutes default)</p>
                  <p><strong>Update Interval:</strong> Background data refresh during live sessions (300s default)</p>
                </div>
              </div>

              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🤖</span>
                  <div className="fs-11 font-bold">Model Selection</div>
                </div>
                <div className="fs-11 text-sub space-y-2">
                  <p><strong>ML (Machine Learning):</strong> Fast predictions (~50ms) using gradient boosting on engineered features</p>
                  <p><strong>DL (Deep Learning):</strong> Accurate predictions (~200ms) using neural networks on raw data</p>
                  <p><strong>Ensemble:</strong> Balanced approach combining both methods (~120ms)</p>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 rounded-lg bg-black text-white">
              <div className="fs-11 font-bold mb-2">🚀 Quick Presets</div>
              <div className="fs-11 grid md:grid-cols-2 gap-3">
                <div><strong>Conservative:</strong> Low chaos, high grid weight, reliable — predictable outcomes</div>
                <div><strong>Aggressive:</strong> High chaos, low grid weight, risky — upset potential</div>
                <div><strong>Qualifying Mode:</strong> Optimized for Saturday sessions with higher grid importance</div>
                <div><strong>Race Mode:</strong> Balanced settings for Sunday Grand Prix predictions</div>
                <div><strong>High Accuracy:</strong> 50k simulations, full calibration — slowest but most precise</div>
                <div><strong>Fast Predictions:</strong> 1k sims, minimal calibration — quick results for testing</div>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(22,163,74,0.08)', border: '1px solid #16a34a' }}>
              <div className="fs-11 font-bold" style={{ color: '#16a34a' }}>💡 Pro Tip</div>
              <div className="fs-11 text-sub mt-1">
                Start with presets, then fine-tune individual parameters. Save your custom configurations for different track types 
                (street circuits vs permanent tracks) or weather conditions. All settings persist across sessions.
              </div>
            </div>
          </div>
        </div>
      )
    },

    'faq': {
      title: 'FAQ & Troubleshooting',
      icon: '❓',
      content: (
        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="f1-display text-xl font-black mb-3">Frequently Asked Questions</h2>
            
            <div className="space-y-4">
              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">How accurate are the predictions?</summary>
                <div className="fs-11 text-sub mt-2">
                  Our models beat random baselines by 15-35% depending on the target:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Winner prediction: ~58% accuracy (vs 4.5% random)</li>
                    <li>Podium prediction: ~72% accuracy (vs 13.6% random)</li>
                    <li>Points finish: ~85% accuracy (vs 45.5% random)</li>
                  </ul>
                  Accuracy varies by session type — qualifying is easier than race outcomes.
                </div>
              </details>

              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">Why do predictions change between runs?</summary>
                <div className="fs-11 text-sub mt-2">
                  Monte Carlo simulations use randomness (seeded for reproducibility). With 10,000+ sims, 
                  results converge but may vary slightly. For identical results, use the same seed in Settings.
                </div>
              </details>

              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">Can I use this for betting?</summary>
                <div className="fs-11 text-sub mt-2">
                  <strong>No.</strong> This tool is for entertainment and educational purposes only. 
                  While our models are sophisticated, F1 is inherently unpredictable. Never bet money you can't afford to lose.
                </div>
              </details>

              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">Where does the data come from?</summary>
                <div className="fs-11 text-sub mt-2">
                  Multiple sources with fallback:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>Jolpica:</strong> Official F1 timing data, results, standings</li>
                    <li><strong>OpenF1:</strong> Live session data, telemetry</li>
                    <li><strong>FastF1:</strong> Historical data, tire strategies</li>
                    <li><strong>Local cache:</strong> 2026 calendar, driver lineups, circuit info</li>
                  </ul>
                  All data includes provenance tracking — check Reports for sources.
                </div>
              </details>

              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">Why is the app slow sometimes?</summary>
                <div className="fs-11 text-sub mt-2">
                  Common causes:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>High simulation count (50k sims takes ~1.2s)</li>
                    <li>First load after server restart (cache warming)</li>
                    <li>Network issues with live data APIs</li>
                    <li>Browser extensions interfering</li>
                  </ul>
                  Fix: Reduce sims to 10k in Settings, hard refresh (Ctrl+Shift+R), disable extensions.
                </div>
              </details>

              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">How do I export my predictions?</summary>
                <div className="fs-11 text-sub mt-2">
                  After running a prediction, scroll to the Reports section at the bottom. Click:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>CSV:</strong> Download tabular data for Excel/Sheets</li>
                    <li><strong>JSON:</strong> Full prediction object with metadata</li>
                    <li><strong>PDF:</strong> Formatted report with charts</li>
                    <li><strong>Share:</strong> Generate shareable image card</li>
                  </ul>
                </div>
              </details>

              <details className="p-4 rounded-lg surface-alt cursor-pointer">
                <summary className="fs-11 font-bold">What's new in 2026?</summary>
                <div className="fs-11 text-sub mt-2">
                  Major regulation changes:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Active aerodynamics (front/rear wing adjustments)</li>
                    <li>Sustainable fuels (100% drop-in replacement)</li>
                    <li>Reduced downforce (-30%) and drag (-55%)</li>
                    <li>New teams: Audi returns, Cadillac enters</li>
                    <li>Lighter cars (768kg) with shorter wheelbase</li>
                  </ul>
                  Our models are specifically tuned for these 2026 regulations.
                </div>
              </details>
            </div>

            <div className="mt-6 p-4 rounded-lg bg-black text-white">
              <div className="fs-11 font-bold mb-2">Still Have Questions?</div>
              <div className="fs-11">
                Check the technical documentation:
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li><code className="f1-mono">docs/ARCHITECTURE.md</code> — System design</li>
                  <li><code className="f1-mono">docs/ML_VALIDATION.md</code> — Model accuracy reports</li>
                  <li><code className="f1-mono">README.md</code> — Setup and deployment</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )
    }
  }

  return (
    <div className="px-4 sm:px-8 py-6 max-w-6xl mx-auto space-y-6">
      {/* Hero Section */}
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/f1_simulation.webp" alt="F1 Simulation" loading="lazy" className="w-full h-56 object-cover" />
          <div className="p-6 flex flex-col justify-center">
            <h1 className="f1-display text-2xl font-black">User Guide</h1>
            <p className="fs-11 text-sub mt-2">
              Everything you need to know about F1 Predictor 2026. From making your first prediction to advanced model tuning.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="badge badge-neutral">Monte Carlo Powered</span>
              <span className="badge badge-neutral">22 Drivers</span>
              <span className="badge badge-neutral">23 Races</span>
              <span className="badge badge-neutral">Real-time Data</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="card p-3">
        <div className="flex flex-wrap gap-2">
          {(Object.keys(sections) as GuideSection[]).map((sectionId) => (
            <button
              key={sectionId}
              onClick={() => setActiveSection(sectionId)}
              className={`btn-ghost !py-2 !px-4 fs-11 ${activeSection === sectionId ? 'is-active' : ''}`}
              style={activeSection === sectionId ? { background: 'var(--red-tint)', borderColor: 'var(--red)', color: 'var(--red)' } : {}}
            >
              <span className="mr-1">{sections[sectionId].icon}</span>
              {sections[sectionId].title}
            </button>
          ))}
        </div>
      </div>

      {/* Active Section Content */}
      <div className="animate-fadeIn">
        {sections[activeSection].content}
      </div>

      {/* Quick Links Footer */}
      <div className="card p-4">
        <div className="fs-11 font-bold mb-2">Quick Links</div>
        <div className="flex flex-wrap gap-2 fs-11">
          <Link to="/dashboard" className="btn-ghost !py-1.5 !px-3">→ Go to Predictions</Link>
          <Link to="/standings" className="btn-ghost !py-1.5 !px-3">→ View Standings</Link>
          <Link to="/h2h" className="btn-ghost !py-1.5 !px-3">→ Compare Drivers</Link>
          <Link to="/fantasy" className="btn-ghost !py-1.5 !px-3">→ Build Fantasy Team</Link>
          <Link to="/settings" className="btn-ghost !py-1.5 !px-3">→ Open Settings</Link>
        </div>
      </div>
    </div>
  )
}
