import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from classification.classifier import classify_app

def run_eval():
    with open("tests/eval_set.json") as f:
        eval_set = json.load(f)

    results = {
        "total": len(eval_set),
        "gender_correct": 0,
        "age_correct": 0,
        "income_correct": 0,
        "tier_correct": 0,
        "failures": []
    }

    for case in eval_set:
        print(f"Evaluating: {case['package_name']}...")
        try:
            actual = classify_app(case['package_name'], country='in')
            if not actual:
                print(f"  Skipped - no data found")
                continue

            expected = case['expected']

            if actual['gender']['label'] == expected['gender']:
                results['gender_correct'] += 1
            else:
                results['failures'].append({
                    'app': case['package_name'],
                    'field': 'gender',
                    'expected': expected['gender'],
                    'got': actual['gender']['label']
                })

            if actual['age']['primary_bucket'] == expected['age']:
                results['age_correct'] += 1
            else:
                results['failures'].append({
                    'app': case['package_name'],
                    'field': 'age',
                    'expected': expected['age'],
                    'got': actual['age']['primary_bucket']
                })

            if actual['income']['label'] == expected['income']:
                results['income_correct'] += 1
            else:
                results['failures'].append({
                    'app': case['package_name'],
                    'field': 'income',
                    'expected': expected['income'],
                    'got': actual['income']['label']
                })

            if actual['signal_tier'] == expected['signal_tier']:
                results['tier_correct'] += 1
            else:
                results['failures'].append({
                    'app': case['package_name'],
                    'field': 'signal_tier',
                    'expected': expected['signal_tier'],
                    'got': actual['signal_tier']
                })

        except Exception as e:
            print(f"  Error: {e}")

    total = results['total']
    print(f"\n=== EVAL RESULTS ===")
    print(f"Gender accuracy : {results['gender_correct']}/{total} ({results['gender_correct']/total*100:.0f}%)")
    print(f"Age accuracy    : {results['age_correct']}/{total} ({results['age_correct']/total*100:.0f}%)")
    print(f"Income accuracy : {results['income_correct']}/{total} ({results['income_correct']/total*100:.0f}%)")
    print(f"Tier accuracy   : {results['tier_correct']}/{total} ({results['tier_correct']/total*100:.0f}%)")

    print(f"\n=== FAILURES ===")
    for f in results['failures']:
        print(f"  {f['app']}: {f['field']} expected={f['expected']} got={f['got']}")

    with open('tests/eval_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to tests/eval_results.json")

if __name__ == "__main__":
    run_eval()