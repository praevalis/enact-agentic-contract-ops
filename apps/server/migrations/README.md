# Database migrations

Alembic connects as `enact_migrate`. Migration execution explicitly assumes
`enact_owner`; the running application connects separately as `enact_app`.
