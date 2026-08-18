# 1TEAM-Main-Orchestration-Project-Infrastructure

팀원1(이동건) — 메인 오케스트레이션 & 프로젝트 인프라 담당 산출물.

## 이 저장소에 있는 것

| 산출물 | 위치 | 내용 |
|---|---|---|
| 프로젝트 규칙 / Agent 라우팅 | `CLAUDE.md` | `/search?q=` → injection-agent 등 라우팅 표, 종료 조건, 중복 방지 규칙 |
| 권한 모드 설계 | `.claude/settings.json` | `python`/`curl(loopback)`/`git status` 등은 자동 승인, `git push`/`git commit`/`rm`/외부 `curl`은 확인 요청, 파괴적 명령은 거부 |
| Local Vulnerable Web App | `vulnapp/app.py` | `/search`(SQLi), `/lookup`(음성 대조군), `/user?id=`(IDOR), `/admin`(무인증), `/upload`(무검증 업로드), `/fetch?url=`(SSRF) — 127.0.0.1:5000 전용 |
| 오케스트레이션 흐름 실측 검증 | `docs/orchestration-flow-verification.md` | recon → 라우팅 → injection-agent/access-control-agent 병렬 호출 → 결과 수렴까지, 실제 subagent 호출 + 실제 HTTP 요청으로 재현한 로그 (시뮬레이션 아님) |
| 증적 기록(evidence.csv) 절차 | `evidence/`, `scripts/`, `.claude/skills/evidence-logging/` | 5명 전원이 같은 스키마로 모든 테스트 시도를 append-only CSV에 남기는 절차 — 아래 참고 |
| 공용 실행 계약 / 안전장치 (내구성) | `dast-harness/` (git submodule, pull-only) | `AgentFinding`/`Evidence`/`Probe` 계약, `AgentHttpClient`, `safety.py`(loopback/allowlist 강제), 다중 스캐너 오케스트레이션(`MultiScanRunner`) — 아래 "dast-harness와의 관계" 참고 |

## 증적을 남기는 과정 (evidence.csv)

라우팅/흐름 검증과는 별개로, **모든 테스트 시도**(finding으로 이어졌든 아니든)를
공통 스키마로 남기는 절차를 만들었다.

- `evidence/evidence.csv` — `timestamp,target,endpoint,agent,operator,caller,hypothesis,payload,observation,new_info,status,evidence_ref` 스키마의 append-only 로그. `agent`는 `Recon`/`Injection`/`IDOR`/`Auth`/`CVE` 중 하나로 5명 전원이 같은 파일·같은 컬럼을 쓴다.
- `scripts/append_evidence.py` — 행 추가 전용 CLI. payload에 쉼표·따옴표가 섞여도 CSV가 깨지지 않도록 손 편집을 막는다.
- `scripts/confirmed_summary.py` — 오케스트레이터 호출 시점에 `status=confirmed` 행만 걸러서 전달용 요약을 만든다(팀원1이 실행).
- `.claude/skills/evidence-logging/SKILL.md` — 5개 agent 전원이 실행 중 로드하는 공용 절차: hypothesis는 결과를 보기 전에 적고, 시도 하나 끝날 때마다 즉시 기록하고, `unconfirmed`→`confirmed` 승격은 기존 행을 고치지 않고 새 행을 추가(재현 2~3회 확인 후)한다.

**실제로 검증됨** — `evidence/evidence.csv`에 있는 6행은 injection-agent를
vulnapp `/search`, `/lookup`에 실제로 돌려서 시도마다 즉시 기록한 결과다
(baseline→attack→control→재현확인→음성대조군 2건). `confirmed_summary.py`를
돌리면 unconfirmed 5건은 걸러지고 confirmed 1건만 나온다 — 실제로 확인함.

> **상태판(Notion) 연동은 아직 없다.** 실제 Notion 페이지/DB ID가 없어서
> 임의로 만들지 않았다 — ID가 정해지면 연동한다. 그 전까지는 `status` 컬럼과
> git 커밋 로그가 상태판 역할을 한다 (`evidence/README.md` 참고).

## 다른 저장소와의 관계

이 저장소는 팀 전체 프로젝트의 **인프라 슬라이스만** 담는다. `CLAUDE.md`의
라우팅 표가 가리키는 `.claude/agents/recon-agent.md`, `injection-agent.md`,
`access-control-agent.md` 등 실제 agent 정의 파일은 여기 없고, 통합 저장소
[`SECURITY-1TEAM-Orchestrator-chain`](https://github.com/chhhd/SECURITY-1TEAM-Orchestrator-chain)에
있다. 이 저장소의 경로 구조는 그 통합본과 그대로 맞아떨어지도록 맞춰뒀다
(`.claude/agents/` 아래에 두면 그대로 합쳐짐).

## dast-harness와의 관계 (틀 vs 내구성)

이 저장소의 `CLAUDE.md`가 정의하는 건 **오케스트레이션의 틀** — 어떤 신호에
어떤 agent를 라우팅할지, 언제 멈출지, 같은 걸 두 번 검사하지 않는 법, 시도를
어떻게 기록할지다. 이 틀이 실제로 안전하고 일관되게 동작하도록 하는
**실행 내구성**(공용 결과 계약, HTTP 요청 통제, 대상 인증 안전장치)은
자체 구현하지 않고 [`dast-harness`](https://github.com/moovingGun/dast-harness)를
**git submodule로 pull-only 연결**해서 가져온다.

```bash
git clone --recurse-submodules https://github.com/chhhd/1TEAM-Main-Orchestration-Project-Infrastructure.git
# 이미 클론했다면
git submodule update --init --recursive
```

두 문서가 상충하면 `dast-harness/AGENT_GUIDE.md`·`dast-harness/CLAUDE.md`가
우선한다 (이 저장소 `CLAUDE.md` 최상단에 명시). `dast-harness/` 안 코드는 여기서
직접 고치지 않는다 — 내구성 쪽 변경은 항상 원본 저장소에서 이뤄지고, 이
저장소에는 submodule 커밋 포인터(`git submodule status`로 확인)만 갱신된다.

## 실행

```bash
python3 vulnapp/app.py &     # 127.0.0.1:5000
```

`docs/orchestration-flow-verification.md`의 재현 커맨드로 SQLi/IDOR/무인증
취약점을 직접 확인할 수 있다.

## 알아둘 것

- `.claude/settings.json`에는 hooks 설정이 없다 — 로깅/hooks는 팀원5(박정근)
  담당이며 통합 저장소에만 있다. 이 저장소만 단독으로 열면 `SubagentStop`
  자동 기록은 동작하지 않는다.
- `vulnapp/`은 의도적으로 취약하게 만든 연습용 앱이다. `127.0.0.1` 바인딩을
  벗어나거나 실제 배포 환경에 올리지 않는다.
- `dast-harness/`는 git submodule이라 일반 clone만으로는 비어 있다. 위
  "dast-harness와의 관계" 절의 `--recurse-submodules` / `submodule update`를
  먼저 돌려야 내용이 채워진다.
