[English](../../en/methods/responses.md) | [한국어](responses.md)

# Responses 메서드

이 문서는 `oauth-codex`의 `responses` 런타임 메서드를 설명합니다.

## Method Summary

| 메서드 | 지원 여부 | 비고 |
|---|---|---|
| `responses.create(...)` | 지원 | 비스트림/스트림 생성 진입점 |
| `responses.stream(...)` | 지원 | `create(stream=True, ...)` 편의 래퍼 |
| `responses.input_tokens.count(...)` | 지원 | 입력 토큰 수 계산 |
| `responses.retrieve(...)` | 미지원 | `NotSupportedError(code="not_supported")` |
| `responses.cancel(...)` | 미지원 | `NotSupportedError(code="not_supported")` |
| `responses.delete(...)` | 미지원 | `NotSupportedError(code="not_supported")` |
| `responses.compact(...)` | 미지원 | `NotSupportedError(code="not_supported")` |
| `responses.parse(...)` | 미지원 | `NotSupportedError(code="not_supported")` |
| `responses.input_items.list(...)` | 미지원 | `NotSupportedError(code="not_supported")` |

## `responses.create`

### Sync / Async / Module-level Signatures

```python
# sync client
client.responses.create(
    *,
    model: str,
    input: str | dict | list[dict] | None = None,
    messages: list[dict] | None = None,
    tools: list | None = None,
    tool_results: list | None = None,
    response_format: dict | None = None,
    tool_choice: str | dict | None = None,
    strict_output: bool = False,
    store: bool = False,
    reasoning: dict | None = None,
    previous_response_id: str | None = None,
    instructions: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    metadata: dict | None = None,
    include: list[str] | None = None,
    max_tool_calls: int | None = None,
    parallel_tool_calls: bool | None = None,
    truncation: Literal["auto", "disabled"] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict | None = None,
    extra_body: dict | None = None,
    service_tier: str | None = None,
    stream: bool = False,
    validation_mode: Literal["warn", "error", "ignore"] | None = None,
    **extra,
) -> Response | Iterator[StreamEvent]

# async client
await client.responses.create(
    *,
    model: str,
    input: str | dict | list[dict] | None = None,
    messages: list[dict] | None = None,
    tools: list | None = None,
    tool_results: list | None = None,
    response_format: dict | None = None,
    tool_choice: str | dict | None = None,
    strict_output: bool = False,
    store: bool = False,
    reasoning: dict | None = None,
    previous_response_id: str | None = None,
    instructions: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    metadata: dict | None = None,
    include: list[str] | None = None,
    max_tool_calls: int | None = None,
    parallel_tool_calls: bool | None = None,
    truncation: Literal["auto", "disabled"] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict | None = None,
    extra_body: dict | None = None,
    service_tier: str | None = None,
    stream: bool = False,
    validation_mode: Literal["warn", "error", "ignore"] | None = None,
    **extra,
) -> Response | AsyncIterator[StreamEvent]

# module-level
oauth_codex.responses.create(...)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `model` | `str` | 예 | - | 모델 ID |
| `input` | `str | dict | list[dict]` | 예 (`messages` 대체 가능) | `None` | `messages`와 동시 사용 불가, list면 비어 있으면 안 됨 |
| `messages` | `list[dict]` | 예 (`input` 대체 가능) | `None` | input alias, 비어 있으면 안 됨 |
| `tools` | `list` | 아니오 | `None` | Responses tool schema로 정규화 |
| `tool_results` | `list[ToolResult|dict]` | 아니오 | `None` | continuation item으로 변환 |
| `response_format` | `dict` | 아니오 | `None` | payload `text.format`로 매핑 |
| `tool_choice` | `str | dict` | 아니오 | `None` | 그대로 전달 |
| `strict_output` | `bool` | 아니오 | `False` | tool schema 변환에 영향 |
| `store` | `bool` | 아니오 | `False` | Codex profile에서 `store_behavior` 적용 |
| `reasoning` | `dict` | 아니오 | `None` | `effort`는 문자열, `summary`는 문자열/불리언 |
| `previous_response_id` | `str` | 아니오 | `None` | Codex profile 로컬 continuity 에뮬레이션 |
| `instructions` | `str` | 아니오 | 자동 | 첫 system message 또는 기본 fallback |
| `temperature` | `float` | 아니오 | `None` | `[0, 2]` 범위 |
| `top_p` | `float` | 아니오 | `None` | `(0, 1]` 범위 |
| `max_output_tokens` | `int` | 아니오 | `None` | 양의 정수 |
| `metadata` | `dict` | 아니오 | `None` | dict 필요 |
| `include` | `list[str]` | 아니오 | `None` | 문자열 리스트 필요 |
| `max_tool_calls` | `int` | 아니오 | `None` | 양의 정수 |
| `parallel_tool_calls` | `bool` | 아니오 | `None` | bool 필요 |
| `truncation` | `"auto" | "disabled"` | 아니오 | `None` | enum 검증 |
| `extra_headers` | `dict[str, str]` | 아니오 | `None` | 보호 헤더 override 차단 |
| `extra_query` | `dict` | 아니오 | `None` | query params로 병합 |
| `extra_body` | `dict` | 아니오 | `None` | JSON body 마지막 병합(override 가능) |
| `service_tier` | `str` | 아니오 | `None` | 현재 무시(검증 모드 따라 경고/에러) |
| `stream` | `bool` | 아니오 | `False` | `True`면 스트림 이벤트 iterator 반환 |
| `validation_mode` | `"warn" | "error" | "ignore"` | 아니오 | client 기본값 | 검증 경고/에러 정책 제어 |

### Return Shape

#### Non-stream mode (`stream=False`)

`oauth_codex.types.responses.Response` 반환:

- `id: str`
- `output: list[dict]`
- `output_text: str`
- `usage: TokenUsage | None`
- `error: dict | None`
- `reasoning_summary: str | None`
- `reasoning_items: list[dict]`
- `encrypted_reasoning_content: str | None`
- `finish_reason: str | None`
- `previous_response_id: str | None`
- `raw_response: dict | None`

#### Stream mode (`stream=True`)

정규화된 stream event iterator 반환:

- `response_started`
- `text_delta`
- `reasoning_delta`
- `reasoning_done`
- `tool_call_started`
- `tool_call_arguments_delta`
- `tool_call_done`
- `usage`
- `response_completed`
- `error`
- `done`

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `AuthRequiredError` | OAuth credential 없음/refresh 실패 |
| `SDKRequestError` | HTTP/provider 실패, stream 에러, JSON shape 오류 |
| `ParameterValidationError` | `validation_mode="error"`에서 파라미터 검증 실패 |
| `ContinuityError` | `previous_response_id` 연속성 불일치 |
| `ValueError` | `input/messages` 조합 오류 또는 빈 list 입력 |
| `TypeError` | 지원하지 않는 입력 타입 |

### Behavior Notes

- Codex profile(`backend-api/codex`)에서 continuity 정보를 로컬에 저장합니다.
- Codex profile + `store=True`:
  - `store_behavior="auto_disable"` -> `store=False`로 변환
  - `store_behavior="error"` -> 검증 예외
  - `store_behavior="passthrough"` -> `store=True` 유지
- `extra_body`는 마지막에 merge되어 기존 payload key를 덮어쓸 수 있습니다.

### Runnable Usage Snippets

#### Sync

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
resp = client.responses.create(
    model="gpt-5.3-codex",
    input="Return JSON with ok=true",
    response_format={"type": "json_object"},
    reasoning={"effort": "low"},
)
print(resp.output_text)
```

#### Async

```python
import asyncio
from oauth_codex import AsyncOAuthCodexClient


async def main() -> None:
    client = AsyncOAuthCodexClient()
    resp = await client.responses.create(model="gpt-5.3-codex", input="hello")
    print(resp.output_text)


asyncio.run(main())
```

#### Module-level

```python
import oauth_codex

resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```

#### Streaming

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
for event in client.responses.stream(model="gpt-5.3-codex", input="stream this"):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="", flush=True)
```

### Pitfalls / Troubleshooting

- `input`과 `messages`를 동시에 넘기면 안 됩니다.
- 엄격 검증이 필요하면 `validation_mode="error"`를 사용하세요.
- `extra_headers`로 보호 헤더(`Authorization`, `ChatGPT-Account-ID`, `Content-Type`)는 덮어쓸 수 없습니다.

## `responses.stream`

### Sync / Async / Module-level Signatures

```python
# sync client
client.responses.stream(
    *,
    model: str,
    input: str | dict | list[dict] | None = None,
    messages: list[dict] | None = None,
    tools: list | None = None,
    tool_results: list | None = None,
    response_format: dict | None = None,
    tool_choice: str | dict | None = None,
    strict_output: bool = False,
    store: bool = False,
    reasoning: dict | None = None,
    previous_response_id: str | None = None,
    instructions: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    metadata: dict | None = None,
    include: list[str] | None = None,
    max_tool_calls: int | None = None,
    parallel_tool_calls: bool | None = None,
    truncation: Literal["auto", "disabled"] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict | None = None,
    extra_body: dict | None = None,
    service_tier: str | None = None,
    validation_mode: Literal["warn", "error", "ignore"] | None = None,
    **extra,
) -> Iterator[StreamEvent]

# async client
await client.responses.stream(
    *,
    model: str,
    input: str | dict | list[dict] | None = None,
    messages: list[dict] | None = None,
    tools: list | None = None,
    tool_results: list | None = None,
    response_format: dict | None = None,
    tool_choice: str | dict | None = None,
    strict_output: bool = False,
    store: bool = False,
    reasoning: dict | None = None,
    previous_response_id: str | None = None,
    instructions: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    metadata: dict | None = None,
    include: list[str] | None = None,
    max_tool_calls: int | None = None,
    parallel_tool_calls: bool | None = None,
    truncation: Literal["auto", "disabled"] | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict | None = None,
    extra_body: dict | None = None,
    service_tier: str | None = None,
    validation_mode: Literal["warn", "error", "ignore"] | None = None,
    **extra,
) -> AsyncIterator[StreamEvent]

# module-level
oauth_codex.responses.stream(...)
```

### Parameters

- `responses.create(...)`와 동일하며 `stream=True`가 고정입니다.

### Return Shape

- `responses.create(stream=True, ...)`와 동일한 stream event iterator.

### Error Cases

- `responses.create(stream=True, ...)`와 동일.

### Behavior Notes

- 내부적으로 `create(stream=True, ...)` 호출 편의 메서드입니다.

### Runnable Usage Snippets

```python
for event in client.responses.stream(model="gpt-5.3-codex", input="hello"):
    if event.type == "text_delta":
        print(event.delta)
```

### Pitfalls / Troubleshooting

- 최종 텍스트가 필요하면 `text_delta`를 누적하거나 비스트림 `create`를 사용하세요.

## `responses.input_tokens.count`

### Sync / Async / Module-level Signatures

```python
# sync client
client.responses.input_tokens.count(*, input, model: str | None = None, tools: list | None = None)

# async client
await client.responses.input_tokens.count(*, input, model: str | None = None, tools: list | None = None)

# module-level
oauth_codex.responses.input_tokens.count(...)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `input` | `str | dict | list[dict]` | 예 | - | responses input item으로 정규화 |
| `model` | `str | None` | 아니오 | `None` | 미지정 시 래퍼는 빈 문자열 전송 |
| `tools` | `list | None` | 아니오 | `None` | tool schema 정규화 |

### Return Shape

`InputTokenCountResponse` 반환:

- `input_tokens: int`
- `cached_tokens: int | None`
- `total_tokens: int | None`

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | endpoint 실패 또는 malformed token-count 응답 |
| `ValueError` | input shape 오류 |

### Behavior Notes

- endpoint 경로 `/responses/input_tokens` 사용.
- 응답에 `input_tokens`가 없으면 provider code `invalid_input_tokens_response`로 `SDKRequestError` 발생.

### Runnable Usage Snippets

```python
out = client.responses.input_tokens.count(
    model="gpt-5.3-codex",
    input="Count my tokens",
)
print(out.input_tokens, out.cached_tokens, out.total_tokens)
```

### Pitfalls / Troubleshooting

- `cached_tokens`, `total_tokens`는 optional field로 처리하세요.

## `responses` 미지원 메서드

다음 메서드는 구조 호환성 용도로만 존재하며 런타임은 미지원입니다.

- `responses.retrieve`
- `responses.cancel`
- `responses.delete`
- `responses.compact`
- `responses.parse`
- `responses.input_items.list`

모두 아래 예외를 발생시킵니다.

```python
NotSupportedError(code="not_supported")
```
