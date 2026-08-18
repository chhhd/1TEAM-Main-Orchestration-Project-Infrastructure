# 팀 워크플로 (Phase 0~4)

5인 팀이 대상을 진단하는 전체 사이클. `CLAUDE.md`의 §Agent 라우팅 규칙·
§종료 조건·§중복 방지 규칙·§기록 절차를 실제 시간 순서로 풀어놓은 문서다.
두 문서가 상충하면 `CLAUDE.md`가 우선한다.

## Phase 0 — 시작 전 (5분)

팀원1(이동건)이 체크리스트 확인: 전원 레포 pull 완료, 계정 분리(각자 다른
테스트 계정), `target-info.md`의 서버 정보 공유, 상태판 초기화.

> 상태판은 자동화된 Kanban 도구가 아니라 `1TEAM-MEMORY`의 Notion 페이지를
> 사람이 직접 갱신하는 것이다(Claude Code MCP 자동 연동은 아직 없음).
> "초기화"는 그 페이지를 이번 세션 대상에 맞게 정리해두는 것을 뜻한다.
> 자세한 건 `evidence/README.md`의 "상태판(Notion)" 절 참고.

여기서 팀원1은 이후 전체 진행에서 **Team Lead 겸 오케스트레이터 운영자**
역할을 맡는다.

## Phase 1 — Recon (5~10분, 단독 실행)

팀원2(이나윤)만 Recon Agent를 돌린다. 여러 명이 동시에 Recon 하면 중복이라
의미가 없다. 결과(Attack Surface)를 즉시 상태판 + evidence 로그에 반영하고
전원에게 공유.

## Phase 2 — 병렬 탐색 (본 게임)

Recon 결과를 보고 각자 자기 전문 Agent로 흩어진다.

- **임희영**: Injection 계열 Endpoint(`/search` 등) → Injection Agent로 독립 테스트
- **박나현**: IDOR/인가/로직 계열 Endpoint(`/user?id=`, `/admin` 등) → Access-Control Agent
- **박정근**: 앞의 두 명이 찾은 Evidence를 실시간으로 보면서 알려진 CVE/Advisory
  패턴과 대조, 필요하면 자기 CVE Agent로 보조 검증
    - 10분 주기로 살펴보고, 물어보기
- **이동건(팀원1)**: 이 구간에서는 직접 Agent를 돌리기보다 **상태판 모니터링 +
  Deconfliction**에 집중한다. 실제로 보는 건 Notion 상태판 + `evidence.csv`의
  `status` 컬럼 + `git log --oneline evidence/evidence.csv`다. 누가 같은
  Endpoint를 중복 테스트하는지, 누가 20분 이상 "막힘" 상태인지 확인하고 다른
  사람을 붙여주는 조율자 역할.
    - 증적들 모아서, 흐름 실행
- **이나윤(팀원2)**: Recon이 끝났으면 놀지 말고, 이 단계에서는 추가로 나온
  Endpoint(체이닝 중 새로 발견된 것들)에 대해 후속 Recon을 계속 수행하거나,
  막힌 사람 지원으로 투입.

각자 테스트 시작 전 상태판에 "in-progress" 표시 → 끝나면 evidence.csv에
즉시 구조화된 결과 기록. 이건 이전에 정리한 규칙(`evidence/README.md` §절차)
그대로 적용된다.

## Phase 3 — 체이닝 (Evidence 2~3개 쌓일 때마다 반복)

이동건이 `python scripts/confirmed_summary.py`로 **confirmed 행만 모아**
오케스트레이터 세션에 넣고, "이 발견들을 조합하면 권한상승이 가능한가"를
판단시킨다. `unconfirmed`/`dead-end` 행을 원본 CSV째로 넣지 않는 이유는
CLAUDE.md §기록 절차·§중복 방지 규칙("정찰 결과 전달 시 요약해서 넘긴다")과
토큰 최소화 원칙 때문이다.

여기서 유망한 조합(예: Injection으로 얻은 DB 정보 + IDOR로 얻은 계정 구조)이
나오면, 그걸 다시 담당자(희영/나현)에게 재할당해서 Phase 2 방식으로 검증.
이 Phase 2 ↔ Phase 3 사이클을 취약점이 실제 권한상승 체인으로 이어질 때까지
반복한다.

## Phase 4 — 완료

체인이 확인되면 즉시 전원에게 브로드캐스트하고 재현 절차를 기록. 이후
박정근이 전체 Evidence 로그를 정리해서 "어떤 Agent가 몇 번 만에, 어떤
모델로 뭘 찾았는지" 실험 결과 요약본을 만든다.

## 참고: 통합 저장소 구조 (합칠 때 최종 형태)

```
ctf-agent-harness/
├── README.md              # 팀 규칙, 링크(Notion 상태판 등) 정리
├── CLAUDE.md
├── .claude/
│   ├── agents/*.md
│   ├── skills/*/SKILL.md
│   ├── hooks/
│   └── settings.json
├── evidence/
│   ├── evidence.csv
│   └── evidence.md
└── target-info.md
```

| 팀원 | 산출물 | 확장자 | 경로 |
| --- | --- | --- | --- |
| 이동건 | 프로젝트 규칙, 권한 설정 | `CLAUDE.md`, `settings.json` | 레포 루트, `.claude/` |
| 이나윤 | Recon Agent 정의 + 절차 | `.md` | `.claude/agents/recon-agent.md`, `.claude/skills/recon/SKILL.md` |
| 임희영 | Injection Agent 정의 + 진단 절차 | `.md` | `.claude/agents/injection-agent.md`, `.claude/skills/injection/SKILL.md` |
| 박나현 | IDOR/Auth Agent 정의 + 체크리스트 | `.md` | `.claude/agents/access-control-agent.md`, `.claude/skills/access-control/SKILL.md` |
| 박정근 | CVE Agent, Hooks 스크립트 | `.md` + `.py`/`.sh`/`.js`(Hook용) | `.claude/agents/cve-agent.md`, `.claude/hooks/` |
