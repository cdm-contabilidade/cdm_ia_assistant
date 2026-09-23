-- CDM AI Assistant migration 007: encrypted provider credentials.
-- PREREQUISITE: the database must be exactly at Alembic revision
-- 006_authorization_target_indexes. Take a backup before running this script.
-- Run with psql --set=ON_ERROR_STOP=1 so any failure aborts this transaction
-- and rolls it back. No provider secrets are read or inserted by this script;
-- the application stores only Fernet ciphertext here, while
-- PROVIDER_KEYS_ENCRYPTION_KEY remains outside the database.

BEGIN;

-- Alembic's default version table is alembic_version and should contain one
-- version_num row for this linear migration history. Lock the row while the
-- migration runs so a concurrent migration cannot change the revision.
DO $precondition$
DECLARE
    version_row_count bigint;
    current_revision text;
BEGIN
    IF to_regclass('alembic_version') IS NULL THEN
        RAISE EXCEPTION
            'Precondition failed: alembic_version does not exist; expected revision 006_authorization_target_indexes';
    END IF;

    SELECT count(*)
      INTO version_row_count
      FROM alembic_version;

    IF version_row_count <> 1 THEN
        RAISE EXCEPTION
            'Precondition failed: expected exactly one alembic_version row, found %',
            version_row_count;
    END IF;

    SELECT version_num
      INTO current_revision
      FROM alembic_version
      FOR UPDATE;

    IF current_revision IS DISTINCT FROM '006_authorization_target_indexes' THEN
        RAISE EXCEPTION
            'Precondition failed: expected Alembic revision 006_authorization_target_indexes, found %',
            coalesce(current_revision, '<NULL>');
    END IF;
END
$precondition$;

CREATE TABLE provider_credentials (
    provider VARCHAR(20) PRIMARY KEY,
    encrypted_api_key TEXT,
    last4 VARCHAR(4),
    disabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_provider_credentials_provider CHECK (provider IN ('gemini', 'openai'))
);

-- Update Alembic only from the verified predecessor revision and assert that
-- exactly one version row changed.
DO $version_update$
DECLARE
    updated_row_count bigint;
BEGIN
    UPDATE alembic_version
    SET version_num = '007_provider_credentials'
    WHERE version_num = '006_authorization_target_indexes';

    GET DIAGNOSTICS updated_row_count = ROW_COUNT;
    IF updated_row_count <> 1 THEN
        RAISE EXCEPTION
            'Alembic version update failed: expected one row changed from 006_authorization_target_indexes, changed %',
            updated_row_count;
    END IF;
END
$version_update$;

COMMIT;
