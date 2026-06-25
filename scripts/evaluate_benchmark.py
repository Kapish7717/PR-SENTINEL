import os
import sys
import json
import glob

# Add parent directory of 'scripts' to python search path to support running from workspace root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env manually before other imports
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

# Verify that GROQ_API_KEY is available
if not os.environ.get("GROQ_API_KEY"):
    print("[ERROR] GROQ_API_KEY is not set in environment or .env file.")
    sys.exit(1)

from agent.graph import graph

def evaluate_patch(patch_path, expected_path):
    print(f"\n--- Evaluating {os.path.basename(patch_path)} ---")
    
    with open(patch_path, "r", encoding="utf-8") as f:
        raw_diff = f.read()
        
    with open(expected_path, "r", encoding="utf-8") as f:
        expected_findings = json.load(f)
        
    initial_state = {
        "raw_diff": raw_diff,
        "parsed_files": [],
        "lint_issues": [],
        "llm_findings": [],
        "all_findings": [],
        "final_review": [],
        "owner": "",
        "repo": "",
        "pr_number": ""
    }
    
    # Invoke the review pipeline
    result = graph.invoke(initial_state)
    bot_findings = result.get("final_review", [])
    
    print(f"Bot generated {len(bot_findings)} findings.")
    print(f"Expected {len(expected_findings)} findings.")
    
    true_positives = []
    false_positives = []
    matched_expected = set()
    
    for gen in bot_findings:
        matched = False
        for idx, exp in enumerate(expected_findings):
            # Match condition: same file and line within tolerance (default +/- 2 lines)
            file_match = gen.get("file") == exp.get("file")
            line_diff = abs(int(gen.get("line", -10)) - int(exp.get("line", -100)))
            line_match = line_diff <= 2
            
            if file_match and line_match:
                matched = True
                matched_expected.add(idx)
                true_positives.append((gen, exp))
                break
        
        if not matched:
            false_positives.append(gen)
            
    false_negatives = [exp for idx, exp in enumerate(expected_findings) if idx not in matched_expected]
    
    tp_count = len(true_positives)
    fp_count = len(false_positives)
    fn_count = len(false_negatives)
    
    # Calculate metrics
    precision = (tp_count / len(bot_findings) * 100.0) if bot_findings else (100.0 if not expected_findings else 0.0)
    recall = (tp_count / len(expected_findings) * 100.0) if expected_findings else 100.0
    
    print("\n[CORRECT] True Positives (Correct Findings):")
    for gen, exp in true_positives:
        print(f"  - [{gen.get('file')}:{gen.get('line')}] Severity: {gen.get('severity')} - {gen.get('comment')}")
        print(f"    (Matched Expected Line: {exp.get('line')})")
        
    if false_positives:
        print("\n[INCORRECT] False Positives (Incorrect/Hallucinated Findings):")
        for gen in false_positives:
            print(f"  - [{gen.get('file')}:{gen.get('line')}] Severity: {gen.get('severity')} - {gen.get('comment')}")
            
    if false_negatives:
        print("\n[MISSED] False Negatives (Missed Expected Findings):")
        for exp in false_negatives:
            print(f"  - [{exp.get('file')}:{exp.get('line')}] Type: {exp.get('issue_type')}")
            
    print(f"\n[METRICS] Metrics for {os.path.basename(patch_path)}:")
    print(f"  Reviewer Acceptance Rate (Precision): {precision:.2f}%")
    print(f"  Recall:                                {recall:.2f}%")
    
    return {
        "tp": tp_count,
        "fp": fp_count,
        "fn": fn_count,
        "total_bot": len(bot_findings),
        "total_exp": len(expected_findings)
    }

def main():
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_diffs"))
    patch_files = glob.glob(os.path.join(test_dir, "*.patch"))
    
    if not patch_files:
        print(f"No patch files found in {test_dir}")
        return
        
    overall_tp = 0
    overall_fp = 0
    overall_fn = 0
    overall_bot = 0
    overall_exp = 0
    
    results = []
    
    for patch_path in patch_files:
        # Check for corresponding expected findings json
        base_name = os.path.basename(patch_path).replace(".patch", "")
        expected_path = os.path.join(test_dir, f"{base_name}_expected.json")
        
        if not os.path.exists(expected_path):
            print(f"[WARNING] Missing expected findings file for {os.path.basename(patch_path)}. Skipping.")
            continue
            
        metrics = evaluate_patch(patch_path, expected_path)
        overall_tp += metrics["tp"]
        overall_fp += metrics["fp"]
        overall_fn += metrics["fn"]
        overall_bot += metrics["total_bot"]
        overall_exp += metrics["total_exp"]
        results.append((base_name, metrics))
        
    print("\n" + "=" * 60)
    print("OVERALL BENCHMARK EVALUATION SUMMARY")
    print("=" * 60)
    
    for name, metrics in results:
        prec = (metrics["tp"] / metrics["total_bot"] * 100.0) if metrics["total_bot"] else (100.0 if not metrics["total_exp"] else 0.0)
        rec = (metrics["tp"] / metrics["total_exp"] * 100.0) if metrics["total_exp"] else 100.0
        print(f"- {name:<25}: Acceptance Rate={prec:>6.2f}% | Recall={rec:>6.2f}% (TP={metrics['tp']}, FP={metrics['fp']}, FN={metrics['fn']})")
        
    overall_precision = (overall_tp / overall_bot * 100.0) if overall_bot else (100.0 if not overall_exp else 0.0)
    overall_recall = (overall_tp / overall_exp * 100.0) if overall_exp else 100.0
    
    print("-" * 60)
    print(f"  Global Reviewer Acceptance Rate:  {overall_precision:.2f}%")
    print(f"  Global Recall:                  {overall_recall:.2f}%")
    print(f"  Total Findings:                 {overall_bot} (Correct: {overall_tp}, Incorrect: {overall_fp}, Missed: {overall_fn})")
    print("=" * 60)

if __name__ == "__main__":
    main()
