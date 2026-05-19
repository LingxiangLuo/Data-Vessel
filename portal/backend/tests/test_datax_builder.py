"""Tests for app/core/datax_builder.py"""
import pytest
from unittest.mock import MagicMock

from app.core.datax_builder import build_datax_job


def _make_ds(type_="mysql", host="db-host", port=3306, db_name="testdb"):
    ds = MagicMock()
    ds.type = type_
    ds.host = host
    ds.port = port
    ds.database_name = db_name
    ds.username = "user"
    ds.password = "secret"
    return ds


SIMPLE_MAPPING = [
    {"kind": "column", "src": "id", "dst": "id"},
    {"kind": "column", "src": "name", "dst": "user_name"},
]


def test_full_sync_adds_truncate():
    src, dst = _make_ds(), _make_ds()
    job = build_datax_job(
        source_ds=src, source_table="src_table",
        target_ds=dst, target_table="dst_table",
        field_mapping=SIMPLE_MAPPING,
        sync_type="full",
        truncate_before_write=True,
    )
    writer_pre = job["job"]["content"][0]["writer"]["parameter"].get("preSql", [])
    assert any("TRUNCATE" in s for s in writer_pre)


def test_full_sync_no_truncate_when_disabled():
    src, dst = _make_ds(), _make_ds()
    job = build_datax_job(
        source_ds=src, source_table="src_table",
        target_ds=dst, target_table="dst_table",
        field_mapping=SIMPLE_MAPPING,
        sync_type="full",
        truncate_before_write=False,
    )
    writer_pre = job["job"]["content"][0]["writer"]["parameter"].get("preSql", [])
    assert not any("TRUNCATE" in s for s in writer_pre)


def test_constant_field_mapping():
    src, dst = _make_ds(), _make_ds()
    mapping = [
        {"kind": "column",   "src": "id",  "dst": "id"},
        {"kind": "constant", "src": "CN",  "dst": "region"},
    ]
    job = build_datax_job(
        source_ds=src, source_table="t", target_ds=dst, target_table="t",
        field_mapping=mapping,
    )
    reader_cols = job["job"]["content"][0]["reader"]["parameter"]["column"]
    assert any(isinstance(c, dict) and c.get("value") == "CN" for c in reader_cols)


def test_channel_setting():
    src, dst = _make_ds(), _make_ds()
    job = build_datax_job(
        source_ds=src, source_table="t", target_ds=dst, target_table="t",
        field_mapping=SIMPLE_MAPPING,
        channel=5,
    )
    assert job["job"]["setting"]["speed"]["channel"] == 5


def test_empty_mapping_raises():
    src, dst = _make_ds(), _make_ds()
    with pytest.raises(ValueError, match="字段映射不能为空"):
        build_datax_job(
            source_ds=src, source_table="t", target_ds=dst, target_table="t",
            field_mapping=[],
        )


def test_password_masked_by_default():
    src, dst = _make_ds(), _make_ds()
    job = build_datax_job(
        source_ds=src, source_table="t", target_ds=dst, target_table="t",
        field_mapping=SIMPLE_MAPPING,
        mask_password=True,
    )
    reader_pw = job["job"]["content"][0]["reader"]["parameter"]["password"]
    writer_pw = job["job"]["content"][0]["writer"]["parameter"]["password"]
    assert reader_pw == "******"
    assert writer_pw == "******"
