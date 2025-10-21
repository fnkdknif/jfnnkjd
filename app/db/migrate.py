"""
Database migration utilities.
Simple migration system for schema changes.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Session, select, SQLModel, Field


class Migration(SQLModel, table=True):
    """Track applied migrations."""

    __tablename__ = "migrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    checksum: str
    applied_at: datetime = Field(default_factory=datetime.utcnow)


class MigrationManager:
    """Manage database schema migrations."""

    def __init__(self, session: Session, migrations_dir: Path):
        self.session = session
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Ensure migrations tracking table exists."""
        Migration.metadata.create_all(self.session.get_bind())

    def _get_migration_checksum(self, migration_file: Path) -> str:
        """Calculate checksum of migration file."""
        content = migration_file.read_text()
        return hashlib.sha256(content.encode()).hexdigest()

    def get_applied_migrations(self) -> list[str]:
        """Get list of applied migration names."""
        stmt = select(Migration.name)
        result = self.session.exec(stmt)
        return result.all()

    def get_pending_migrations(self) -> list[Path]:
        """Get list of pending migration files."""
        if not self.migrations_dir.exists():
            return []

        applied = set(self.get_applied_migrations())
        all_migrations = sorted(self.migrations_dir.glob("*.sql"))

        pending = [m for m in all_migrations if m.stem not in applied]
        return pending

    def apply_migration(self, migration_file: Path) -> bool:
        """
        Apply a single migration.
        Returns True if successful.
        """
        try:
            # Read and execute SQL
            sql_content = migration_file.read_text()
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]

            for stmt in statements:
                self.session.exec(stmt)

            # Record migration
            checksum = self._get_migration_checksum(migration_file)
            migration = Migration(name=migration_file.stem, checksum=checksum)
            self.session.add(migration)
            self.session.commit()

            print(f"✓ Applied migration: {migration_file.name}")
            return True

        except Exception as e:
            self.session.rollback()
            print(f"✗ Failed to apply migration {migration_file.name}: {e}")
            return False

    def migrate(self) -> int:
        """
        Apply all pending migrations.
        Returns number of migrations applied.
        """
        pending = self.get_pending_migrations()

        if not pending:
            print("No pending migrations.")
            return 0

        print(f"Found {len(pending)} pending migration(s).")

        applied_count = 0
        for migration_file in pending:
            if self.apply_migration(migration_file):
                applied_count += 1
            else:
                print(f"Stopping migration due to error.")
                break

        return applied_count

    def rollback_last(self) -> bool:
        """
        Rollback last migration (if rollback script exists).
        """
        # Get last applied migration
        stmt = select(Migration).order_by(Migration.applied_at.desc())
        result = self.session.exec(stmt)
        last_migration = result.first()

        if not last_migration:
            print("No migrations to rollback.")
            return False

        # Look for rollback script
        rollback_file = self.migrations_dir / f"{last_migration.name}_rollback.sql"

        if not rollback_file.exists():
            print(f"No rollback script found for {last_migration.name}")
            return False

        try:
            # Execute rollback
            sql_content = rollback_file.read_text()
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]

            for stmt in statements:
                self.session.exec(stmt)

            # Remove migration record
            self.session.delete(last_migration)
            self.session.commit()

            print(f"✓ Rolled back migration: {last_migration.name}")
            return True

        except Exception as e:
            self.session.rollback()
            print(f"✗ Failed to rollback migration: {e}")
            return False


def create_migration(name: str, migrations_dir: Path) -> Path:
    """
    Create a new migration file.
    Returns path to the created file.
    """
    migrations_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.sql"
    filepath = migrations_dir / filename

    # Create template
    template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- Add your SQL statements here
-- Example:
-- ALTER TABLE documents ADD COLUMN new_field VARCHAR(255);

-- Remember to create a corresponding rollback file:
-- {timestamp}_{name}_rollback.sql
"""

    filepath.write_text(template)
    print(f"Created migration: {filepath}")

    # Create rollback template
    rollback_filepath = migrations_dir / f"{timestamp}_{name}_rollback.sql"
    rollback_template = f"""-- Rollback for: {name}
-- Created: {datetime.now().isoformat()}

-- Add rollback SQL statements here
-- Example:
-- ALTER TABLE documents DROP COLUMN new_field;
"""

    rollback_filepath.write_text(rollback_template)
    print(f"Created rollback script: {rollback_filepath}")

    return filepath
