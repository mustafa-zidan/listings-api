# Migration Guide

This guide explains how to create and run database migrations using Alembic in this project.

---

## Creating a New Migration

1. **Make Changes to Your Models**:
   Update your SQLAlchemy models in the `app.models` module to reflect the desired database changes.

2. **Generate a New Migration Script**:
   Use the following command to generate a migration script:
   ```bash
   alembic revision --autogenerate -m "Your migration description"
   ```
   Replace `"Your migration description"` with a brief description of the changes made in this migration.
   The generated migration script will be located in the `versions/` directory.

## Running Migrations

### Run Migrations in (Online Mode):

To apply the migrations to your development database, use the following command:
```bash
alembic upgrade head
```

### Run Migrations (Offline Mode):

If you need to generate a SQL script to apply the migrations manually, use the following command:
```bash
alembic upgrade head --sql > migration.sql
```
## Verifying Migration Status
To check the current migration status, run:
```bash
alembic current
```
This will display the current migration revision applied to the database.

## Rolling Back a Migration
To roll back the last migration, use the following command:
```bash
alembic downgrade -1
```
You can also downgrade to a specific revision by using its revision ID:
```bash
alembic downgrade <revision_id>
```
Replace `<revision_id>` with the desired revision ID.

## Additional Commands



