[English](../../en/methods/request_options.md) | [한국어](request_options.md)

# Request Options 심화 가이드

이 문서는 `oauth-codex`에서 request option의 우선순위와 검증 동작을 설명합니다.

## Scope

아래 옵션은 주로 `responses.create(...)`, `responses.stream(...)` 경로에서 적용됩니다.

## Method Summary

| 옵션 | 목적 |
|---|---|
| `extra_headers` | 안전한 요청 헤더 추가 |
| `extra_query` | query string 파라미터 추가 |
| `extra_body` | JSON body 추가 필드 병합 |
| `validation_mode` | warn/error/ignore 검증 정책 선택 |
| `store` + `store_behavior` | Codex profile에서 저장 동작 제어 |
| `service_tier` | 현재 무시되며 검증 정책에 따라 경고/에러 |
| `previous_response_id` | Codex profile 로컬 continuity와 연동 |

## Request Option 처리 순서

Responses 요청 기준 처리 순서는 다음과 같습니다.

1. 핵심 파라미터(`temperature`, `top_p`, `max_output_tokens` 등) 검증/정규화
2. profile과 `store_behavior`를 반영한 `store` 정규화
3. `validation_mode` 기준으로 `extra_headers`, `extra_query`, `extra_body` 정규화
4. 기본 payload 생성
5. `extra_body`를 마지막에 merge (`payload.update(extra_body)`)
6. HTTP 요청 단계에서 `extra_headers`, `extra_query` 적용

## `validation_mode`

### 값

- `"warn"` (기본): 경고만 남기고 계속 진행
- `"error"`: 검증 실패 시 `ParameterValidationError` 발생
- `"ignore"`: 검증 경고/에러를 생략

### 영향을 받는 검증 예시

- `temperature`, `top_p`, `max_output_tokens`, `metadata`, `include` 타입/범위 검증
- `truncation` enum 검증
- `extra_headers` 보호 헤더 검증
- 미지원 extra kwargs 검증
- `service_tier` 무시 경고

## `extra_headers`

### 사용 예

```python
client.responses.create(..., extra_headers={"x-trace-id": "abc123"})
```

### 검증/병합 동작

- `dict[str, str]`이어야 합니다.
- 키는 대소문자 무관하게 보호 헤더 목록과 비교합니다.
- 보호 헤더는 override 차단됩니다.
  - `Authorization`
  - `ChatGPT-Account-ID`
  - `Content-Type`
- 보호 헤더가 아닌 값만 최종 요청 헤더에 병합됩니다.

### 에러/경고 정책

- `warn`: 경고 후 해당 항목 드롭
- `error`: `ParameterValidationError` 발생
- `ignore`: 검증 메시지 생략(정규화 과정에서 값이 드롭될 수 있음)

## `extra_query`

### 사용 예

```python
client.responses.create(..., extra_query={"trace": "1", "debug": "true"})
```

### 검증/병합 동작

- dict 타입이어야 합니다.
- HTTP query params로 병합됩니다.

### 에러/경고 정책

- dict가 아니면 `validation_mode` 정책을 따릅니다.

## `extra_body`

### 사용 예

```python
client.responses.create(..., extra_body={"custom_flag": True})
```

### 검증/병합 동작

- dict 타입이어야 합니다.
- JSON payload 마지막 단계에 merge되어 기존 키를 덮어쓸 수 있습니다.

### 우선순위 규칙

표준 파라미터와 `extra_body`가 같은 키를 설정하면 `extra_body` 값이 우선합니다.

## Codex profile에서 `store`와 `store_behavior`

### 관련 클라이언트 설정

- `store_behavior`는 client 생성자 옵션입니다.
  - `"auto_disable"` (기본)
  - `"error"`
  - `"passthrough"`

### 요청에서 `store=True`일 때 동작

| `store_behavior` | 결과 |
|---|---|
| `auto_disable` | 요청 payload에서 `store=False`로 변경 |
| `error` | 검증 예외 발생 |
| `passthrough` | `store=True` 유지 |

## `service_tier`

- 입력은 받지만 현재 Codex backend에서는 무시됩니다.
- `validation_mode`에 따라 경고 또는 에러가 발생합니다.

## `previous_response_id`

### 동작

- 가능한 경우 upstream payload에 포함됩니다.
- Codex profile에서는 로컬 continuity 호환 로직에 따라 실제 입력이 확장될 수 있고, continuity 기록을 저장합니다.

### 연속성 검증

- 응답의 `previous_response_id`가 요청 값과 불일치하면 `ContinuityError`를 발생시킵니다.

## Sync / Async / Module-level Usage Snippets

### Sync

```python
resp = client.responses.create(
    model="gpt-5.3-codex",
    input="hello",
    extra_headers={"x-trace-id": "abc123"},
    extra_query={"trace": "1"},
    extra_body={"custom_flag": True},
    validation_mode="warn",
)
```

### Async

```python
resp = await async_client.responses.create(
    model="gpt-5.3-codex",
    input="hello",
    extra_body={"custom_flag": True},
)
```

### Module-level

```python
import oauth_codex

resp = oauth_codex.responses.create(
    model="gpt-5.3-codex",
    input="hello",
    extra_query={"trace": "1"},
)
```

## Pitfalls / Troubleshooting

- `service_tier`는 현재 실제 효과가 없습니다.
- `extra_body` merge-last 특성 때문에 핵심 payload 키를 덮어쓸 수 있습니다.
- 검증을 강제하려면 `validation_mode="error"`를 사용하세요.
