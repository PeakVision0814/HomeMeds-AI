# HomeMeds Pro

HomeMeds Pro is a Streamlit-based household medicine inventory manager. It helps you track what medicines you have at home, where they are stored, how much is left, and whether anything is near expiry or already expired.

The app also includes an AI pharmacist assistant that can use your current inventory as context and provide medication-related guidance through DeepSeek or OpenAI-compatible models.

> Chinese documentation is available in [README_zh.md](README_zh.md).

## Features

### Inventory Management

- Track household medicines, quantities, expiry dates, storage locations, and ownership.
- Record medicine usage and automatically deduct stock.
- Correct total remaining stock during inventory checks.
- Highlight expired medicines and show near-expiry warnings.

### Catalog And Data Separation

- Maintain a shared standard medicine catalog through `data/catalog_seed.json`.
- Keep official catalog data separate from user-entered inventory records.
- Protect standard entries from accidental edits during normal use.
- Export updated seed data when maintaining the shared catalog.

### Fast Medicine Entry

- Search by barcode or medicine name.
- Add new medicine records when no catalog match exists.
- Store professional fields such as indications, contraindications, adverse reactions, and special-use notes.

### AI Pharmacist Assistant

- Supports DeepSeek and OpenAI-compatible APIs through the `openai` client.
- Reads the current inventory as context for more relevant answers.
- Uses safety fields such as contraindications and pediatric-use notes when available.

## Project Structure

```text
HomeMeds/
+-- data/
|   +-- catalog_seed.json     # Versioned standard medicine seed data
+-- src/
|   +-- database.py           # SQLite initialization, migration, import/export logic
|   +-- services/             # Business logic and data access
|   |   +-- ai_service.py
|   |   +-- catalog.py
|   |   +-- inventory.py
|   |   +-- members.py
|   |   +-- queries.py
|   +-- views/                # Streamlit UI pages
|       +-- ai_doctor.py
|       +-- catalog.py
|       +-- dashboard.py
|       +-- operations.py
|       +-- sidebar.py
+-- app.py                    # Application entry point
+-- requirements.txt
+-- README.md                 # English documentation
+-- README_zh.md              # Chinese documentation
```

Local runtime database files such as `data/medicines.db` are intentionally not committed.

## Getting Started

### 1. Create A Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize The Database

```powershell
python src/database.py
```

Use the reset option only when you intentionally want to rebuild local data:

```powershell
python src/database.py --reset
```

Back up any important local SQLite data before resetting.

### 3. Run The App

```powershell
streamlit run app.py
```

## Configuration

- API keys are entered through the app sidebar or local environment.
- Do not commit OpenAI, DeepSeek, or other provider keys.
- Keep local SQLite inventory data private and out of version control.

## Development Notes

- Keep Streamlit page rendering in `src/views/`.
- Put reusable business logic in `src/services/`.
- Use `src/database.py` for schema initialization, migration, and seed import/export behavior.
- Match the existing Python style: 4-space indentation, `snake_case`, and imports from `src...`.

There is no committed automated test suite yet. For now, verify changes by running:

```powershell
python src/database.py
streamlit run app.py
```

For database changes, test both a fresh database and an existing database migration path.

## License

MIT License.
