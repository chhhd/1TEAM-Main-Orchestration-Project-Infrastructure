#!/usr/bin/env python3
"""Append one row to evidence/evidence.csv — the common schema all five
team members use. Always go through this script rather than hand-editing
the CSV: payloads routinely contain commas, quotes, and newlines (SQLi/SSTI
payloads especially), and csv.writer is what keeps those from corrupting
the file. Run once per test attempt, immediately after that attempt.

Usage:
    python scripts/append_evidence.py \\
        --target http://127.0.0.1:5000 \\
        --endpoint "/search?q=" \\
        --agent Injection \\
        --operator 임희영 \\
        --caller manual \\
        --hypothesis "Boolean 기반 SQLi 여부" \\
        --payload "q=' OR '1'='1" \\
        --observation "응답 200, 레코드 2건->3건 (기밀 레코드 포함)" \\
        --new-info yes \\
        --status unconfirmed \\
        --evidence-ref -
"""
import argparse
import csv
import os
import sys
from datetime import datetime

# Windows consoles often default to cp949/cp1252, which can't encode Korean
# text or em-dashes in this script's help/output — force UTF-8 regardless
# of the console codepage rather than stripping non-ASCII content.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(ROOT, "evidence", "evidence.csv")
FIELDS = ["timestamp", "target", "endpoint", "agent", "operator", "caller",
          "hypothesis", "payload", "observation", "new_info", "status", "evidence_ref"]

AGENTS = ("Recon", "Injection", "IDOR", "Auth", "CVE")
CALLERS = ("manual", "orchestrator")
NEW_INFO = ("yes", "no")
STATUSES = ("unconfirmed", "confirmed", "dead-end")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", required=True)
    p.add_argument("--endpoint", required=True)
    p.add_argument("--agent", required=True, choices=AGENTS)
    p.add_argument("--operator", required=True, help="실행한 사람 이름")
    p.add_argument("--caller", required=True, choices=CALLERS)
    p.add_argument("--hypothesis", required=True)
    p.add_argument("--payload", required=True)
    p.add_argument("--observation", required=True)
    p.add_argument("--new-info", required=True, dest="new_info", choices=NEW_INFO)
    p.add_argument("--status", required=True, choices=STATUSES)
    p.add_argument("--evidence-ref", default="-", dest="evidence_ref")
    p.add_argument("--timestamp", default=None,
                    help="YYYY-MM-DD HH:MM 형식. 생략하면 현재 날짜/시각으로 자동 채움 "
                         "(2026-08-18부로 날짜 포함이 기본 — 기존 행의 HH:MM 전용 형식은 "
                         "그대로 두고 새 행부터 적용)")
    return p.parse_args()


def main():
    args = parse_args()
    timestamp = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    is_new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": timestamp,
            "target": args.target,
            "endpoint": args.endpoint,
            "agent": args.agent,
            "operator": args.operator,
            "caller": args.caller,
            "hypothesis": args.hypothesis,
            "payload": args.payload,
            "observation": args.observation,
            "new_info": args.new_info,
            "status": args.status,
            "evidence_ref": args.evidence_ref,
        })
    print(f"appended: {timestamp} {args.agent} {args.endpoint} [{args.status}] by {args.operator}")


if __name__ == "__main__":
    main()
