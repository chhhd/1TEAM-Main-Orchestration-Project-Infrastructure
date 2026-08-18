# target-info.md — 허용 대상 범위

`CLAUDE.md`의 §범위 제한(Rules of Engagement)이 참조하는 파일. 여기 명시된
호스트/URL 외에는 스캔·요청하지 않는다.

## 이 저장소의 허용 대상

| 대상 | 용도 | 비고 |
|---|---|---|
| `http://127.0.0.1:5000` | `vulnapp/app.py` — 오케스트레이션 흐름 검증용 로컬 취약 앱 | `/search`, `/lookup`, `/user?id=`, `/admin`, `/upload`, `/fetch?url=` |
| `http://127.0.0.1:8080` | `dast-harness/targets/vulnerable_app/app.py` (submodule) — 스캐너/에이전트 정확도 검증용 통제 취약 타겟 | dast-harness 쪽 `ground_truth.json` 참고 |

## 원칙

- loopback(`127.0.0.1`/`localhost`) 또는 명시적으로 허가된 대상만 스캔한다
  (`dast_harness/safety.py`가 강제하는 것과 같은 경계).
- 이 표에 없는 새 대상을 추가하려면 이 파일을 먼저 갱신하고, 왜 필요한지
  커밋 메시지에 남긴다 — 대상 추가를 코드 변경과 같은 취급으로 리뷰한다.
- 실제 대회/훈련 대상이 정해지면 이 표에 행을 추가하되, 스코프를 넓히는
  변경이므로 팀 확인 후 반영한다.
