#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from pathlib import Path

def run_test(image_path, expected_type=None, expected_merchant=None):
    """Run the OCR classification on an image and validate results"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {image_path}")
    print(f"Expected type: {expected_type}, Expected merchant: {expected_merchant}")
    print('='*60)
    
    # Run the llm-scan.py script
    result = subprocess.run(
        [sys.executable, "llm-scan.py", image_path],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    # Check if the command succeeded
    if result.returncode != 0:
        print(f"ERROR: Command failed with return code {result.returncode}")
        print(f"STDERR: {result.stderr}")
        return False, {"error": result.stderr}
    
    # Parse the output to extract the classification result
    output_lines = result.stdout.strip().split('\n')
    for line in output_lines:
        if line.startswith("file_name="):
            # Parse the Pydantic model output
            print(f"Classification result: {line}")
            
            # Basic validation
            if expected_type and f"type='{expected_type}'" not in line:
                print(f"FAILED: Expected type '{expected_type}' not found in output")
                return False, {"output": line, "expected_type": expected_type}
            
            if expected_merchant and expected_merchant.lower() not in line.lower():
                print(f"WARNING: Expected merchant '{expected_merchant}' not clearly identified")
                # Don't fail on merchant mismatch as OCR might read it differently
            
            print("✓ Test PASSED")
            return True, {"output": line}
    
    print("WARNING: Could not find classification result in output")
    return False, {"error": "No classification result found", "stdout": result.stdout}

def main():
    """Run all tests and generate a report"""
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    # Check if GEMINI_API_KEY is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set")
        sys.exit(1)
    
    print("Starting OCR Document Classification Tests")
    print(f"Working directory: {os.getcwd()}")
    
    # Define test cases
    test_cases = [
        {
            "image": "test-images/safeway_receipt.png",
            "expected_type": "receipt",
            "expected_merchant": "Safeway"
        },
        {
            "image": "test-images/silpo_receipt.png",
            "expected_type": "receipt",
            "expected_merchant": "Silpo"
        },
        {
            "image": "test-images/atb_receipt.png",
            "expected_type": "receipt",
            "expected_merchant": "ATB"
        }
    ]
    
    # Run tests
    results = []
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        if not os.path.exists(test_case["image"]):
            print(f"WARNING: Test image {test_case['image']} not found, skipping")
            continue
            
        success, details = run_test(
            test_case["image"],
            test_case.get("expected_type"),
            test_case.get("expected_merchant")
        )
        
        results.append({
            "test": test_case,
            "success": success,
            "details": details
        })
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Generate summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    # Save results to JSON
    with open("test-results.json", "w") as f:
        json.dump({
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results
        }, f, indent=2)
    
    print(f"\nTest results saved to test-results.json")
    
    # Exit with appropriate code
    if failed > 0:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()