# Enact Relational Schema Design

**Status:** Accepted WP2 design
**Related:** `docs/context/implementation-plan.md`, `docs/context/execution-plan.md`

## 1. Purpose

This document defines the relational schema direction, aggregate ownership, tenant
boundaries, versioning conventions, and migration sequence for Enact. It is the detailed
database-design companion to the persistence and security direction in the implementation
plan.

The design covers the complete product workflow so that later slices share consistent
identifiers and integrity rules. Feature tables are still introduced only by the vertical slice
that uses them. WP2 does not create the complete future schema speculatively.

The names below are logical proposed table names. A slice may refine a name or representation
when its concrete access patterns are implemented, provided the invariants in this document
remain intact or the accepted design is updated.

## 2. Core conventions

### 2.1 Identifiers

- Durable internal identifiers use PostgreSQL `uuid` columns.
- PostgreSQL generates identifiers with `DEFAULT gen_random_uuid()`.
- Applications omit generated identifiers on insert and retrieve them with `RETURNING`.
- External-system identifiers remain text and are scoped by connector instance. They are not
  used as Enact primary keys.

### 2.2 Tenant ownership

- Tenant-owned rows carry a non-null `organization_id`.
- Tenant context is transaction-local and fail-closed. Missing or invalid context exposes no
  tenant-owned rows and permits no tenant-owned writes.
- Tenant-owned parent and child tables use composite foreign keys where the relationship must
  remain inside one organization.
- Tenant-owned uniqueness constraints include `organization_id` unless uniqueness is truly
  global.
- Row-level security controls visibility. Foreign keys and uniqueness constraints separately
  enforce structural tenant integrity.

For example:

```sql
ALTER TABLE enact.customers
ADD CONSTRAINT uq_customers_organization_id_id
UNIQUE (organization_id, id);

ALTER TABLE enact.cases
ADD CONSTRAINT fk_cases_customer
FOREIGN KEY (organization_id, customer_id)
REFERENCES enact.customers (organization_id, id);
```

The second constraint validates the pair `(organization_id, customer_id)`. A case belonging to
organization A therefore cannot reference a customer belonging to organization B, even when
the customer UUID itself exists.

Composite tenant foreign keys are not used for intentionally global records such as user
identities.

### 2.3 Time, quantities, and money

- Timestamps use timezone-aware `timestamptz`.
- Calendar-only contractual dates use `date`.
- Monetary amounts use exact numeric columns and an ISO currency code; floating-point values
  are prohibited.
- Quantities and rates use exact numeric types when fractional values are valid.
- Effective periods retain explicit inclusive or exclusive boundary semantics rather than
  relying on undocumented date conventions.

### 2.4 States and concurrency

- Lifecycle states initially use constrained text rather than PostgreSQL enum types so states
  can evolve through ordinary migrations.
- Mutable records use an integer optimistic-concurrency version only when conflicting writes
  must be detected.
- A guarded update includes the previously read version and increments it atomically:

```sql
UPDATE enact.cases
SET status = :new_status,
    concurrency_version = concurrency_version + 1,
    updated_at = now()
WHERE organization_id = :organization_id
  AND id = :case_id
  AND concurrency_version = :expected_version;
```

An affected-row count of zero indicates stale state. Immutable version records do not need a
concurrency column.

### 2.5 Immutability and deletion

- Versions, decisions, source evidence, audit events, plans, simulations, authorizations,
  receipts, and reconciliation results are append-only after creation unless a narrowly defined
  lifecycle field requires an update.
- Historical records are invalidated, superseded, or revoked rather than overwritten or
  deleted.
- Foreign keys default to `RESTRICT` for evidentiary and historical data.
- Cascading deletion is limited to private, non-evidentiary children whose identity has no
  independent meaning.
- Table-specific privileges or database enforcement protect high-value immutable records;
  service-layer discipline alone is insufficient.

### 2.6 Relational and JSONB data

Identity, tenancy, lifecycle, relationships, commonly queried values, and integrity-critical
fields remain relational. Large immutable representations may use JSONB when they also carry:

- A schema version.
- A content hash.
- Creation provenance.
- Relational columns for identity, ownership, lifecycle, and commonly queried fields.

JSONB does not replace foreign keys for known relationships.

## 3. Tenant classes and access boundaries

### 3.1 Global control-plane data

Global data is not owned by one organization. The primary planned example is `users`.
Ordinary tenant repositories must not expose unrestricted access to global tables.

Membership discovery before an organization is selected requires a narrowly bounded
authentication and organization-selection path. It must not weaken RLS on application data.

### 3.2 Tenant roots

Tenant roots are directly owned by an organization. Examples include customers, cases,
connector instances, mappings, and policies.

### 3.3 Tenant descendants

Tenant descendants belong to a tenant root but still repeat `organization_id`. Tenant ownership
is not inferred only through a join to a parent. This enables direct fail-closed RLS and
composite foreign-key enforcement on every tenant-owned table.

### 3.4 RLS requirements

Every tenant-owned table must have:

- A non-null `organization_id`.
- `ENABLE ROW LEVEL SECURITY`.
- `FORCE ROW LEVEL SECURITY`.
- Matching `USING` and `WITH CHECK` policies.
- Composite tenant-safe foreign keys for tenant-owned relationships.
- Tenant-isolation tests executed as `enact_app`, not as an owner or superuser.

Tests must cover reads, inserts, updates, deletes, joins, and foreign-key attempts across
organizations. They must also prove that missing tenant context returns no rows and rejects
writes.

## 4. Aggregate ownership

| Aggregate | Root | Owned records |
|---|---|---|
| Identity and tenancy | Organization | Memberships and customers |
| Case | Case | Lineage edges, runs, and lifecycle state |
| Audit | Organization | Append-only audit events |
| Document bundle | Bundle | Documents, versions, relationships, parsed items, and source spans |
| Connection | Connector instance | Credential reference and discovery runs |
| Snapshot | Operational snapshot | Artifacts, entities, constraints, and provenance |
| Capability graph | Graph version | Graph entities and relationships tied to exact snapshots |
| Intent | Contract intent | Intent versions, alternatives, provenance, and diagnostics |
| Obligation | Obligation | Obligation versions, dependencies, and completion evidence |
| Mapping registry | Operational mapping | Mapping versions, review decisions, and invalidations |
| Policy | Organization policy | Immutable policy versions |
| Change analysis | Semantic change set | Individual changes and impact graph |
| Plan | Plan | Versions, actions, dependencies, preconditions, and assertions |
| Simulation | Plan version | Immutable simulation attempts and results |
| Authorization | Plan version | Authorization decisions bound to an exact plan hash |
| Execution | Authorized plan | Executions, action attempts, idempotency records, and receipts |
| Reconciliation | Execution | Comparisons, mismatches, and accepted deviations |
| Compiler checkpoint ownership | Case run | Tenant-to-thread ownership mapping |

Cross-aggregate references point to stable or immutable identifiers. Authorization, for
example, binds to an exact plan version and hash rather than to a mutable plan root.

## 5. Identity, tenancy, and case tables

### `organizations`

Represents an Enact tenant, such as Acme Cloud. It contains the organization identifier,
display name, lifecycle status, and timestamps. Its identifier is repeated as `organization_id`
on tenant-owned rows.

### `users`

Represents a human identity independently of organization membership. It contains the
authentication-provider subject, display identity, and identity status. A user may belong to
multiple organizations.

### `memberships`

Connects a global user to an organization and records their role and membership status. Roles
support the deal desk, administrator, operations reviewer, and auditor responsibilities. A
tenant-scoped uniqueness constraint prevents duplicate membership in one organization.

### `customers`

Represents an organization's contractual counterparty, such as Redwood Systems. It contains
organization-scoped identity, display name, optional business identifiers, and lifecycle
status. Cases and customer-state discovery reference it.

### `cases`

Represents one durable activation or amendment unit of work. It owns lifecycle state and links
to the customer. A concurrency version protects meaningful mutable transitions such as case
status changes.

### `case_lineage`

Represents typed relationships between cases, such as `amends` or `supersedes`. Explicit edges
preserve amendment history and can carry authority metadata without reducing lineage to one
unexplained prior-case pointer.

### `case_runs`

Records resumable attempts to process a case, including discovery, document processing,
compilation, planning, or execution coordination. Retries create new runs so failed attempts
remain inspectable.

### `audit_events`

Records who performed an action, what resource was affected, when it occurred, and the request
or correlation identifier. Audit events describe activity. They differ from evidence links,
which explain why a result has a particular contractual or operational value.

## 6. Document and source tables

### `document_bundles`

Groups documents submitted together for a case. The Redwood baseline bundle contains the order
form, master services agreement, product schedule, support schedule, and onboarding statement
of work. An amendment is received in a later case and bundle.

### `documents`

Represents the logical identity, classification, authority metadata, and processing state of a
document within a bundle. The identity survives processing retries and corrected versions.

### `document_versions`

Represents an immutable uploaded binary or derived document revision. It stores the
object-storage key, SHA-256 hash, media type, byte length, filename, version number, and upload
provenance. The document bytes remain behind the object-storage boundary.

### `document_relationships`

Represents relationships such as amendment, supplementation, incorporation, or term-specific
override. A relationship may reference supporting source evidence or a reviewer decision. This
allows authority to be evaluated per term instead of imposing one global document order.

### `parsed_items`

Stores processor-neutral document structure such as headings, paragraphs, tables, table cells,
and list items. Parent relationships and document order preserve hierarchy without exposing a
processor-specific data model to the rest of the application.

### `source_spans`

Identifies exact source locations using document version, parsed item, page, text offsets,
optional bounding box, exact extracted text, and a content hash. Intent fields and decisions
refer to source spans rather than only to whole documents.

## 7. Connector, discovery, and snapshot tables

### `connector_instances`

Represents a configured connection to an operational system, such as the billing or entitlement
simulator. It stores connector type, display identity, status, and non-secret configuration.

### `credential_references`

Stores a secret-provider reference, locator, and rotation metadata for a connector. It never
stores plaintext credentials. Model-facing services cannot access credential references.

### `discovery_runs`

Records an attempt to read reference data, capabilities, constraints, or customer state from a
connector. It records completeness, failures, and partial-result diagnostics. One run may
produce multiple snapshots.

### `operational_snapshots`

Identifies an immutable reference-data, capability, or customer-state view. It records connector
and customer scope, capture time, external version, content hash, completeness, and freshness
metadata. Compilation consumes these snapshots instead of uncontrolled live reads.

### `snapshot_artifacts`

Stores the complete versioned snapshot representation as schema-versioned JSONB. It preserves
the source representation for reproducibility.

### `snapshot_entities`

Projects important target objects into searchable relational rows. Examples include products,
prices, features, meters, subscriptions, and workspace allocations. Each row retains its
connector-scoped external identifier and a pointer into the original artifact.

### `snapshot_constraints`

Represents discovered rules such as supported proration, feature prerequisites, workspace
limits, or pooling behavior. A typed payload may be used where constraint shapes differ, while
identity, provenance, and commonly queried values remain relational.

The billing and entitlement simulators remain independently versioned operational stores.
Enact references their external identifiers through connector snapshots and has no relational
foreign keys into simulator-owned tables.

## 8. Operational Capability Graph tables

### `capability_graph_versions`

Identifies an immutable graph projection created from exact snapshot versions. It records its
input snapshots, projection schema version, and content hash.

### `capability_graph_entities`

Represents graph nodes such as products, prices, features, supported operations, subscriptions,
and current entitlements. Nodes reference snapshot entities where possible rather than copying
source data without provenance.

### `capability_graph_relationships`

Represents typed edges such as `requires`, `supports`, `has_subscription`, or `controls_meter`.
The graph supports mapping and impact analysis while remaining a PostgreSQL relational
projection rather than requiring a graph database.

## 9. Contract Intent IR and diagnostic tables

### `contract_intents`

Represents the durable intent aggregate for a case. It may point to the current candidate and
accepted versions. It never contains target-system identifiers merely because a mapping was
proposed.

### `contract_intent_versions`

Stores an immutable, schema-versioned interpretation of the contract, including billing,
entitlement, support, onboarding, effective-period, and authority semantics. It records its
content hash, creation run, version number, and predecessor.

### `intent_provenance`

Links an exact intent field path to one or more source spans. The link identifies whether a span
supports, conflicts with, or was overridden for that field and records the authority reason.

### `intent_alternatives`

Stores competing interpretations of an unresolved field. The reference ambiguity produces a
pooled 20 TB alternative and a 20 TB-per-workspace alternative. Alternatives retain their
source spans and materiality.

### `diagnostics`

Records deterministic errors, warnings, policy exceptions, unsupported capabilities, contract
ambiguities, unresolved mappings, and stale-state findings. A diagnostic has a stable code,
category, severity, affected path or domain, structured details, and resolution state.

## 10. Obligation tables

### `obligations`

Represents the durable identity and lifecycle of a support or onboarding commitment, such as a
30-minute Priority 1 response or kickoff within five business days.

### `obligation_versions`

Stores immutable obligation terms: subject, responsible party, beneficiary, required outcome,
trigger, due condition, effective period, remedy, evidence requirements, and source provenance.

### `obligation_dependencies`

Represents prerequisites and ordering. Customer identity-provider access, for example, precedes
SSO configuration, while workspace setup, identity setup, and training precede the
production-readiness review.

### `obligation_evidence`

Records evidence that an obligation trigger or completion occurred. A recorded kickoff
completion may satisfy an obligation milestone and make the onboarding fee billable.

## 11. Mapping and decision tables

### `operational_mappings`

Represents the durable identity and current reviewed state of a relationship between an intent
concept and target objects. It is an organization-level aggregate so a reviewed mapping can be
reused within its authorized scope.

### `operational_mapping_versions`

Stores immutable mapping content, including the intent-side concept, target snapshot entities,
applicable target operation, compatibility information, content hash, and provenance.

Mapping scope may be represented by constrained columns or related qualifiers depending on the
concrete access patterns. Supported scopes are activation-only, customer-specific,
contract-template-specific, product-family-specific, and organization-wide. A scoped mapping
stores the identifier that qualifies its scope.

### `mapping_decisions`

Records review of a mapping version, including acceptance or rejection, reviewer, explanation,
evidence, and approved reuse scope. Broad promotion requires a separately authorized decision.

### `mapping_invalidations`

Records that a previously reviewed mapping can no longer be reused because a target object,
connector, compatibility rule, or reviewer decision changed. Invalidation preserves the old
mapping for audit and evidence.

### `interpretation_decisions`

Records answers about what the contract means. The clarification that 20 TB is pooled across
both production workspaces belongs here, not in a mapping decision.

Interpretation, mapping, and policy decisions remain separate types even if implementation
later introduces carefully designed shared decision infrastructure.

## 12. Policy tables

### `organization_policies`

Represents the durable identity and current state of an explicit organization policy, such as
an automatically permitted discount limit.

### `organization_policy_versions`

Stores immutable, effective-dated, schema-versioned policy rules and their content hashes.
Validation and planning record the exact policy versions used.

### `policy_decisions`

Records authorization or rejection of policy exceptions. In the reference case, a concise
decision may cover the 15% discount and 30-minute Priority 1 response commitment without
requiring approval for standard actions.

## 13. Semantic change and impact tables

### `semantic_change_sets`

Represents the immutable difference between an accepted prior intent and an amended intent. It
records both versions, effective date, content hash, and lifecycle state.

### `semantic_changes`

Stores individual field-level or semantic changes, including change type, before value, after
value, effective period, and amendment source spans. Explicitly unchanged terms may be retained
when needed to support unaffected-state proof.

### `impact_graph_entities`

Represents intent concepts, operational objects, or domains considered during amendment impact
analysis.

### `impact_graph_relationships`

Explains how a semantic change propagates. A seat-quantity change affects seat entitlement and
prorated billing; a capacity change affects the enforced allowance and billing overage
threshold. Unconnected state is excluded from mutation actions.

## 14. Plan tables

### `plans`

Represents the durable planning aggregate for a case and may identify its current plan version.

### `plan_versions`

Stores an immutable plan compiled from exact intent, mapping, policy, snapshot, and optional
semantic-change-set versions. It carries a plan hash. Any material input change produces a new
plan version.

### `plan_actions`

Represents one proposed operational mutation or obligation-ledger action. It records domain,
target, operation, before and after values, and stable idempotency material.

### `plan_action_dependencies`

Defines required ordering between actions, such as creating a customer account before its
subscription or enabling the enterprise edition before analytics.

### `plan_preconditions`

Defines state that must still be true before execution, including expected target versions,
current quantities, mapping validity, and target existence.

### `unaffected_state_assertions`

Records state that the plan must preserve. The Redwood amendment asserts that analytics,
workspace quantities, SSO, SCIM, support, onboarding, and prior invoices remain unchanged.

## 15. Simulation and authorization tables

### `simulation_attempts`

Records an immutable simulation of an exact plan version, including before-state hashes,
expected after-state, adapter responses, warnings, failures, and status. Changed input or target
state requires a new simulation.

### `plan_authorizations`

Records permission to execute an exact plan version and hash, normally after review of a
specific simulation. Authorization does not transfer automatically to a new plan version.

## 16. Execution tables

### `executions`

Represents a coordinated attempt to apply an authorized plan and records its overall status,
timing, correlation identifier, and failure summary.

### `action_attempts`

Records individual attempts to execute a plan action, including attempt number, expected target
version, timing, and result. Retries preserve the plan action's stable idempotency identity.

### `idempotency_records`

Records the unique organization-, connector-, and action-scoped idempotency key and its first
known outcome. A repeated request reuses that outcome instead of producing a duplicate charge
or quantity increase. This responsibility may be integrated with action attempts if the final
adapter design preserves the same database-enforced uniqueness.

### `execution_receipts`

Stores the target system's response, external operation identifier, resulting target version,
structured response or hash, timestamp, and success or failure information. A successful
receipt is not proof of final state; reconciliation performs that verification.

## 17. Reconciliation tables

### `reconciliation_runs`

Records a post-execution observation of actual target state and links it to the execution and
freshly captured state.

### `reconciliation_comparisons`

Compares one intended value with one observed value and records whether they match. Comparisons
retain links to the responsible plan action and observed snapshot entity.

### `reconciliation_mismatches`

Stores actionable mismatch details, severity, attribution category, related action and receipt,
and resolution state.

### `accepted_deviations`

Records an authorized decision to accept a known reconciliation difference, including reviewer,
rationale, scope, and effective period. A deviation is never silently converted into success.

## 18. Evidence and compiler checkpoint tables

### `evidence_links`

Connects material artifacts across aggregate boundaries using typed relationships and optional
field paths. It supports the complete chain:

```text
source span
  -> intent field
  -> snapshot entity
  -> mapping or decision
  -> diagnostic
  -> plan action
  -> authorization
  -> execution receipt
  -> reconciliation comparison
```

Evidence links supplement rather than replace direct foreign keys used for ordinary ownership.

### `compiler_threads`

Maps a LangGraph thread to its organization, case, and run. Before loading or resuming a
checkpoint, the application verifies ownership through this mapping.

LangGraph may maintain its own checkpoint representation. Those tables are infrastructure
details and are not exposed as tenant application resources. The ownership chain is:

```text
organization -> case -> case run -> compiler thread -> checkpoint
```

## 19. End-to-end data flow

### 19.1 Baseline activation

1. `organizations`, `users`, and `memberships` establish Acme Cloud and an authorized user.
2. `customers` identifies Redwood Systems.
3. `cases` creates the baseline activation and `case_runs` records processing attempts.
4. The uploaded bundle creates document, version, relationship, parsed-item, and source-span
   records while PDF bytes remain in object storage.
5. Connector discovery creates immutable billing, entitlement, capability, and customer-state
   snapshots and their searchable entity projections.
6. A capability graph version projects the relevant snapshot entities and relationships.
7. Compilation creates an immutable contract-intent version with field-level source
   provenance.
8. The pooled-versus-per-workspace ambiguity creates alternatives and a blocking diagnostic.
9. The user's pooled answer creates an interpretation decision and permits a new or resumed
   accepted intent version.
10. Mapping candidates connect intent concepts to snapshot entities. Review creates mapping
    versions and mapping decisions within explicit reuse scopes.
11. Obligations represent support and onboarding commitments and dependencies.
12. Validation uses exact intent, snapshot, mapping, and policy versions to create an immutable
    plan with actions, dependencies, preconditions, and unaffected-state assertions.
13. Simulation records expected before-and-after state. Policy evaluation identifies the
    discount and support exceptions, and the reviewer records the policy decision.
14. Authorization binds to the exact plan hash and simulation.
15. Execution records coordinated and per-action attempts, stable idempotency identities, and
    adapter receipts.
16. Reconciliation reads actual target state and records comparisons, mismatches, and any
    explicitly accepted deviations.
17. Evidence links connect each material final value back through actions, decisions, mappings,
    snapshots, intent, and source spans.

### 19.2 Amendment compilation

1. A new amendment case and bundle are connected to the baseline through case lineage.
2. The compiler loads the accepted baseline intent and mappings, captures current operational
   snapshots, and constructs a new amended intent version.
3. A semantic change set records the increase from 300 to 450 seats and from pooled 20 TB to
   pooled 35 TB, including effective periods and amendment provenance.
4. The impact graph identifies seat billing, seat entitlement, usage billing, and usage
   entitlement as affected.
5. Unchanged analytics, workspace, identity, support, onboarding, and prior-invoice state is
   recorded as preservation assertions rather than mutation actions.
6. Planning calculates the prorated charge and matching entitlement deltas from exact accepted
   inputs.
7. Preconditions and fresh snapshot versions detect stale state before authorization and
   execution.
8. Idempotent execution applies only the affected actions, and reconciliation verifies the
   resulting billing and entitlement state.

## 20. Migration sequence

The design is implemented incrementally:

1. **WP2 foundation:** migration naming, ownership, schema qualification, grants, default
   privileges, downgrade conventions, RLS helpers, tenant context, and isolation harness. No
   speculative feature tables.
2. **WP3 identity and intake:** identity, membership, customers, cases, lineage, runs, audit,
   documents, relationships, parsing, and source spans.
3. **WP4 operational discovery:** connector and credential references, independently versioned
   simulator stores, discovery runs, immutable snapshots, and capability graph projection.
4. **WP5 intent compilation:** intent versions, provenance, alternatives, diagnostics,
   obligations, and compiler checkpoint ownership.
5. **WP6 mapping:** mapping registry, versions, scopes, review decisions, promotions, and
   invalidations.
6. **WP7 planning and execution:** policy versions, plan versions and actions, simulations,
   authorization, execution, receipts, reconciliation, and evidence.
7. **WP8 amendments:** semantic change sets, semantic changes, impact graph, and amendment
   preservation assertions.

Each migration uses a monotonically increasing four-digit revision prefix, contains one
coherent schema change, includes a valid downgrade unless an accepted exception explains why
reversal is unsafe, and applies the required ownership, grants, and RLS configuration in the
same reviewed change.

## 21. Design validation criteria

Before WP2.1 is accepted, the design must demonstrate that:

- Every tenant-owned relationship is structurally unable to cross organizations.
- Missing tenant context fails closed.
- Global identity access does not create a bypass around tenant RLS.
- The pooled 20 TB clarification is distinct from target mapping and policy authorization.
- The 15% discount and 30-minute support commitment are policy exceptions rather than mapping
  decisions.
- Billing and entitlement allowance values can be traced to the same accepted quantity and
  scope.
- Plans and authorizations are bound to exact immutable inputs.
- Stale snapshots, mappings, policies, plans, and target versions can be detected.
- The July amendment produces only seat, prorated billing, and shared-capacity mutations.
- Unchanged products, obligations, and prior invoices remain provably unaffected.
- Every material reconciled result can be traced back to source evidence, discovered context,
  organization policy, or a recorded human decision.
