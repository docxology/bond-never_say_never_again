"""Legacy asset migration — remastered intel for the REMOUNT engine.

REMOUNT's third concept is *legacy asset migration*: when a prior operation is
re-opened, its intelligence assets (intel dossiers, captured gadgets, weapons
registries) must be carried forward, re-fingerprinted, and verified before the
remount consumes them. This module models that lifecycle deterministically:

* :class:`LegacyAsset` — an immutable intelligence record carrying a declared
  integrity fingerprint for its ``content``.
* :func:`verify` — recompute the SHA-256 fingerprint and compare it against the
  declared one; ``None`` (un-scanned) records are treated as self-consistent.
* :func:`remaster` — migrate a source asset into a new version (content,
  optional reclassification/re-typing) with a freshly computed fingerprint,
  preserving the source lineage.
* :class:`AssetCatalog` — an ordered registry over a set of legacy assets with
  aggregate integrity, per-kind counts, and batch migration.

The module is pure (stdlib only): no ``infrastructure`` imports, no RNG, and
the fingerprints are fully deterministic so a remount can be audited offline.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass

__all__ = [
    "AssetCatalog",
    "AssetIntegrityError",
    "LegacyAsset",
    "MigratedAsset",
    "compute_integrity",
    "remaster",
    "verify",
]


class AssetIntegrityError(ValueError):
    """Raised when a legacy asset fails its declared integrity check."""


def canonical_bytes(content: str) -> bytes:
    """Return the canonical bytes for fingerprinting (NFC-normalized UTF-8)."""
    normalized = unicodedata.normalize("NFC", content)
    return normalized.encode("utf-8")


def compute_integrity(content: str) -> str:
    """Return the SHA-256 hex fingerprint of ``content`` (deterministic)."""
    return hashlib.sha256(canonical_bytes(content)).hexdigest()


@dataclass(frozen=True)
class LegacyAsset:
    """An immutable legacy intelligence asset.

    ``integrity`` holds the fingerprint claimed for ``content`` at record
    time. When ``None`` the record is un-scanned and treated as self-
    consistent (see :func:`verify`).

    Attributes:
        id: Stable asset identifier (e.g. ``intel-OP-01``).
        kind: Asset family, e.g. ``intel``, ``gadget``, ``weapon``.
        classification: Handling classification, e.g. ``CONFIDENTIAL``.
        content: The payload (intel text, registry dump, dossier).
        version: Migration version (>= 1).
        integrity: Declared SHA-256 fingerprint, or ``None`` when un-scanned.
    """

    id: str
    kind: str
    classification: str
    content: str
    version: int = 1
    integrity: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("LegacyAsset.id must be a non-empty string")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("LegacyAsset.kind must be a non-empty string")
        if not isinstance(self.classification, str) or not self.classification.strip():
            raise ValueError("LegacyAsset.classification must be a non-empty string")
        if not isinstance(self.content, str):
            raise ValueError("LegacyAsset.content must be a string")
        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
        ):
            raise ValueError("LegacyAsset.version must be a positive integer")

    @property
    def canonical_integrity(self) -> str:
        """The SHA-256 fingerprint recomputed from the current ``content``."""
        return compute_integrity(self.content)


def verify(asset: LegacyAsset) -> bool:
    """Return True when the asset's declared integrity matches its content.

    An un-scanned record (``integrity is None``) is considered self-consistent.
    """
    if asset.integrity is None:
        return True
    return asset.canonical_integrity == asset.integrity


@dataclass(frozen=True)
class MigratedAsset:
    """The result of migrating one legacy asset.

    ``asset`` is the remastered record (version + 1); ``source_id`` and
    ``source_classification`` preserve lineage back to the original.
    """

    asset: LegacyAsset
    source_id: str
    source_classification: str

    @property
    def verified(self) -> bool:
        """True when the migrated record's fingerprint is self-consistent."""
        return verify(self.asset)


def remaster(
    source: LegacyAsset,
    *,
    new_content: str,
    classification: str | None = None,
    kind: str | None = None,
    require_intact: bool = True,
) -> MigratedAsset:
    """Migrate ``source`` into a remastered record with a fresh fingerprint.

    Args:
        source: The legacy asset to migrate.
        new_content: The remastered payload for the migrated record.
        classification: Optional reclassification (defaults to source's).
        kind: Optional re-typing (defaults to source's).
        require_intact: When True, raise :class:`AssetIntegrityError` if the
            source fails its declared integrity check before migration.

    Returns:
        A :class:`MigratedAsset` whose ``asset`` has ``version = source.version + 1``.
    """
    if require_intact and not verify(source):
        raise AssetIntegrityError(
            f"asset {source.id!r} failed integrity verification; migration aborted"
        )
    migrated = LegacyAsset(
        id=source.id,
        kind=source.kind if kind is None else kind,
        classification=source.classification
        if classification is None
        else classification,
        content=new_content,
        version=source.version + 1,
        integrity=compute_integrity(new_content),
    )
    return MigratedAsset(
        asset=migrated, source_id=source.id, source_classification=source.classification
    )


@dataclass(frozen=True)
class MigrationBatch:
    """Aggregate result of migrating a catalog of assets."""

    assets: tuple[MigratedAsset, ...]

    @property
    def verified(self) -> bool:
        """True when every migrated record is fingerprint-consistent."""
        return all(record.verified for record in self.assets)

    def counts_by_kind(self) -> dict[str, int]:
        """Count of migrated records per asset kind, in sorted kind order."""
        counts: dict[str, int] = {}
        for record in self.assets:
            counts[record.asset.kind] = counts.get(record.asset.kind, 0) + 1
        return {kind: counts[kind] for kind in sorted(counts)}


class AssetCatalog:
    """Ordered registry of legacy assets with aggregate integrity and migration."""

    def __init__(
        self, assets: list[LegacyAsset] | tuple[LegacyAsset, ...] = ()
    ) -> None:
        self._assets: dict[str, LegacyAsset] = {}
        for asset in assets:
            self._register(asset)

    def _register(self, asset: LegacyAsset) -> None:
        if asset.id in self._assets:
            raise ValueError(f"duplicate asset id in catalog: {asset.id!r}")
        self._assets[asset.id] = asset

    def add(self, asset: LegacyAsset) -> None:
        """Add a legacy asset to the catalog."""
        self._register(asset)

    def get(self, asset_id: str) -> LegacyAsset:
        """Return the asset with ``asset_id`` or raise ``KeyError``."""
        try:
            return self._assets[asset_id]
        except KeyError:
            raise KeyError(f"no legacy asset with id {asset_id!r}") from None

    def __contains__(self, asset_id: object) -> bool:
        return asset_id in self._assets

    def __len__(self) -> int:
        return len(self._assets)

    def __iter__(self):
        return iter(self._assets.values())

    @property
    def assets(self) -> tuple[LegacyAsset, ...]:
        """All catalog assets, in insertion order."""
        return tuple(self._assets.values())

    def verify_all(self) -> bool:
        """True when every catalog asset passes its declared integrity check."""
        return all(verify(asset) for asset in self._assets.values())

    def counts_by_kind(self) -> dict[str, int]:
        """Count of assets per kind, in sorted kind order."""
        counts: dict[str, int] = {}
        for asset in self._assets.values():
            counts[asset.kind] = counts.get(asset.kind, 0) + 1
        return {kind: counts[kind] for kind in sorted(counts)}

    def stable_integrity(self) -> str:
        """A catalog-wide fingerprint over (id, kind, integrity) rows, sorted."""
        rows = sorted(
            (a.id, a.kind, a.canonical_integrity) for a in self._assets.values()
        )
        payload = "|".join(f"{aid}:{kind}:{digest}" for aid, kind, digest in rows)
        return compute_integrity(payload)

    def migrate(
        self,
        new_contents: dict[str, str],
        *,
        classification: str | None = None,
        require_intact: bool = True,
    ) -> MigrationBatch:
        """Migrate the assets named in ``new_contents`` and return a batch.

        Assets whose ids are absent from ``new_contents`` are skipped. Raises
        ``AssetIntegrityError`` via :func:`remaster` when ``require_intact``.
        """
        batch: list[MigratedAsset] = []
        for asset_id in self._assets:
            if asset_id not in new_contents:
                continue
            batch.append(
                remaster(
                    self._assets[asset_id],
                    new_content=new_contents[asset_id],
                    classification=classification,
                    require_intact=require_intact,
                )
            )
        return MigrationBatch(assets=tuple(batch))
