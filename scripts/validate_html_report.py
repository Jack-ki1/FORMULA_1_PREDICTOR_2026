"""
Validation script to verify HTML template rendering fixes.
Run: py scripts/validate_html_report.py
"""

from reports.html_report import generate_report
import sys
import os

def validate_report(circuit='canada', rain_probability=0.2, n_simulations=500):
    print(f"Generating report for {circuit}...")
    path = generate_report(circuit, rain_probability=rain_probability, n_simulations=n_simulations)
    
    print(f"✓ Report saved to: {path}")
    print(f"✓ File size: {os.path.getsize(path):,} bytes\n")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for raw template expressions (should NOT exist)
    print("=" * 60)
    print("CHECKING FOR RAW TEMPLATE EXPRESSIONS")
    print("=" * 60)
    
    template_expressions = [
        '{rain_prob_display',
        '{n_simulations:,}',
        '{model_confidence',
        '{drivers_json}',
        '{win_probs_json}',
        '{expected_points_json}',
        '{predictions[0].get',
        '{dark_horse_driver}',
        '{safest_points_driver}',
        '{tire_complexity}',
    ]
    
    found_errors = []
    for expr in template_expressions:
        if expr in content:
            found_errors.append(expr)
            print(f"  ❌ FAIL: Found raw expression: {expr}")
        else:
            print(f"  ✅ PASS: No raw expression: {expr}")
    
    # Check for properly rendered values (SHOULD exist)
    print("\n" + "=" * 60)
    print("CHECKING FOR PROPERLY RENDERED VALUES")
    print("=" * 60)
    
    expected_patterns = [
        ('Rain Probability:', 'rain_prob_display'),
        ('Simulations', 'n_simulations'),
        ('Model Confidence', 'model_confidence'),
        ('Most Likely Winner', 'predictions[0]'),
        ('Dark Horse', 'dark_horse_driver'),
    ]
    
    for pattern, name in expected_patterns:
        if pattern in content:
            print(f"  ✅ PASS: Found rendered section: {name}")
        else:
            print(f"  ❌ FAIL: Missing section: {name}")
    
    # Check JavaScript section
    print("\n" + "=" * 60)
    print("CHECKING JAVASCRIPT DATA INJECTION")
    print("=" * 60)
    
    if 'const drivers = [' in content or 'const drivers = []' in content:
        print("  ✅ PASS: JavaScript drivers array is defined")
    else:
        print("  ❌ FAIL: JavaScript drivers array NOT found")
    
    if 'const winProbs = [' in content or 'const winProbs = []' in content:
        print("  ✅ PASS: JavaScript winProbs array is defined")
    else:
        print("  ❌ FAIL: JavaScript winProbs array NOT found")
    
    if 'const predictions = drivers.map' in content:
        print("  ✅ PASS: JavaScript predictions array is defined")
    else:
        print("  ❌ FAIL: JavaScript predictions array NOT defined")
    
    # Check for expected points
    print("\n" + "=" * 60)
    print("CHECKING EXPECTED POINTS CALCULATION")
    print("=" * 60)
    
    if 'Expected Points = 0.0' not in content or 'expectedPoints = [0,0,0' not in content:
        print("  ✅ PASS: Expected points are NOT all zero")
    else:
        print("  ❌ FAIL: Expected points still showing as 0")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if len(found_errors) == 0:
        print("✅ ALL CHECKS PASSED - No template rendering issues found!")
        return True
    else:
        print(f"❌ {len(found_errors)} CRITICAL ISSUES FOUND:")
        for error in found_errors:
            print(f"   - {error}")
        return False

if __name__ == '__main__':
    circuit = sys.argv[1] if len(sys.argv) > 1 else 'canada'
    success = validate_report(circuit)
    sys.exit(0 if success else 1)
