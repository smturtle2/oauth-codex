from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel as _PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(_PydanticBaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @classmethod
    def from_dict(cls, data: object, *, strict: bool = False) -> Self:
        return cls.model_validate(data, strict=strict)

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        use_api_names: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        return self.model_dump(
            mode=mode,
            by_alias=use_api_names,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def to_json(
        self,
        *,
        indent: int | None = 2,
        use_api_names: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> str:
        return self.model_dump_json(
            indent=indent,
            by_alias=use_api_names,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
