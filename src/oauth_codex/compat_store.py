from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_COMPAT_STORAGE_DIR = Path.home() / ".oauth_codex" / "compat"
COMPAT_STORAGE_DIR_ENV = "CODEX_COMPAT_STORAGE_DIR"

_FILES_INDEX_DEFAULT = {"object": "list", "data": []}
_VECTOR_INDEX_DEFAULT = {"object": "list", "data": []}
_RESPONSES_INDEX_DEFAULT = {"object": "list", "data": []}
_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


def resolve_compat_storage_dir(base_dir: str | Path | None = None) -> Path:
    if base_dir is not None:
        return Path(base_dir).expanduser()
    env_dir = os.getenv(COMPAT_STORAGE_DIR_ENV)
    if env_dir:
        return Path(env_dir).expanduser()
    return DEFAULT_COMPAT_STORAGE_DIR


class LocalCompatStore:
    def __init__(self, *, base_dir: str | Path | None = None) -> None:
        self.base_dir = resolve_compat_storage_dir(base_dir)
        self.files_dir = self.base_dir / "files"
        self.files_blobs_dir = self.files_dir / "blobs"
        self.files_index_path = self.files_dir / "index.json"
        self.vector_stores_dir = self.base_dir / "vector_stores"
        self.vector_stores_index_path = self.vector_stores_dir / "index.json"
        self.responses_dir = self.base_dir / "responses"
        self.responses_index_path = self.responses_dir / "index.json"

    def create_file(
        self,
        *,
        file: Any,
        purpose: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(purpose, str) or not purpose.strip():
            raise ValueError("purpose must be a non-empty string")

        content, filename = self._read_file_bytes(file)
        created_at = int(time.time())
        file_id = f"file_{uuid.uuid4().hex}"
        record: dict[str, Any] = {
            "id": file_id,
            "object": "file",
            "bytes": len(content),
            "created_at": created_at,
            "filename": filename,
            "purpose": purpose,
        }
        for key, value in (metadata or {}).items():
            if key in record:
                continue
            record[key] = value

        self.files_blobs_dir.mkdir(parents=True, exist_ok=True)
        self._atomic_write_bytes(self.files_blobs_dir / f"{file_id}.bin", content)
        index = self._load_files_index()
        index["data"].append(record)
        self._atomic_write_json(self.files_index_path, index)
        return dict(record)

    def get_file(self, file_id: str) -> dict[str, Any]:
        if not isinstance(file_id, str) or not file_id:
            raise ValueError("file_id must be a non-empty string")
        for item in self._load_files_index()["data"]:
            if item.get("id") == file_id:
                return dict(item)
        raise KeyError(f"file {file_id} not found")

    def create_vector_store(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("vector store payload must be a dictionary")
        vector_id = f"vs_{uuid.uuid4().hex}"
        created_at = int(time.time())
        name = payload.get("name")
        if name is not None and not isinstance(name, str):
            raise ValueError("name must be a string")
        metadata = payload.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary")
        file_ids = self._validate_file_ids(payload.get("file_ids"))
        usage_bytes = self._sum_file_bytes(file_ids)
        record: dict[str, Any] = {
            "id": vector_id,
            "object": "vector_store",
            "created_at": created_at,
            "name": name,
            "metadata": dict(metadata or {}),
            "file_ids": file_ids,
            "status": "completed",
            "usage_bytes": usage_bytes,
            "file_counts": self._file_counts(len(file_ids)),
        }
        if "expires_after" in payload:
            record["expires_after"] = payload["expires_after"]
        index = self._load_vector_index()
        index["data"].append(record)
        self._atomic_write_json(self.vector_stores_index_path, index)
        return dict(record)

    def retrieve_vector_store(self, vector_store_id: str) -> dict[str, Any]:
        return dict(self._find_vector_store(vector_store_id)[1])

    def list_vector_stores(self, params: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(params, dict):
            raise ValueError("list params must be a dictionary")
        data = [dict(item) for item in self._load_vector_index()["data"]]
        limit = params.get("limit")
        if limit is None:
            sliced = data
            has_more = False
        else:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive integer")
            sliced = data[:limit]
            has_more = len(data) > limit
        first_id = sliced[0]["id"] if sliced else None
        last_id = sliced[-1]["id"] if sliced else None
        return {
            "object": "list",
            "data": sliced,
            "first_id": first_id,
            "last_id": last_id,
            "has_more": has_more,
        }

    def update_vector_store(self, vector_store_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("vector store payload must be a dictionary")
        index = self._load_vector_index()
        pos, record = self._find_vector_store(vector_store_id, index=index)
        updated = dict(record)
        if "name" in payload:
            name = payload["name"]
            if name is not None and not isinstance(name, str):
                raise ValueError("name must be a string")
            updated["name"] = name
        if "metadata" in payload:
            metadata = payload["metadata"]
            if metadata is not None and not isinstance(metadata, dict):
                raise ValueError("metadata must be a dictionary")
            updated["metadata"] = dict(metadata or {})
        if "file_ids" in payload:
            file_ids = self._validate_file_ids(payload["file_ids"])
            updated["file_ids"] = file_ids
            updated["usage_bytes"] = self._sum_file_bytes(file_ids)
            updated["file_counts"] = self._file_counts(len(file_ids))
        if "expires_after" in payload:
            updated["expires_after"] = payload["expires_after"]
        index["data"][pos] = updated
        self._atomic_write_json(self.vector_stores_index_path, index)
        return dict(updated)

    def delete_vector_store(self, vector_store_id: str) -> dict[str, Any]:
        index = self._load_vector_index()
        pos, _ = self._find_vector_store(vector_store_id, index=index)
        del index["data"][pos]
        self._atomic_write_json(self.vector_stores_index_path, index)
        return {"id": vector_store_id, "object": "vector_store.deleted", "deleted": True}

    def search_vector_store(
        self,
        vector_store_id: str,
        *,
        query: Any,
        max_num_results: Any = 10,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if max_num_results is None:
            max_num_results = 10
        if not isinstance(max_num_results, int) or max_num_results <= 0:
            raise ValueError("max_num_results must be a positive integer")

        record = self.retrieve_vector_store(vector_store_id)
        results: list[dict[str, Any]] = []
        for file_id in record.get("file_ids", []):
            file_meta = self.get_file(file_id)
            text = self._read_file_text(file_id)
            score = self._token_overlap_score(query, text)
            if score <= 0:
                continue
            results.append(
                {
                    "id": f"vsr_{uuid.uuid4().hex}",
                    "object": "vector_store.search_result",
                    "score": score,
                    "file_id": file_id,
                    "filename": file_meta.get("filename"),
                    "content": [{"type": "text", "text": self._snippet(text)}],
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        sliced = results[:max_num_results]
        return {"object": "list", "data": sliced, "has_more": len(results) > max_num_results}

    def get_response_continuity(self, response_id: str) -> dict[str, Any]:
        if not isinstance(response_id, str) or not response_id:
            raise ValueError("response_id must be a non-empty string")
        for item in self._load_responses_index()["data"]:
            if item.get("id") == response_id:
                return dict(item)
        raise KeyError(f"response {response_id} not found")

    def upsert_response_continuity(
        self,
        *,
        response_id: str,
        model: str,
        continuation_input: list[dict[str, Any]],
        previous_response_id: str | None,
        created_at: int | None = None,
    ) -> dict[str, Any]:
        if not isinstance(response_id, str) or not response_id:
            raise ValueError("response_id must be a non-empty string")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if previous_response_id is not None and (
            not isinstance(previous_response_id, str) or not previous_response_id
        ):
            raise ValueError("previous_response_id must be None or a non-empty string")
        if not isinstance(continuation_input, list):
            raise ValueError("continuation_input must be a list of dictionaries")
        normalized_input: list[dict[str, Any]] = []
        for item in continuation_input:
            if not isinstance(item, dict):
                raise ValueError("continuation_input must be a list of dictionaries")
            normalized_input.append(dict(item))

        if created_at is None:
            created_at = int(time.time())
        if not isinstance(created_at, int):
            raise ValueError("created_at must be an integer")

        record = {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "model": model,
            "previous_response_id": previous_response_id,
            "continuation_input": normalized_input,
        }
        index = self._load_responses_index()
        for idx, item in enumerate(index["data"]):
            if item.get("id") == response_id:
                index["data"][idx] = record
                break
        else:
            index["data"].append(record)
        self._atomic_write_json(self.responses_index_path, index)
        return dict(record)

    def _load_files_index(self) -> dict[str, Any]:
        return self._load_index(self.files_index_path, _FILES_INDEX_DEFAULT)

    def _load_vector_index(self) -> dict[str, Any]:
        return self._load_index(self.vector_stores_index_path, _VECTOR_INDEX_DEFAULT)

    def _load_responses_index(self) -> dict[str, Any]:
        return self._load_index(self.responses_index_path, _RESPONSES_INDEX_DEFAULT)

    def _load_index(self, path: Path, default_payload: dict[str, Any]) -> dict[str, Any]:
        if not path.exists():
            return {"object": "list", "data": []}
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return dict(default_payload)
        data = raw.get("data")
        if not isinstance(data, list):
            data = []
        normalized = [item for item in data if isinstance(item, dict)]
        return {"object": "list", "data": normalized}

    def _find_vector_store(
        self,
        vector_store_id: str,
        *,
        index: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        if not isinstance(vector_store_id, str) or not vector_store_id:
            raise ValueError("vector_store_id must be a non-empty string")
        source = index or self._load_vector_index()
        for idx, item in enumerate(source["data"]):
            if item.get("id") == vector_store_id:
                return idx, item
        raise KeyError(f"vector_store {vector_store_id} not found")

    def _validate_file_ids(self, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise ValueError("file_ids must be a list of non-empty strings")
        normalized = list(value)
        for file_id in normalized:
            self.get_file(file_id)
        return normalized

    def _sum_file_bytes(self, file_ids: list[str]) -> int:
        total = 0
        for file_id in file_ids:
            file_meta = self.get_file(file_id)
            raw_bytes = file_meta.get("bytes", 0)
            if isinstance(raw_bytes, int):
                total += raw_bytes
        return total

    def _read_file_text(self, file_id: str) -> str:
        blob_path = self.files_blobs_dir / f"{file_id}.bin"
        if not blob_path.exists():
            raise KeyError(f"file {file_id} not found")
        data = blob_path.read_bytes()
        return data.decode("utf-8", errors="ignore")

    def _read_file_bytes(self, file_obj: Any) -> tuple[bytes, str]:
        if isinstance(file_obj, (bytes, bytearray, memoryview)):
            return bytes(file_obj), "upload.bin"
        if isinstance(file_obj, (str, os.PathLike)):
            path = Path(file_obj).expanduser()
            return path.read_bytes(), path.name
        if hasattr(file_obj, "read"):
            raw = file_obj.read()
            if isinstance(raw, str):
                content = raw.encode("utf-8")
            elif isinstance(raw, (bytes, bytearray, memoryview)):
                content = bytes(raw)
            else:
                raise ValueError("file.read() must return bytes or string")
            raw_name = getattr(file_obj, "name", None)
            if isinstance(raw_name, os.PathLike):
                filename = Path(raw_name).name
            elif isinstance(raw_name, str) and raw_name:
                filename = Path(raw_name).name
            else:
                filename = "upload.bin"
            return content, filename
        raise ValueError("file must be bytes, path-like, or a file-like object")

    def _token_overlap_score(self, query: str, text: str) -> float:
        query_tokens = set(_TOKEN_PATTERN.findall(query.lower()))
        text_tokens = set(_TOKEN_PATTERN.findall(text.lower()))
        if not query_tokens or not text_tokens:
            return 0.0
        overlap = len(query_tokens.intersection(text_tokens))
        return overlap / float(len(query_tokens))

    def _snippet(self, text: str, *, limit: int = 400) -> str:
        normalized = text.strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[:limit]

    def _file_counts(self, completed: int) -> dict[str, int]:
        return {
            "in_progress": 0,
            "completed": completed,
            "failed": 0,
            "cancelled": 0,
            "total": completed,
        }

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, ensure_ascii=True, indent=2)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            delete=False,
        ) as fp:
            tmp_path = Path(fp.name)
            fp.write(serialized)
            fp.flush()
            os.fsync(fp.fileno())
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, path)

    def _atomic_write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(path.parent),
            delete=False,
        ) as fp:
            tmp_path = Path(fp.name)
            fp.write(data)
            fp.flush()
            os.fsync(fp.fileno())
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, path)
