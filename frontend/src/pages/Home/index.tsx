import { Link } from 'react-router-dom'
export function HomePage(){
  return (
    <div className="px-4 sm:px-8 py-8">
      <div className="navy-panel p-8 rounded-xl text-white">
        <h1 className="f1-display text-3xl font-black">F1 Predictor 2026</h1>
        <p className="mt-2 text-sm" style={{color:'rgba(255,255,255,.8)'}}>AI-powered Formula 1 predictions — race, qualifying and practice forecasts built on a real prediction engine.</p>
        <Link to="/dashboard" className="btn-primary inline-block mt-4">Open Dashboard</Link>
      </div>
      <div className="grid sm:grid-cols-3 gap-4 mt-6">
        <Link to="/standings" className="card p-4 hover:shadow-lg transition">Driver & Constructor Standings</Link>
        <Link to="/h2h" className="card p-4 hover:shadow-lg transition">Head-to-Head Comparison</Link>
        <Link to="/constructors" className="card p-4 hover:shadow-lg transition">Constructor Analysis</Link>
      </div>
    </div>
  )
}
