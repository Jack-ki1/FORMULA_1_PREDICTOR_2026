"""
Measure accuracy script - evaluates model performance on historical data.
Runs the benchmark suite and generates accuracy reports.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.benchmark_suite import benchmark_suite


def measure_accuracy():
    """Run accuracy measurement on historical data."""
    print("Measuring model accuracy...")
    
    try:
        # Generate accuracy report
        report = benchmark_suite.generate_accuracy_report()
        
        print("\n=== Model Accuracy Report ===")
        print(f"Overall Model Accuracy: {report['overall_performance']['average_model_accuracy']:.2%}")
        print(f"Overall Baseline Accuracy: {report['overall_performance']['average_baseline_accuracy']:.2%}")
        print(f"Overall Improvement: {report['overall_performance']['average_improvement']:.2%}")
        
        print("\n=== Target-Specific Accuracy ===")
        for target_id, metrics in report['target_accuracies'].items():
            print(f"\n{metrics['target_label']}:")
            print(f"  Model Accuracy: {metrics['model_accuracy']:.2%}")
            print(f"  Baseline Accuracy: {metrics['baseline_accuracy']:.2%}")
            print(f"  Improvement: {metrics['improvement']:.2%} ({metrics['improvement_percentage']:.1f}%)")
        
        print("\n=== Recommendations ===")
        for recommendation in report['recommendations']:
            print(f"  • {recommendation}")
        
        print("\n✓ Accuracy measurement completed")
        
    except Exception as e:
        print(f"\n✗ Accuracy measurement failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    measure_accuracy()
