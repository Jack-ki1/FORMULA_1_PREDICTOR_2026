"""
Main Entry Point for F1 Prediction System.

This module initializes the application and provides a command-line interface
for running predictions.
"""

import argparse
import sys
import os
from datetime import datetime

# Add the project root to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.predictor import predict, PredictionRequest
from fastapi import FastAPI

# FastAPI app is mounted in api.routes.router
from api.routes import router as api_router

app: FastAPI = FastAPI(title="F1 Prediction API")
app.include_router(api_router, prefix="/api/v1")

from config.settings import API_CONFIG, ENGINE_CONFIG, logger
from scripts.data_quality_report import run_data_quality_report


def run_api_server():
    """Start the Flask API server."""
    logger.info("Starting API server...")
    app.run(
        host=API_CONFIG.host,
        port=API_CONFIG.port,
        debug=API_CONFIG.debug
    )


def run_prediction(args):
    """Run a single prediction based on command-line arguments."""
    logger.info("Running prediction from command line...")
    
    # Create prediction request from args
    request = PredictionRequest(
        circuit_id=args.circuit,
        rain_probability=args.rain_prob,
        n_simulations=args.sim_count,
        seed=args.seed or ENGINE_CONFIG.default_seed,
        output_format=args.output_format,
        include_intermediate_artifacts=args.include_intermediate
    )
    
    print(f"Generating prediction for {args.circuit} GP with {args.sim_count} simulations...")
    if request.seed is not None:
        print(f"Using seed: {request.seed}")
    if args.rain_prob is not None:
        print(f"Rain probability: {args.rain_prob:.2f}")
    
    # Run prediction
    result = predict(request)
    
    # Print summary
    print(f"\nPredicted podium for {result['meta']['circuit']}:")
    for i, driver in enumerate(result['predictions'][:3], 1):
        print(f"{i}. {driver['driver']} ({driver['team']}) - Win prob: {driver['win_pct']}%")
    
    # Optionally save detailed results
    if args.save_file:
        import json
        filename = args.save_file
        if not filename.endswith('.json'):
            filename += '.json'
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nDetailed results saved to: {filename}")


def run_data_quality_check():
    """Run the data quality report."""
    print("Running data quality report...\n")
    issues, successes = run_data_quality_report()
    
    print("SUCCESS CHECKS:")
    for success in successes:
        print(f"  ✓ {success}")
    
    print("\nISSUES FOUND:")
    if not issues:
        print("  No issues found!")
    else:
        for issue in issues:
            print(f"  ✗ {issue}")
    
    print(f"\nSummary: {len(successes)} checks passed, {len(issues)} issues found")


def main():
    parser = argparse.ArgumentParser(description="F1 Prediction System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # API server command
    api_parser = subparsers.add_parser('api', help='Run the API server')
    
    # Prediction command
    pred_parser = subparsers.add_parser('predict', help='Run a single prediction')
    pred_parser.add_argument('--circuit', required=True, help='Circuit ID (e.g., canada, monaco)')
    pred_parser.add_argument('--rain-prob', type=float, help='Rain probability (0.0-1.0)')
    pred_parser.add_argument('--sim-count', type=int, default=5000, help='Number of simulations')
    pred_parser.add_argument('--seed', type=int, help='Random seed for deterministic runs')
    pred_parser.add_argument('--output-format', default='full', 
                            choices=['full', 'summary', 'intermediate', 'winner_only'],
                            help='Output format for predictions')
    pred_parser.add_argument('--include-intermediate', action='store_true',
                            help='Include intermediate artifacts in output')
    pred_parser.add_argument('--save-file', help='Save results to JSON file')
    
    # Data quality command
    dq_parser = subparsers.add_parser('quality-check', help='Run data quality report')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(log_level)
    
    if args.command == 'api':
        run_api_server()
    elif args.command == 'predict':
        run_prediction(args)
    elif args.command == 'quality-check':
        run_data_quality_check()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()