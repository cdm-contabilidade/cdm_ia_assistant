-- Manual PostgreSQL reproduction of Alembic revisions:
--   004_featured_knowledge_base -> 005_group_resource_authorization
--   -> 006_authorization_target_indexes
--
-- PREREQUISITE: the database must be at exactly 004_featured_knowledge_base.
-- The default Alembic version table (alembic_version) must contain exactly one
-- row with that revision.  Take a backup before running this script.
--
-- PostgreSQL requirements: PostgreSQL 12+ with the built-in plpgsql language.
-- The script uses only core PostgreSQL facilities (bytea, convert_to, decode,
-- encode, get_byte, set_byte, md5 is not required) and installs no extensions.
-- The temporary UUIDv5 helper below reproduces Python uuid.uuid5 exactly for
-- the deterministic grant IDs used by revision 005.  It is dropped with the
-- session's temporary schema and is not an application object.
--
-- Run manually, for example:
--   psql --set=ON_ERROR_STOP=1 "$DATABASE_URL" -f backend/scripts/manual_authorization_005_006.sql

BEGIN;

-- Alembic's default version table is alembic_version with one version_num
-- VARCHAR(32) row for a linear migration history.  Lock that row so another
-- migration cannot change the revision while this transaction is running.
DO $precondition$
DECLARE
    version_row_count bigint;
    current_revision text;
BEGIN
    IF to_regclass('alembic_version') IS NULL THEN
        RAISE EXCEPTION
            'Precondition failed: alembic_version does not exist; expected revision 004_featured_knowledge_base';
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

    IF current_revision IS DISTINCT FROM '004_featured_knowledge_base' THEN
        RAISE EXCEPTION
            'Precondition failed: expected Alembic revision 004_featured_knowledge_base, found %',
            coalesce(current_revision, '<NULL>');
    END IF;
END
$precondition$;

-- Keep the uuid.uuid5 behavior from revision 005 without requiring the
-- uuid-ossp or pgcrypto extensions.  A function in pg_temp is session-local.
CREATE TEMP TABLE _manual_authorization_sql_helper (
    marker integer
) ON COMMIT DROP;

CREATE OR REPLACE FUNCTION pg_temp.manual_uuid_v5(p_namespace uuid, p_name text)
RETURNS uuid
LANGUAGE plpgsql
AS $uuid_v5$
DECLARE
    payload bytea;
    payload_length integer;
    padded_length integer;
    bit_length bigint;
    words bigint[];
    h0 bigint := 1732584193;
    h1 bigint := 4023233417::bigint;
    h2 bigint := 2562383102::bigint;
    h3 bigint := 271733878;
    h4 bigint := 3285377520::bigint;
    a bigint;
    b bigint;
    c bigint;
    d bigint;
    e bigint;
    f bigint;
    k bigint;
    temp_value bigint;
    round_no integer;
    block_start integer;
    hex_digest text;
    digest bytea;
BEGIN
    payload := decode(replace(p_namespace::text, '-', ''), 'hex') || convert_to(p_name, 'UTF8');
    payload_length := length(payload);
    padded_length := ((payload_length + 9 + 63) / 64) * 64;
    bit_length := payload_length::bigint * 8;
    payload := payload
        || decode('80', 'hex')
        || decode(repeat('00', padded_length - payload_length - 9), 'hex')
        || decode(lpad(to_hex(bit_length), 16, '0'), 'hex');

    words := array_fill(0::bigint, ARRAY[80]);
    block_start := 0;
    WHILE block_start < length(payload) LOOP
        FOR round_no IN 1..16 LOOP
            words[round_no] :=
                get_byte(payload, block_start + ((round_no - 1) * 4))::bigint * 16777216
                + get_byte(payload, block_start + ((round_no - 1) * 4) + 1) * 65536
                + get_byte(payload, block_start + ((round_no - 1) * 4) + 2) * 256
                + get_byte(payload, block_start + ((round_no - 1) * 4) + 3);
        END LOOP;

        FOR round_no IN 17..80 LOOP
            temp_value := words[round_no - 3]
                # words[round_no - 8]
                # words[round_no - 14]
                # words[round_no - 16];
            words[round_no] := ((temp_value << 1) | (temp_value >> 31)) & 4294967295::bigint;
        END LOOP;

        a := h0;
        b := h1;
        c := h2;
        d := h3;
        e := h4;

        FOR round_no IN 1..80 LOOP
            IF round_no <= 20 THEN
                f := (b & c) | ((4294967295::bigint # b) & d);
                k := 1518500249;
            ELSIF round_no <= 40 THEN
                f := b # c # d;
                k := 1859775393;
            ELSIF round_no <= 60 THEN
                f := (b & c) | (b & d) | (c & d);
                k := 2400959708::bigint;
            ELSE
                f := b # c # d;
                k := 3395469782::bigint;
            END IF;

            temp_value := (
                (((a << 5) | (a >> 27)) & 4294967295::bigint)
                + f + e + k + words[round_no]
            ) % 4294967296::bigint;
            e := d;
            d := c;
            c := ((b << 30) | (b >> 2)) & 4294967295::bigint;
            b := a;
            a := temp_value;
        END LOOP;

        h0 := (h0 + a) % 4294967296::bigint;
        h1 := (h1 + b) % 4294967296::bigint;
        h2 := (h2 + c) % 4294967296::bigint;
        h3 := (h3 + d) % 4294967296::bigint;
        h4 := (h4 + e) % 4294967296::bigint;
        block_start := block_start + 64;
    END LOOP;

    hex_digest := lpad(to_hex(h0), 8, '0')
        || lpad(to_hex(h1), 8, '0')
        || lpad(to_hex(h2), 8, '0')
        || lpad(to_hex(h3), 8, '0')
        || lpad(to_hex(h4), 8, '0');
    digest := decode(hex_digest, 'hex');
    digest := set_byte(digest, 6, (get_byte(digest, 6) & 15) | 80);
    digest := set_byte(digest, 8, (get_byte(digest, 8) & 63) | 128);
    hex_digest := encode(digest, 'hex');

    RETURN (
        substr(hex_digest, 1, 8) || '-'
        || substr(hex_digest, 9, 4) || '-'
        || substr(hex_digest, 13, 4) || '-'
        || substr(hex_digest, 17, 4) || '-'
        || substr(hex_digest, 21, 12)
    )::uuid;
END
$uuid_v5$;

CREATE TABLE "groups" (
    id uuid PRIMARY KEY,
    name varchar(120) NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_groups_name UNIQUE (name)
);

CREATE TABLE group_memberships (
    group_id uuid NOT NULL,
    user_id uuid NOT NULL,
    FOREIGN KEY (group_id) REFERENCES "groups" (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, user_id)
);

CREATE INDEX ix_group_memberships_user_id
    ON group_memberships (user_id);

CREATE TABLE group_resource_grants (
    id uuid PRIMARY KEY,
    group_id uuid NOT NULL,
    capability varchar(30) NOT NULL,
    knowledge_base_id uuid,
    allowed boolean NOT NULL DEFAULT true,
    CONSTRAINT ck_group_resource_grants_target CHECK (
        (capability = 'web_search' AND knowledge_base_id IS NULL)
        OR (capability = 'knowledge_base' AND knowledge_base_id IS NOT NULL)
    ),
    FOREIGN KEY (group_id) REFERENCES "groups" (id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE CASCADE
);

CREATE INDEX ix_group_resource_grants_lookup
    ON group_resource_grants (group_id, capability, knowledge_base_id);

CREATE TABLE user_permission_overrides (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    capability varchar(30) NOT NULL,
    knowledge_base_id uuid,
    allowed boolean NOT NULL,
    CONSTRAINT ck_user_permission_overrides_target CHECK (
        (capability = 'web_search' AND knowledge_base_id IS NULL)
        OR (capability = 'knowledge_base' AND knowledge_base_id IS NOT NULL)
    ),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE CASCADE
);

CREATE INDEX ix_user_permission_overrides_lookup
    ON user_permission_overrides (user_id, capability, knowledge_base_id);

-- Revision 005 data migration.
INSERT INTO "groups" (id, name)
VALUES ('00000000-0000-0000-0000-000000000005'::uuid, 'legacy-default');

INSERT INTO group_memberships (group_id, user_id)
SELECT '00000000-0000-0000-0000-000000000005'::uuid, users.id
FROM users
WHERE users.role = 'collaborator'
  AND users.is_active IS TRUE
  AND users.is_blacklisted IS FALSE;

INSERT INTO group_resource_grants (
    id, group_id, capability, knowledge_base_id, allowed
)
SELECT
    pg_temp.manual_uuid_v5(
        '00000000-0000-0000-0000-000000000005'::uuid,
        'knowledge_base:' || knowledge_bases.id::text
    ),
    '00000000-0000-0000-0000-000000000005'::uuid,
    'knowledge_base',
    knowledge_bases.id,
    true
FROM knowledge_bases;

INSERT INTO group_resource_grants (
    id, group_id, capability, knowledge_base_id, allowed
)
VALUES (
    pg_temp.manual_uuid_v5(
        '00000000-0000-0000-0000-000000000005'::uuid,
        'web_search'
    ),
    '00000000-0000-0000-0000-000000000005'::uuid,
    'web_search',
    NULL,
    true
);

-- Revision 006 indexes.
CREATE INDEX ix_group_resource_grants_knowledge_base_id
    ON group_resource_grants (knowledge_base_id);

CREATE UNIQUE INDEX uq_group_resource_grants_knowledge_base_target
    ON group_resource_grants (group_id, knowledge_base_id)
    WHERE capability = 'knowledge_base';

CREATE UNIQUE INDEX uq_group_resource_grants_web_target
    ON group_resource_grants (group_id)
    WHERE capability = 'web_search';

CREATE INDEX ix_user_permission_overrides_knowledge_base_id
    ON user_permission_overrides (knowledge_base_id);

CREATE UNIQUE INDEX uq_user_permission_overrides_knowledge_base_target
    ON user_permission_overrides (user_id, knowledge_base_id)
    WHERE capability = 'knowledge_base';

CREATE UNIQUE INDEX uq_user_permission_overrides_web_target
    ON user_permission_overrides (user_id)
    WHERE capability = 'web_search';

-- Alembic's default version_num column is VARCHAR(32).  The target revision
-- is exactly 32 characters, so it fits without truncation.  Keep the update
-- and its row-count check together so the check is part of the same statement.
DO $version_update$
DECLARE
    updated_row_count bigint;
BEGIN
    UPDATE alembic_version
    SET version_num = '006_authorization_target_indexes'
    WHERE version_num = '004_featured_knowledge_base';

    GET DIAGNOSTICS updated_row_count = ROW_COUNT;
    IF updated_row_count <> 1 THEN
        RAISE EXCEPTION
            'Alembic version update failed: expected one row changed from 004_featured_knowledge_base, changed %',
            updated_row_count;
    END IF;
END
$version_update$;

COMMIT;
