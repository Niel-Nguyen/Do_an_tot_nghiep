# RAG_CHINH Menu App

## Verify end-to-end
- Seed dishes automatically on first run; or manually:
  - `python migrate_dishes.py`
- Import paid bill histories (optional):
  - `python migrate_paid_bill_histories.py`
- Start app:
  - `python app.py`
- Visit:
  - `/` menu should list dishes
  - `/login` face login; register if not recognized
  - `/admin/bills` see in-memory orders
  - `/health` returns JSON `{status: ok, dishes: N}`
- Mark bill paid in `/admin/bill/<user>/<order>/status`; DB reflects in `/api/paid_bills`.

## Backup
- POST `/admin/backup_db` to create `backups/project_data_*.db`.

## Requirements
See `requirements.txt`.

## Notes
- SQLite file: `project_data.db`.
- Auto-migration ensures `bills.paid_at` column exists.
