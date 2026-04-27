import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from src.database import init_db


@pytest.fixture()
def isolated_db(monkeypatch):
    case_dir = Path(__file__).parent / ".tmp_data" / uuid4().hex
    case_dir.mkdir(parents=True, exist_ok=True)

    db_path = case_dir / "medicines.db"
    seed_path = case_dir / "catalog_seed.json"
    seed_data = [
        {
            "barcode": "seed-001",
            "name": "Seed Medicine",
            "manufacturer": "Seed Factory",
            "spec": "10ml",
            "form": "Liquid",
            "unit": "bottle",
            "tags": "cold fever",
            "indications": "Seed indication",
            "std_usage": "Seed usage",
            "adverse_reactions": "",
            "contraindications": "Seed contraindication",
            "precautions": "",
            "pregnancy_lactation_use": "",
            "child_use": "Ask a doctor",
            "elderly_use": "",
            "is_standard": 1,
            "created_at": "2026-01-01 00:00:00",
        }
    ]
    seed_path.write_text(json.dumps(seed_data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setenv("HOMEMEDS_DB_PATH", str(db_path))
    monkeypatch.setenv("HOMEMEDS_SEED_FILE", str(seed_path))

    init_db()
    yield {"db_path": db_path, "seed_path": seed_path}

    shutil.rmtree(case_dir, ignore_errors=True)
