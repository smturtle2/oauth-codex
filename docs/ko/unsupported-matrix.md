[English](../en/unsupported-matrix.md) | [한국어](unsupported-matrix.md)

# 미지원 리소스 매트릭스

이 문서는 런타임 지원 리소스와 구조 호환용 리소스를 분리해 보여줍니다.

## 런타임 지원 리소스

| 리소스 | 런타임 상태 | 메서드 문서 |
|---|---|---|
| `responses` | 지원(부분) | [Responses 메서드](methods/responses.md) |
| `responses.input_tokens` | 지원 | [Responses 메서드](methods/responses.md) |
| `files` | 지원 | [Files 메서드](methods/files.md) |
| `vector_stores` | 지원 | [Vector Stores 메서드](methods/vector_stores.md) |
| `vector_stores.files` | 지원(부분) | [Vector Stores 메서드](methods/vector_stores.md) |
| `vector_stores.file_batches` | 지원 | [Vector Stores 메서드](methods/vector_stores.md) |
| `models` | 지원(부분) | [Models 메서드](methods/models.md) |

## 지원 리소스 내부의 미지원 메서드

| 메서드 | 동작 |
|---|---|
| `responses.retrieve` | `NotSupportedError(code="not_supported")` |
| `responses.cancel` | `NotSupportedError(code="not_supported")` |
| `responses.delete` | `NotSupportedError(code="not_supported")` |
| `responses.compact` | `NotSupportedError(code="not_supported")` |
| `responses.parse` | `NotSupportedError(code="not_supported")` |
| `responses.input_items.list` | `NotSupportedError(code="not_supported")` |
| `models.delete` | `NotSupportedError(code="not_supported")` |
| `vector_stores.files.update` | `NotSupportedError(code="not_supported")` |

## 구조 호환용 리소스 (OpenAI 스타일 표면)

다음 리소스 그룹은 표면 호환성을 위해 노출되지만, 현재 런타임 호출은 `NotSupportedError(code="not_supported")`를 발생시킵니다.

- `completions`
- `chat`, `chat.completions.*`
- `embeddings`
- `images`
- `audio.*`
- `moderations`
- `fine_tuning.*`
- `beta.*` (assistants, threads, runs, realtime/chatkit 계열)
- `batches`
- `uploads.*`
- `realtime.*`
- `conversations.*`
- `evals.*`
- `containers.*`
- `videos`
- `webhooks`

## Codex profile 경로 제한 (`not_supported_on_codex_oauth`)

Codex profile base URL(`https://chatgpt.com/backend-api/codex`)에서는:

- direct upstream path로 `/responses`, `/responses/input_tokens`만 허용됩니다.
- 그 외 direct path는 아래 예외를 발생시킵니다.

```python
NotSupportedError(code="not_supported_on_codex_oauth")
```

Codex profile의 vector store/files 지원은 direct backend 동등성이 아니라 local compatibility 에뮬레이션 기반입니다.
