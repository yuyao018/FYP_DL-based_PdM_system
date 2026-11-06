import { PGlite } from '../tmp/maintenance_sql_runtime/node_modules/@electric-sql/pglite/dist/index.js';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
const db = new PGlite();
try {
await db.exec(`
CREATE ROLE authenticated;
CREATE SCHEMA app_private;
CREATE TABLE public.engines(id integer PRIMARY KEY, organization_id uuid, is_deleted boolean);
INSERT INTO engines VALUES
(1,'00000000-0000-0000-0000-000000000001',true),
(2,'00000000-0000-0000-0000-000000000002',true),
(3,'00000000-0000-0000-0000-000000000001',false);
CREATE FUNCTION app_private.current_org_id() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT current_setting('test.org')::uuid $$;
CREATE FUNCTION app_private.has_org_role(target_org uuid, allowed_roles text[]) RETURNS boolean LANGUAGE sql STABLE AS
$$ SELECT target_org = app_private.current_org_id() AND current_setting('test.role') = ANY(allowed_roles) $$;
GRANT USAGE ON SCHEMA public, app_private TO authenticated;
GRANT SELECT, UPDATE ON engines TO authenticated;
ALTER TABLE engines ENABLE ROW LEVEL SECURITY;
CREATE POLICY engines_read_org ON engines FOR SELECT TO authenticated
USING (organization_id = app_private.current_org_id() AND COALESCE(is_deleted,true));
CREATE POLICY engines_update_admin ON engines FOR UPDATE TO authenticated
USING (app_private.has_org_role(organization_id, ARRAY['admin']::text[]))
WITH CHECK (app_private.has_org_role(organization_id, ARRAY['admin']::text[]));
SET ROLE authenticated;
SET test.org = '00000000-0000-0000-0000-000000000001';
SET test.role = 'admin';
`);
await assert.rejects(db.query('UPDATE engines SET is_deleted=false WHERE id=1 RETURNING *'),
    e => e.code === '42501');
console.log('PASS: original policy reproduces reported 42501');
await db.exec('RESET ROLE');
const fix = readFileSync(new URL('../docs/RLS_FIX_ENGINE_SOFT_DELETE.sql', import.meta.url), 'utf8');
await db.exec(fix);
await db.exec(fix); // safely repeatable
await db.exec('SET ROLE authenticated');
assert.equal((await db.query('UPDATE engines SET is_deleted=false WHERE id=1 RETURNING *')).rows.length, 1);
console.log('PASS: admin removes engine with RETURNING');
assert.equal((await db.query('SELECT * FROM engines WHERE is_deleted=false')).rows.length, 2);
assert.equal((await db.query('UPDATE engines SET is_deleted=true WHERE id=1 RETURNING *')).rows.length, 1);
console.log('PASS: admin lists and restores removed engines');
assert.equal((await db.query('SELECT * FROM engines WHERE id=2')).rows.length, 0);
assert.equal((await db.query('UPDATE engines SET is_deleted=false WHERE id=2 RETURNING *')).rows.length, 0);
console.log('PASS: admin cannot read or modify another organization');
await assert.rejects(db.query("UPDATE engines SET organization_id='00000000-0000-0000-0000-000000000002' WHERE id=1 RETURNING *"),
    e => e.code === '42501');
console.log('PASS: admin cannot move engine into another organization');
await db.exec("SET test.role = 'user'");
assert.equal((await db.query('SELECT * FROM engines WHERE id=3')).rows.length, 0);
assert.equal((await db.query('SELECT * FROM engines WHERE id=1')).rows.length, 1);
assert.equal((await db.query('UPDATE engines SET is_deleted=false WHERE id=1 RETURNING *')).rows.length, 0);
console.log('PASS: ordinary members see active engines and cannot remove engines');
} finally { await db.close(); }
