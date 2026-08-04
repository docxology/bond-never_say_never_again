"""Tests for the legacy asset migration module (legacy_assets.py).

Real deterministic data: SHA-256 fingerprinting, tamper detection, migration
batching, and catalog aggregation. No mocks.
"""

from __future__ import annotations

import pytest

from never_say_never_again.legacy_assets import (
    AssetCatalog,
    AssetIntegrityError,
    LegacyAsset,
    MigratedAsset,
    MigrationBatch,
    compute_integrity,
    remaster,
    verify,
)


def test_compute_integrity_is_deterministic_and_nfc_stable():
    a = compute_integrity("intel payload")
    b = compute_integrity("intel payload")
    assert a == b
    assert len(a) == 64
    # NFC normalization: canonically-equivalent strings fingerprint identically.
    assert compute_integrity("\u00e9") == compute_integrity("e\u0301")


def test_verify_untampered_and_tampered():
    asset = LegacyAsset(
        id="intel-1",
        kind="intel",
        classification="SECRET",
        content="original dossier",
        integrity=compute_integrity("original dossier"),
    )
    assert verify(asset) is True

    forged = LegacyAsset(
        id="intel-1",
        kind="intel",
        classification="SECRET",
        content="altered dossier",
        integrity=compute_integrity("original dossier"),
    )
    assert verify(forged) is False


def test_verify_unscanned_is_self_consistent():
    asset = LegacyAsset(
        id="intel-2", kind="intel", classification="SECRET", content="x", integrity=None
    )
    assert verify(asset) is True
    assert asset.canonical_integrity == compute_integrity("x")


def test_remaster_bumps_version_and_refingerprints():
    source = LegacyAsset(
        id="intel-3",
        kind="intel",
        classification="SECRET",
        content="old",
        version=2,
        integrity=compute_integrity("old"),
    )
    migrated = remaster(source, new_content="new")
    assert isinstance(migrated, MigratedAsset)
    assert migrated.asset.version == 3
    assert migrated.asset.content == "new"
    assert migrated.asset.integrity == compute_integrity("new")
    assert migrated.verified is True
    assert migrated.source_id == "intel-3"
    assert migrated.source_classification == "SECRET"


def test_remaster_reclassifies_and_retypes():
    source = LegacyAsset(
        id="g-1", kind="gadget", classification="CONFIDENTIAL", content="rig"
    )
    migrated = remaster(
        source, new_content="rig v2", classification="TOP_SECRET", kind="weapon"
    )
    assert migrated.asset.classification == "TOP_SECRET"
    assert migrated.asset.kind == "weapon"


def test_remaster_rejects_tampered_source_when_required():
    tampered = LegacyAsset(
        id="t-1",
        kind="intel",
        classification="SECRET",
        content="altered",
        integrity=compute_integrity("original"),
    )
    with pytest.raises(AssetIntegrityError):
        remaster(tampered, new_content="x", require_intact=True)
    # require_intact=False permits migration of a questionable source.
    migrated = remaster(tampered, new_content="x", require_intact=False)
    assert migrated.verified is True


def test_catalog_duplicate_rejected():
    catalog = AssetCatalog()
    catalog.add(LegacyAsset(id="a", kind="intel", classification="C", content="x"))
    with pytest.raises(ValueError):
        catalog.add(LegacyAsset(id="a", kind="intel", classification="C", content="y"))


def test_catalog_lookup_and_membership():
    catalog = AssetCatalog(
        [LegacyAsset(id="a", kind="intel", classification="C", content="x")]
    )
    assert "a" in catalog
    assert len(catalog) == 1
    assert catalog.get("a").id == "a"
    with pytest.raises(KeyError):
        catalog.get("missing")


def test_catalog_counts_by_kind_sorted():
    catalog = AssetCatalog(
        [
            LegacyAsset(id="i1", kind="intel", classification="C", content="x"),
            LegacyAsset(id="i2", kind="intel", classification="C", content="y"),
            LegacyAsset(id="g1", kind="gadget", classification="C", content="z"),
        ]
    )
    assert catalog.counts_by_kind() == {"gadget": 1, "intel": 2}


def test_catalog_verify_all_and_stable_integrity():
    catalog = AssetCatalog(
        [LegacyAsset(id="a", kind="intel", classification="C", content="x")]
    )
    assert catalog.verify_all() is True
    assert len(catalog.stable_integrity()) == 64
    another = AssetCatalog(
        [LegacyAsset(id="a", kind="intel", classification="C", content="x")]
    )
    assert catalog.stable_integrity() == another.stable_integrity()


def test_catalog_migrate_skips_unspecified_assets():
    catalog = AssetCatalog(
        [
            LegacyAsset(id="a", kind="intel", classification="C", content="x"),
            LegacyAsset(id="b", kind="gadget", classification="C", content="y"),
        ]
    )
    batch = catalog.migrate({"a": "new-a"})
    assert isinstance(batch, MigrationBatch)
    assert len(batch.assets) == 1
    assert batch.assets[0].asset.id == "a"
    assert batch.assets[0].asset.version == 2


def test_migration_batch_counts_and_verified():
    catalog = AssetCatalog(
        [
            LegacyAsset(id="i1", kind="intel", classification="C", content="x"),
            LegacyAsset(id="i2", kind="intel", classification="C", content="y"),
            LegacyAsset(id="g1", kind="gadget", classification="C", content="z"),
        ]
    )
    batch = catalog.migrate({"i1": "nx", "i2": "ny", "g1": "nz"})
    assert batch.verified is True
    assert batch.counts_by_kind() == {"gadget": 1, "intel": 2}


def test_legacy_asset_validation():
    with pytest.raises(ValueError):
        LegacyAsset(id="", kind="intel", classification="C", content="x")
    with pytest.raises(ValueError):
        LegacyAsset(id="a", kind="", classification="C", content="x")
    with pytest.raises(ValueError):
        LegacyAsset(id="a", kind="intel", classification="", content="x")
    with pytest.raises(ValueError):
        LegacyAsset(id="a", kind="intel", classification="C", content=123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        LegacyAsset(id="a", kind="intel", classification="C", content="x", version=0)
