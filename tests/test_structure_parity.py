from __future__ import annotations

import pkgutil

import openai.resources
import oauth_codex.resources


def _resource_modules(package, prefix: str) -> set[str]:
    modules: set[str] = set()
    for mod in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if mod.ispkg:
            continue
        name = mod.name.replace(prefix, "")
        modules.add(name)
    return modules


def test_resource_module_manifest_covers_openai_217() -> None:
    openai_modules = _resource_modules(openai.resources, "openai.resources.")
    oauth_modules = _resource_modules(oauth_codex.resources, "oauth_codex.resources.")

    missing = sorted(openai_modules - oauth_modules)
    assert not missing
