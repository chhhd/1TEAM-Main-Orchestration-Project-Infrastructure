#!/usr/bin/env python3
"""evidence/evidence.csv를 날짜별로 쪼개서 evidence/evidence_<날짜>.csv로 추출한다.

evidence.csv 자체는 5명 전원이 공유하는 단일 진실 소스라 쪼개거나 이름을
바꾸지 않는다(append-only 원칙 유지) — 이 스크립트는 원본은 그대로 두고,
"그날 진행한 내용"만 보고 싶을 때 쓰는 읽기 전용 파생 산출물을 만든다.

timestamp가 `YYYY-MM-DD HH:MM` 형식(2026-08-18부터 기본)인 행만 날짜를
확실히 알 수 있다. 그 이전에 기록된 `HH:MM` 전용 행은 날짜를 스스로 판단할
수 없으므로 --date로 콕 집어 요청해도 대상에서 제외되고, 한 번만 경고로
알려준다 (README.md의 "알려진 한계" 참고 — 필요하면 git log 커밋 시각으로
직접 보정).

Usage:
    python scripts/export_by_date.py                  # 오늘 날짜만 추출
    python scripts/export_by_date.py --date 2026-08-18 # 특정 날짜만 추출
    python scripts/export_by_date.py --all             # 날짜별로 전부 추출
    python scripts/export_by_date.py --agent Recon      # agent로도 추가 필터
"""
import argparse
import csv
import os
import re
import sys
from datetime import date

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(ROOT, "evidence", "evidence.csv")
OUT_DIR = os.path.join(ROOT, "evidence")

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[ T]\d{2}:\d{2}$")


def row_date(row):
    m = DATE_RE.match(row.get("timestamp", ""))
    return m.group(1) if m else None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--date", default=None, help="YYYY-MM-DD. 생략하면 오늘 날짜")
    p.add_argument("--all", action="store_true", help="evidence.csv에 있는 모든 날짜를 각각 추출")
    p.add_argument("--agent", default=None, help="Recon/Injection/IDOR/Auth/CVE 중 하나로 추가 필터")
    args = p.parse_args()

    if not os.path.exists(CSV_PATH):
        print("evidence/evidence.csv가 아직 없음 — 기록된 시도가 없다.")
        return

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    undated = [r for r in rows if row_date(r) is None]
    if undated:
        print(f"[경고] 날짜를 알 수 없는(YYYY-MM-DD 형식이 아닌) 행 {len(undated)}건은 "
              f"제외됨 — README.md '알려진 한계' 참고", file=sys.stderr)

    if args.agent:
        rows = [r for r in rows if r.get("agent") == args.agent]

    if args.all:
        target_dates = sorted({d for r in rows if (d := row_date(r))})
    else:
        target_dates = [args.date or date.today().isoformat()]

    if not target_dates:
        print("추출할 날짜가 있는 행이 없음.")
        return

    for d in target_dates:
        day_rows = [r for r in rows if row_date(r) == d]
        out_path = os.path.join(OUT_DIR, f"evidence_{d}.csv")
        if not day_rows:
            print(f"{d}: 해당 날짜 행 없음 — {out_path} 생성하지 않음")
            continue
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(day_rows)
        print(f"{d}: {len(day_rows)}건 -> {out_path}")


if __name__ == "__main__":
    main()
