# evidence.csv — 공통 스키마 & 기록 절차

5명 전원(오케스트레이션/Recon/Injection/Access-control/CVE)이 같은 파일,
같은 컬럼을 쓴다. 절차 전문은 `.claude/skills/evidence-logging/SKILL.md`에
있고(각 agent가 실행 중 로드함), 여기는 사람이 읽는 참고용 요약이다.

## 스키마

```
timestamp,target,endpoint,agent,operator,caller,hypothesis,payload,observation,new_info,status,evidence_ref
```

| 컬럼 | 의미 |
|---|---|
| `timestamp` | 기록 시각 `HH:MM` (예: `14:32`). **알려진 한계: 날짜가 없다** — 여러 날짜에 걸친 로그를 구분해야 하면 `git log`의 커밋 시각으로 보정한다. 스키마를 임의로 바꾸지 않는다 |
| `target` | 테스트한 base URL |
| `endpoint` | 구체적인 엔드포인트/파라미터 |
| `agent` | `Recon` \| `Injection` \| `IDOR` \| `Auth` \| `CVE` (닫힌 어휘) — `IDOR`은 객체/BOLA류, `Auth`는 수직 권한상승·비즈니스 로직류 (access-control-agent가 둘 다 다루므로 이 컬럼으로 세부 구분) |
| `operator` | 실행한 사람 이름 |
| `caller` | `manual`(사람이 직접 골라서 실행) \| `orchestrator`(오케스트레이터가 지시) |
| `hypothesis` | 이번 시도로 뭘 확인하려 했는지 한 줄 — **결과를 보기 전에** 적는다 |
| `payload` | 실제 사용한 payload/요청 (재현용, 핵심) |
| `observation` | 관찰된 응답/차이 (구체적으로: 상태코드, 길이, 에러 문자열 등) |
| `new_info` | `yes`/`no` — 이 시도로 새 정보를 얻었는가 |
| `status` | `unconfirmed` → (재현 2~3회 후) `confirmed`, 또는 `dead-end` |
| `evidence_ref` | 스크린샷/로그 파일 경로, 없으면 `-` |

## 행 추가는 항상 스크립트로

CSV를 텍스트 에디터로 직접 고치지 않는다 — payload에 쉼표/따옴표가 섞이면
(SQLi/SSTI payload는 거의 항상 그렇다) 손 편집은 파일을 깨뜨린다.

```bash
python scripts/append_evidence.py \
  --target http://127.0.0.1:5000 --endpoint "/search?q=" --agent Injection \
  --operator 임희영 --caller manual \
  --hypothesis "Boolean 기반 SQLi 여부" \
  --payload "q=' OR '1'='1" \
  --observation "응답 200, 레코드 2건->3건 (기밀 레코드 포함)" \
  --new-info yes --status unconfirmed --evidence-ref -
```

재현 확인 후 승격할 땐 **기존 행을 고치지 말고** 같은 커맨드를
`--status confirmed`로 다시 실행해 새 행을 추가한다 — 이 파일은
append-only 로그다.

## 절차 (5명 전원 동일)

1. **테스트 시작 전** — 상태판에서 해당 endpoint를 "진행중"으로 바꾸고 이름 표시.
2. **Agent 실행** — 각자 전문 agent로 테스트. agent 정의(`.claude/agents/*.md`)에
   이미 "hypothesis/payload/observation을 명시하라"는 지시가 skill로 강제돼
   있어서, 이 단계에서 바로 로그에 옮길 재료가 나온다.
3. **시도 하나 끝날 때마다 즉시 한 행 기록** — 몰아서 적지 않는다.
4. **status는 본인이 1차 판단** — `unconfirmed`로 우선 기록, 재현 2~3회 확인 후
   본인이 `confirmed`로 승격. 애매하면 CVE 담당(박정근)이나 팀원1에게
   크로스체크 요청 후 승격.
5. **커밋 & 상태판 갱신**:
   ```bash
   git add evidence/evidence.csv
   git commit -m "<이름>: <endpoint> <agent> 시도 N건"
   git push
   ```
   그리고 상태판을 성공/실패/막힘으로 갱신.
6. **`1TEAM-MEMORY`에도 동기화** — 실제 Phase 1~4 게임 중에는 5번에서 커밋한
   같은 행을 옆에 클론해둔 [`1TEAM-MEMORY`](https://github.com/chhhd/1TEAM-MEMORY)에도
   append하고 push한다 (스크립트/스키마 동일, `1TEAM-MEMORY/scripts/append_evidence.py`
   사용). 팀원1(본인)이 Phase 3에서 실제로 취합해야 할 건 이 레포뿐 아니라
   나머지 4개 레포의 시도까지이므로, 각자 자기 레포 push 후 `1TEAM-MEMORY`에도
   동기화하는 걸 팀 전체에 상기시킨다.
7. **오케스트레이터 호출 시점** — 팀원1이 `1TEAM-MEMORY` 클론에서 아래로
   confirmed 행만 모아 전달 (5개 레포 각각이 아니라 `1TEAM-MEMORY`의
   evidence.csv 기준 — 그래야 5명분이 한 파일에서 모인다):
   ```bash
   python scripts/confirmed_summary.py               # 전체
   python scripts/confirmed_summary.py --agent IDOR   # 특정 agent만
   ```

## 상태판(Notion)

팀 통합 규정 저장소(`1TEAM-MEMORY`)에 실제 상태판 링크가 있다:
https://app.notion.com/p/3ba73ca863d880b9b13ddb4d07c91b9c

Claude Code 쪽에 Notion MCP 연동을 붙이는 작업은 아직 이 저장소에는 없다
(page ID는 확보됐으므로, MCP 연결 설정이 정해지면 §절차 1번의 "상태판에서
진행중으로 표시"를 자동화할 수 있다). 그 전까지는 위 절차대로 **사람이
직접** 상태판을 갱신하고, `evidence.csv`의 `status` 컬럼과 git 커밋 로그
(`git log --oneline evidence/evidence.csv`)가 보조 상태판 역할을 한다.

## 팀 로스터 (operator 이름 통일용)

| 이름 | 담당 |
|---|---|
| 이동건 | 오케스트레이션 & 인프라 |
| 이나윤 | Recon |
| 임희영 | Injection |
| 박나현 | IDOR / Auth (Access-control) |
| 박정근 | CVE & 평가 |
