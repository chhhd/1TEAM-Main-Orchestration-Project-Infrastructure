#!/usr/bin/env python3
"""팀원1(오케스트레이션 담당)이 오케스트레이터 세션 호출 시점에 쓰는 도구.

evidence/evidence.csv에서 status=="confirmed" 행만 골라 오케스트레이터에게
넘길 압축 요약을 만든다. unconfirmed/dead-end 행은 원본 CSV에는 남아있지만
이 요약에는 들어가지 않는다 — 오케스트레이터 컨텍스트에 검증 중인 가설까지
전달해서 혼동을 주지 않기 위함.

Usage:
    python scripts/confirmed_summary.py                # 전체 confirmed 요약
    python scripts/confirmed_summary.py --agent Injection
    python scripts/confirmed_summary.py --since-endpoint /search
"""
import argparse
import csv
import os
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(ROOT, "evidence", "evidence.csv")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--agent", default=None, help="Recon/Injection/IDOR/Auth/CVE 중 하나로 필터")
    args = p.parse_args()

    if not os.path.exists(CSV_PATH):
        print("evidence/evidence.csv가 아직 없음 — 기록된 시도가 없다.")
        return

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("status") == "confirmed"]

    if args.agent:
        rows = [r for r in rows if r.get("agent") == args.agent]

    if not rows:
        print("confirmed 행 없음.")
        return

    print(f"## Confirmed findings ({len(rows)}건) — 오케스트레이터 전달용\n")
    for r in rows:
        print(f"### [{r['agent']}] {r['endpoint']} — {r['timestamp']} by {r['operator']} ({r['caller']})")
        print(f"- Target: {r['target']}")
        print(f"- Hypothesis: {r['hypothesis']}")
        print(f"- Payload: {r['payload']}")
        print(f"- Observation: {r['observation']}")
        print(f"- New info: {r['new_info']}")
        if r['evidence_ref'] and r['evidence_ref'] != "-":
            print(f"- Evidence ref: {r['evidence_ref']}")
        print()


if __name__ == "__main__":
    main()
