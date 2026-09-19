# Database migrations

This directory contains reviewed changes to Enact-owned objects in the `enact` schema.
PostgreSQL role and schema provisioning remains in
`infra/postgres/bootstrap/01-roles.sh`; Alembic does not create login roles, grant role
membership, or create the application schema because those objects must exist before
Alembic can connect.

## Roles and ownership

- Alembic connects as the `enact_migrate` login role.
- Online migration execution uses `SET LOCAL ROLE enact_owner`. The role change is scoped to
  the migration transaction and is reverted automatically on commit or rollback.
- Objects created by migrations are therefore owned by the non-login `enact_owner` role.
- The service connects as `enact_app`. It must not own application objects, perform DDL,
  assume `enact_owner`, or access Alembic's version table.
- Application objects are schema-qualified under `enact`. Alembic's version table also lives
  in `enact`, but it is not granted to `enact_app`.

Do not add `ALTER ... OWNER` statements to ordinary revisions. If a revision cannot create an
object while acting as `enact_owner`, fix the migration or provisioning boundary instead of
transferring ownership to a login role.

## Runtime privileges

The bootstrap grants `enact_app` only `USAGE` on the `enact` schema. Every revision that adds
an application-accessible object must grant only the privileges required by its current
runtime consumer in that same revision.

Use these rules when reviewing grants:

- Grant table privileges explicitly, such as `SELECT`, `INSERT`, `UPDATE`, or `DELETE`; do not
  use `ALL PRIVILEGES`.
- Grant sequence privileges explicitly when a runtime insert depends on a sequence.
- Grant `EXECUTE` only for functions or procedures intended as runtime entry points. Revoke
  the PostgreSQL default `PUBLIC` function execution privilege before granting a narrower
  role.
- Do not grant `enact_app` access to migration-only tables, maintenance functions, or
  implementation objects that have no runtime consumer.
- Do not use `GRANT ... ON ALL ...` in a migration. It can widen access to unrelated objects.

Enact deliberately does not configure broad `ALTER DEFAULT PRIVILEGES` rules. Explicit grants
keep each revision reviewable and prevent a future table, sequence, or function from becoming
runtime-accessible merely because it was created in the schema. If a concrete operational
need later justifies default privileges, that is an architecture change and must be accepted
before implementation.

## Revision conventions

- Use a monotonically increasing four-digit revision identifier and a concise description,
  for example `0001_initial` or `0002_add_documents`.
- Keep one coherent schema change in each revision.
- Create objects in dependency order: tables and constraints, indexes, tenant policies, then
  runtime grants.
- Treat generated revisions as drafts. Review schema qualification, constraint names, server
  defaults, ownership, grants, and row-level security before applying them.
- A migration that creates or changes a tenant-owned table must apply its required RLS
  configuration and runtime grants in the same reviewed change. The reusable RLS mechanics
  and isolation tests are established by WP2.7.

Tenant-owned revisions use the shared RLS helpers and keep grants explicit:

```python
from alembic import op
from enact.platform.database.migrations import disable_tenant_rls, enable_tenant_rls


def upgrade() -> None:
    op.create_table(...)
    enable_tenant_rls(op, 'customers')
    op.execute('GRANT SELECT, INSERT, UPDATE ON enact.customers TO enact_app')


def downgrade() -> None:
    op.execute('REVOKE SELECT, INSERT, UPDATE ON enact.customers FROM enact_app')
    disable_tenant_rls(op, 'customers')
    op.drop_table('customers', schema='enact')
```

The upgrade order is table, constraints, indexes, RLS, then grants. Downgrades revoke grants,
remove RLS, and drop dependent objects in reverse order. The RLS helper assumes a non-null
UUID `organization_id` column and creates one `tenant_isolation` policy for `enact_app` with
matching `USING` and `WITH CHECK` expressions. Do not add a second permissive policy that can
broaden this predicate.

Online migrations are the authoritative execution path because the environment can assume
`enact_owner` transaction-locally. Offline SQL generation cannot perform that connection-time
role transition; generated SQL must be executed by an operator under equivalent owner
privileges.

## Downgrades

Every revision must restore the exact preceding schema and privilege state unless an accepted
task explicitly documents why reversal is unsafe or impossible.

Downgrades reverse dependencies and security changes before removing their objects:

1. Revoke privileges introduced by the upgrade.
2. Remove policies and other dependent security objects.
3. Remove constraints, indexes, functions, sequences, and tables in safe reverse order.

If a downgrade preserves an object, restore its previous owner, grants, defaults, policies,
and constraints rather than only reversing its columns. Never make data loss implicit: call
out destructive downgrade behavior in the revision docstring and obtain acceptance for an
irreversible revision before merging it.
