from datetime import date, timedelta

from src.services.catalog import get_catalog_info, load_catalog_data, upsert_catalog_item
from src.services.inventory import (
    add_inventory_item,
    decrease_quantity,
    delete_medicine,
    update_quantity,
)
from src.services.members import add_member, delete_member, get_all_members
from src.services.queries import (
    filter_by_expiry_status,
    get_dashboard_metrics,
    get_expiry_alerts,
    load_data,
)


def test_catalog_upsert_and_lookup(isolated_db):
    ok = upsert_catalog_item(
        "cat-001",
        "Catalog Medicine",
        "Factory",
        "12 tablets",
        "Tablet",
        "tablet",
        "pain fever",
        "For testing",
        "Once daily",
        "",
        "",
        "",
        "",
        "",
        "",
        0,
    )

    assert ok is True
    found = get_catalog_info("Catalog")
    assert found["barcode"] == "cat-001"
    assert found["tags"] == "pain fever"

    df = load_catalog_data()
    assert set(df["barcode"]) == {"seed-001", "cat-001"}


def test_inventory_lifecycle_and_metrics(isolated_db):
    future = date.today() + timedelta(days=30)

    assert add_inventory_item("seed-001", future, 10, "妈妈", "after meals") is True

    df = load_data()
    med_id = int(df.iloc[0]["id"])
    assert df.iloc[0]["quantity_display"] == "10.0 bottle"

    ok, remaining = decrease_quantity(med_id, 2.5)
    assert ok is True
    assert remaining == 7.5

    assert update_quantity(med_id, 6) is True
    total, expired, soon = get_dashboard_metrics()
    assert (total, expired, soon) == (1, 0, 1)

    assert delete_medicine(med_id) is True
    assert load_data().empty


def test_expiry_status_filters_and_alerts(isolated_db):
    expired = date.today() - timedelta(days=2)
    expiring = date.today() + timedelta(days=30)
    normal = date.today() + timedelta(days=180)

    assert add_inventory_item("seed-001", expired, 1, "妈妈", "") is True
    assert add_inventory_item("seed-001", expiring, 2, "爸爸", "") is True
    assert add_inventory_item("seed-001", normal, 3, "宝宝", "") is True

    df = load_data()
    assert set(df["expiry_status"]) == {"expired", "expiring", "normal"}
    assert set(filter_by_expiry_status(df, "attention")["expiry_status"]) == {"expired", "expiring"}
    assert len(filter_by_expiry_status(df, "expired")) == 1
    assert len(filter_by_expiry_status(df, "expiring")) == 1
    assert len(filter_by_expiry_status(df, "normal")) == 1

    total, expired_count, expiring_count = get_dashboard_metrics()
    assert (total, expired_count, expiring_count) == (3, 1, 1)

    alerts = get_expiry_alerts()
    assert list(alerts["expiry_status"]) == ["expired", "expiring"]


def test_member_lifecycle(isolated_db):
    assert "妈妈" in get_all_members()

    ok, message = add_member("测试成员")
    assert ok is True
    assert message == "添加成功"
    assert "测试成员" in get_all_members()

    ok, message = add_member("测试成员")
    assert ok is False
    assert message == "该成员已存在"

    assert delete_member("测试成员") is True
    assert "测试成员" not in get_all_members()
