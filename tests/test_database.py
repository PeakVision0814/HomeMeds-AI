import json

from src.database import export_seed_data, get_connection, get_db_path, get_seed_file


def test_init_db_uses_configured_paths_and_imports_seed(isolated_db):
    assert get_db_path() == str(isolated_db["db_path"])
    assert get_seed_file() == str(isolated_db["seed_path"])

    conn = get_connection()
    try:
        catalog_count = conn.execute("SELECT count(*) FROM medicine_catalog").fetchone()[0]
        member_count = conn.execute("SELECT count(*) FROM family_members").fetchone()[0]
        seed_row = conn.execute(
            "SELECT name, is_standard FROM medicine_catalog WHERE barcode = ?",
            ("seed-001",),
        ).fetchone()
    finally:
        conn.close()

    assert catalog_count == 1
    assert member_count == 5
    assert seed_row["name"] == "Seed Medicine"
    assert seed_row["is_standard"] == 1


def test_export_seed_data_writes_only_standard_catalog_items(isolated_db):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO medicine_catalog (
                barcode, name, tags, is_standard
            ) VALUES (?, ?, ?, ?)
            """,
            ("user-001", "User Medicine", "private", 0),
        )
        conn.commit()
    finally:
        conn.close()

    assert export_seed_data() == 1

    exported = json.loads(isolated_db["seed_path"].read_text(encoding="utf-8"))
    assert [item["barcode"] for item in exported] == ["seed-001"]
