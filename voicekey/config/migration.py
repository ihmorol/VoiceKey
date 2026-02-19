"""Versioned config migration registry and execution helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from voicekey.config.schema import CONFIG_VERSION

MigrationHandler = Callable[[dict[str, Any]], dict[str, Any]]


class ConfigMigrationError(RuntimeError):
    """Raised when migration cannot safely advance to target schema version."""


@dataclass(frozen=True)
class MigrationResult:
    """Deterministic migration output metadata."""

    payload: dict[str, Any]
    from_version: int
    to_version: int
    migrated: bool
    warnings: tuple[str, ...] = ()


class MigrationRegistry:
    """Forward-only migration registry keyed by source version."""

    def __init__(self, target_version: int = CONFIG_VERSION) -> None:
        if target_version < 1:
            raise ValueError("target_version must be >= 1")
        self._target_version = target_version
        self._handlers: dict[int, MigrationHandler] = {}

    @property
    def target_version(self) -> int:
        return self._target_version

    def register(self, from_version: int, handler: MigrationHandler) -> None:
        if from_version < 1:
            raise ValueError("from_version must be >= 1")
        if from_version >= self._target_version:
            raise ValueError("from_version must be below target_version")
        if from_version in self._handlers:
            raise ValueError(f"migration already registered for version {from_version}")
        self._handlers[from_version] = handler

    def migrate(self, raw_payload: Mapping[str, Any]) -> MigrationResult:
        payload = deepcopy(dict(raw_payload))
        from_version, warnings = _resolve_source_version(payload)

        if from_version > self._target_version:
            raise ConfigMigrationError(
                "config version is newer than this runtime supports; cannot migrate safely"
            )

        if from_version < 1:
            raise ConfigMigrationError("config version must be >= 1")

        if from_version == self._target_version:
            payload["version"] = self._target_version
            return MigrationResult(
                payload=payload,
                from_version=from_version,
                to_version=self._target_version,
                migrated=False,
                warnings=tuple(warnings),
            )

        current_version = from_version
        while current_version < self._target_version:
            handler = self._handlers.get(current_version)
            if handler is None:
                raise ConfigMigrationError(
                    f"no migration step registered from version {current_version}"
                )

            try:
                migrated_payload = handler(deepcopy(payload))
            except Exception as exc:  # pragma: no cover - defensive conversion
                raise ConfigMigrationError(
                    f"migration step {current_version} failed: {exc}"
                ) from exc

            if not isinstance(migrated_payload, dict):
                raise ConfigMigrationError(
                    f"migration step {current_version} must return a mapping payload"
                )

            next_version = migrated_payload.get("version")
            if not isinstance(next_version, int):
                raise ConfigMigrationError(
                    f"migration step {current_version} did not set integer version"
                )
            if next_version <= current_version:
                raise ConfigMigrationError(
                    f"migration step {current_version} did not advance config version"
                )
            if next_version > self._target_version:
                raise ConfigMigrationError(
                    f"migration step {current_version} advanced past supported target version"
                )

            warnings.append(f"Applied config migration {current_version}->{next_version}.")
            payload = migrated_payload
            current_version = next_version

        return MigrationResult(
            payload=payload,
            from_version=from_version,
            to_version=self._target_version,
            migrated=True,
            warnings=tuple(warnings),
        )


def build_default_registry() -> MigrationRegistry:
    """Build runtime migration registry for currently supported versions."""
    registry = MigrationRegistry(target_version=CONFIG_VERSION)
    registry.register(1, _migrate_v1_to_v2)
    registry.register(2, _migrate_v2_to_v3)
    return registry


def migrate_payload(
    raw_payload: Mapping[str, Any],
    registry: MigrationRegistry | None = None,
) -> MigrationResult:
    """Migrate raw config payload to current target version."""
    active_registry = registry or build_default_registry()
    return active_registry.migrate(raw_payload)


def _resolve_source_version(payload: dict[str, Any]) -> tuple[int, list[str]]:
    version = payload.get("version")
    warnings: list[str] = []
    if version is None:
        warnings.append("Missing config version; assuming version 1 for migration.")
        payload["version"] = 1
        return 1, warnings
    if isinstance(version, bool) or not isinstance(version, int):
        raise ConfigMigrationError("config version must be an integer")
    return version, warnings


def _migrate_v1_to_v2(payload: dict[str, Any]) -> dict[str, Any]:
    payload["version"] = 2
    return payload


def _migrate_v2_to_v3(payload: dict[str, Any]) -> dict[str, Any]:
    payload["version"] = 3
    return payload


__all__ = [
    "ConfigMigrationError",
    "MigrationRegistry",
    "MigrationResult",
    "build_default_registry",
    "migrate_payload",
]
