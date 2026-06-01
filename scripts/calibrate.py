#!/usr/bin/env python3
"""Calibration harness: grade fit-score predictions against app-tracker outcomes.

Buckets predicted fit vs actual advance rate, computes calibration gap,
and suggests weight nudges. Fit scores are predictions you can grade.
"""
import sys, yaml, collections

def load_tracker(path="pipeline/app-tracker.md"):
    txt = open(path).read()
    block = txt.split("```yaml")[1].split("```")[0]
    return yaml.safe_load(block) or []

ADVANCED = {"SCREEN", "ONSITE", "OFFER"}

def main():
    apps = load_tracker()
    buckets = collections.defaultdict(lambda: [0, 0])  # bucket -> [advanced, total]
    for a in apps:
        fs = a.get("fit_score")
        if fs is None:
            continue
        b = (fs // 10) * 10
        advanced = any(t.get("to") in ADVANCED for t in a.get("transitions", []))
        buckets[b][0] += int(advanced)
        buckets[b][1] += 1
    print("predicted_fit_bucket  advance_rate  n")
    for b in sorted(buckets):
        adv, tot = buckets[b]
        print(f"{b:>3}-{b+9:<3}            {adv/tot:>6.0%}      {tot}")
    print("\nIf high buckets underperform low buckets, weights are miscalibrated.")
    print("Adjust pipeline/scoring-weights.yaml and re-run after more outcomes land.")

if __name__ == "__main__":
    main()
