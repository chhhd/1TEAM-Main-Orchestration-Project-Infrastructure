---
name: evidence-logging
description: The common evidence.csv schema and recording procedure all five team members (Recon/Injection/IDOR-Auth/CVE agents, and the human operators running them) use for every test attempt. Load this whenever you run any specialist agent against a target — it defines what to log, when, and how, independent of which agent you are.
---

# Evidence Logging — Common Schema & Procedure

One schema, one CSV, used identically by every agent and every team member —
`recon`, `injection`, `access-control` (IDOR/Auth), and CVE work all log to
the same `evidence/evidence.csv`, never a per-agent file. This is what lets
팀원1 later pull a single confirmed-findings view across all five people's
work without reconciling five different formats.

## Schema

```
timestamp,target,endpoint,agent,operator,caller,hypothesis,payload,observation,new_info,status,evidence_ref
```

| Column | Meaning |
|---|---|
| `timestamp` | 기록 시각, `YYYY-MM-DD HH:MM` (예: `2026-08-18 14:32`). 2026-08-18부터 날짜 포함이 기본(`append_evidence.py`가 자동 채움) — 그 이전 행은 `HH:MM`만 있는 옛 형식 그대로이며, 그런 행의 날짜가 필요하면 git 커밋 시각으로 보정한다 |
| `target` | 테스트한 URL/파라미터의 target (base URL) |
| `endpoint` | 구체적인 엔드포인트/파라미터 (예: `/search?q=`) |
| `agent` | 어떤 전문 agent를 썼는지 — `Recon` \| `Injection` \| `IDOR` \| `Auth` \| `CVE` (닫힌 어휘, 새 값을 임의로 추가하지 않는다) |
| `operator` | 실행한 사람 이름 |
| `caller` | `manual`(사람이 직접 이 시도를 골라서 실행) \| `orchestrator`(오케스트레이터가 지시해서 실행) |
| `hypothesis` | 이번 시도로 뭘 확인하려 했는지 한 줄 |
| `payload` | 실제 사용한 payload/요청 — **재현의 핵심**, 생략하거나 대충 요약하지 않는다 |
| `observation` | 관찰된 응답/차이를 구체적으로 (숫자·상태코드·문자열 포함) |
| `new_info` | `yes` \| `no` — 이 시도로 새로운 정보를 얻었는가 |
| `status` | `unconfirmed` \| `confirmed` \| `dead-end` |
| `evidence_ref` | 스크린샷/로그 파일 경로, 없으면 `-` |

## Why an agent needs this at all

You (the specialist agent) are not just testing — you're producing the raw
material for this log. If your final report doesn't clearly separate
hypothesis / payload / observation for each attempt, the human operator has
to reverse-engineer those from prose after the fact, and that's exactly the
"기다렸다 몰아서 적기" failure mode this process exists to prevent. **State
your hypothesis before you send a payload, not after you see the result** —
that's what makes `new_info` and `status` honest judgments instead of
after-the-fact rationalization.

## What operator/caller you use

You will be told the operator's name and the caller mode (`manual` or
`orchestrator`) in your invocation prompt. **If you were not told, do not
guess a name** — use `caller=manual` only if a human is directly driving this
session interactively; otherwise ask, or if truly blocked, log
`operator=unknown` and flag it in your final report so the human fixes the
row before committing.

## Recording procedure (identical for all five team members)

1. **테스트 시작 전** — 상태판(Notion 등 팀이 쓰는 보드)에서 해당 endpoint를
   "진행중"으로 바꾸고 자기 이름 표시. (이 저장소에는 아직 실제 Notion 연동이
   없다 — `evidence/README.md`의 "상태판" 절 참고.)
2. **Agent 실행** — 이 skill이 강제하는 대로, 시도마다 hypothesis/payload/observation을
   명시적으로 말하면서 진행한다.
3. **시도 하나 끝날 때마다 즉시 한 행 기록** — 몰아서 적지 않는다. CSV를 직접
   손으로 편집하지 말고 반드시 헬퍼 스크립트를 쓴다 (payload에 쉼표/따옴표가
   섞이면 손으로 편집한 CSV는 깨진다):
   ```bash
   python scripts/append_evidence.py \
     --target <base-url> --endpoint "<endpoint>" --agent <Recon|Injection|IDOR|Auth|CVE> \
     --operator <이름> --caller <manual|orchestrator> \
     --hypothesis "<한 줄>" --payload "<실제 페이로드>" \
     --observation "<관찰>" --new-info <yes|no> --status unconfirmed --evidence-ref -
   ```
4. **status는 본인이 1차 판단** — 처음엔 `unconfirmed`로 기록. 재현 테스트
   2~3회 반복까지 확인되면 같은 endpoint/payload로 다시 스크립트를 실행해
   `--status confirmed`로 승격 행을 추가한다 (기존 행을 고치지 않고 새 행을
   추가 — CSV는 append-only 로그다). 판단이 애매하면 CVE 담당(팀원5)이나
   팀원1에게 크로스체크 요청한 뒤 승격한다.
5. **커밋 & 상태판 갱신** — 사람 오퍼레이터가 직접 실행 (agent가 git commit을
   대신 하지 않는다):
   ```bash
   git add evidence/evidence.csv
   git commit -m "<이름>: <endpoint> <agent> 시도 N건"
   git push
   ```
   그리고 상태판을 성공/실패/막힘으로 갱신한다.
6. **오케스트레이터 호출 시점** — 팀원1이 `python scripts/confirmed_summary.py`로
   confirmed 행만 모아 오케스트레이터 세션에 전달한다. unconfirmed/dead-end는
   원본 CSV에 남지만 이 요약에는 들어가지 않는다.

## Common mistakes

- 결과를 기다렸다 여러 건을 한 번에 기록 — payload/observation이 부정확해진다
- CSV를 텍스트 에디터로 직접 편집 — payload의 쉼표/따옴표가 필드를 깨뜨린다
- `status=confirmed`를 재현 없이 1회 관찰만으로 바로 부여
- `hypothesis`를 결과를 보고 나서 사후적으로 작성 (판단이 아니라 정당화가 됨)
