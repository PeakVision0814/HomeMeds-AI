# Repository Guidelines

## Project Structure & Module Organization

HomeMeds is a Python Streamlit app. `app.py` is the main entry point and routes the selected sidebar page to modules in `src/views/`. Business logic lives in `src/services/`, while `src/database.py` owns SQLite initialization, schema updates, and seed import/export behavior. Versioned seed data is stored in `data/catalog_seed.json`; local runtime database files such as `data/medicines.db` should not be committed. Keep generated caches such as `__pycache__/` out of changes.

## Build, Test, and Development Commands

Create and activate a virtual environment before installing dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Initialize or update the local database with:

```powershell
python src/database.py
```

Run the app locally with:

```powershell
streamlit run app.py
```

Use `python src/database.py --reset` only when intentionally rebuilding local data, and back up any important SQLite state first.

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation, `snake_case` for functions and variables, and descriptive module names. Keep Streamlit UI rendering in `src/views/`; place reusable data access and mutation logic in `src/services/`. Prefer small functions that return plain Python data structures or pandas DataFrames over embedding database logic directly in view code. Match the existing import style: local modules are imported from `src...`.

## Testing Guidelines

There is no committed test suite yet. For logic changes, add focused tests under a new `tests/` directory using `pytest`, with files named `test_<module>.py`. Until automated tests exist, run `python src/database.py` and `streamlit run app.py`, then manually verify the affected dashboard, operations, catalog, or AI page workflow. For database changes, test both a fresh database and an existing database migration path.

## Commit & Pull Request Guidelines

Recent commits use Conventional Commit-style prefixes with versions, for example `feat(v0.8): ...` and `fix(v0.7.5): ...`. Keep that pattern for new commits when practical. Pull requests should describe the user-visible change, list database or seed-data impacts, mention manual verification steps, and include screenshots for Streamlit UI changes. Link related issues when available and avoid committing secrets, local databases, virtual environments, or generated cache files.

## Security & Configuration Tips

Do not hard-code OpenAI or DeepSeek API keys. Enter keys through the app sidebar or local environment only. Treat user inventory data as private and keep local SQLite files out of version control.
