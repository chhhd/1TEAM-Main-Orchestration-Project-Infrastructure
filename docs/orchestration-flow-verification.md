# Orchestration Flow Verification

목적: "메인 세션이 subagent 결과(Evidence)를 받아 다음 subagent를 호출하는 흐름"이
설계 문서가 아니라 실제로 동작하는지 확인. 아래는 `vulnapp/app.py`
(`127.0.0.1:5000`)를 대상으로 한 실측 로그다 — 시뮬레이션이 아니라 각 단계가
실제 subagent 호출과 실제 HTTP 요청으로 이루어졌다.

## 체인

```
1. recon-agent 호출 (foreground)
   ↓ Attack Surface 테이블 반환
2. 오케스트레이터가 CLAUDE.md 라우팅 표에 따라 분기 결정
   ↓ (동시에 두 subagent 호출, background)
3a. injection-agent 호출 — /search, /lookup만 넘김
3b. access-control-agent 호출 — /user, /admin만 넘김
   ↓ 각각 독립 컨텍스트에서 baseline→attack→control 진행
4. 두 결과가 오케스트레이터로 수렴, 최종 리포트로 병합
```

## 1단계 — recon-agent 결과

```
## Attack Surface

| Method | Path | Params (name:location:type) | Auth observed | Likely class |
|---|---|---|---|---|
| GET | /search | q:query:string | none required (200 unauth) | injection |
| GET | /lookup | q:query:string | none required (200 unauth) | other (negative control) |
| GET | /user | id:query:int; Authorization:header:bearer token | required (401 unauth) | access-control |
| GET | /admin | none | none required (200 unauth) | access-control |
| POST | /upload | file:multipart:file | none required (no auth check in source) | other (no dedicated agent) |
| GET | /uploads/<filename> | filename:path:string | none required | other (no dedicated agent) |
| GET | /fetch | url:query:string | none required (200 unauth) | other (SSRF, no dedicated agent) |
```

recon은 소스(`app.py`)를 직접 읽어 7개 라우트 전부를 링크 크롤링 없이 찾아냈다
(모두 "Not linked from crawl, found via source"로 신고할 필요조차 없이 소스 read
한 번으로 확보 — 실제로는 이게 크롤러 단독보다 안전한 방식임을 보여준다).

## 2단계 — 오케스트레이터 라우팅 결정

`CLAUDE.md` 표에 따라:
- `/search`(query 파라미터) → **injection-agent**
- `/lookup`(같은 모양, 음성 대조군) → injection-agent에게 같이 넘겨 오탐 검증도 시킴
- `/user`(id 참조), `/admin`(role-gated) → **access-control-agent**
- `/upload`, `/fetch` → 전용 agent 없음, 라우팅 표에 없는 클래스라는 걸 그대로 기록하고 넘어감 (임의로 아무 agent에게나 떠넘기지 않음)

두 agent는 서로 겹치지 않는 엔드포인트 집합만 받았다 — 같은 recon 결과를
필터링해서 각자의 스코프만 넘기는 것이 실제로 이루어짐을 확인.

## 3단계 — 병렬 실행 결과 (둘 다 실측, CONFIRMED)

### injection-agent → `/search` SQL Injection (CONFIRMED)

```
baseline: curl "http://127.0.0.1:5000/search?q=report"
  -> 200 {"results":[{id:1,"Q1 report"},{id:2,"Q2 report"}]}

attack:   curl "http://127.0.0.1:5000/search?q=%27"
  -> 500 {"error":"SQL syntax error near '''"}

control:  curl "http://127.0.0.1:5000/search?q=%27--"
  -> 200 {"results":[...전체 3건, 기밀 salary.csv 포함...]}
```
비인증 공격자가 필터를 깨고 원래 노출 안 되는 기밀 레코드까지 덤프 가능함을
3단 증거로 확정. `/lookup`은 같은 방식으로 테스트했으나 SQL 시그니처가 전혀
나오지 않아 음성 대조군으로 정상 분류(오탐 없음).

### access-control-agent → `/user` IDOR + `/admin` 무인증 (둘 다 CONFIRMED)

```
IDOR:
  baseline: alice-token + id=1 -> 200 (자기 프로필)
  attack:   alice-token + id=2 -> 200 (bob 프로필 — 이메일/SSN 뒷자리까지 노출)
  control:  토큰 없음 + id=1   -> 401 (인증은 있으나 소유권 검사만 없음 확정)

Missing-Auth:
  curl -i http://127.0.0.1:5000/admin  (Authorization 헤더 없음)
  -> 200, 전체 사용자 레코드(SSN 포함) 반환 — 소스에 인증 체크 자체가 없음
```

access-control-agent는 자기 스코프(`/search`, `/lookup`, `/upload`, `/fetch`)를
넘지 않고 정확히 넘겨받은 두 엔드포인트만 테스트했고, recon이 `/user`를
"path 참조"가 아니라 "query 참조"로 넘긴 것에 대해 스스로 관측 노트를 남겼다
(§4 참고) — 스코프 경계와 자기 판단 근거 기록이 둘 다 실제로 동작함을 보여준다.

## 4단계 — 체인에서 드러난 실제 개선점

시뮬레이션이 아니라 실제로 돌려봤기 때문에 나온, 설계 문서만으론 안 보였을 결함:

> access-control-agent의 관측: `/user?id=`는 recon이 "path 참조"로 분류했지만
> 실제로는 query 파라미터다. 그래도 access-control-agent는 이걸 스코프 밖으로
> 치지 않고 "진짜 객체 참조니까 처리하되, 분류 기준이 어긋난다"고 스스로 보고했다.

→ 후속 조치: recon-agent의 "Likely class" 분류 기준에서 access-control 후보를
"path 파라미터"로만 한정하지 말고 "query든 path든 객체 id를 가리키는 파라미터"로
넓혀야 한다. (`.claude/agents/recon-agent.md`와 `access-control-checklist` skill —
`SECURITY-1TEAM-Orchestrator-chain` 저장소 — 쪽에서 반영 필요, 이 저장소 범위 밖.)

## 결론

- recon → 라우팅 → 병렬 subagent 호출 → 결과 수렴, 4단계 전부 실측으로 확인됨
- 두 subagent 모두 독립 컨텍스트에서 baseline/attack/control 3단 증거를 실제로
  만들어냈고, 스코프 밖 항목을 침범하지 않았다
- 체인을 실제로 돌려봄으로써 recon의 분류 기준 자체의 결함(query vs path)이
  드러남 — 이게 "이론 설계"와 "실행 검증"의 차이다
