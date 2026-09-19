# Enact Technical Implementation Plan

**Status:** Accepted revised baseline
**Related:** `docs/context/prd.md`
**Scope:** Baseline activation followed by amendment-driven contract change compilation

## 1. Architecture

Enact is a modular monolith with a React/Vite static client calling FastAPI directly. FastAPI owns application data, orchestration, target mutations, and the OpenAPI contract.

```text
Browser
  -> React/Vite operational workspace
  -> FastAPI
       -> case and document services
       -> document processor
       -> LangGraph compiler
       -> operational discovery and snapshots
       -> deterministic validation and planning
       -> policy, authorization, and execution
       -> reconciliation, evidence, and evaluation
       -> billing, entitlement, and obligation adapters
            -> PostgreSQL
            -> S3-compatible document storage
            -> configurable model provider
```

The system begins request-driven and resumable. A worker may be introduced only for a measured workload that cannot operate reliably within the request lifecycle. Multiple agents remain an evaluation-driven option, not a default.

## 2. Technology baseline

| Concern | Technology |
|---|---|
| Web | React, Vite, TypeScript, pnpm |
| API and services | FastAPI, Pydantic, Python 3.13 |
| Agent orchestration | LangGraph Python |
| Persistence | PostgreSQL, SQLAlchemy 2.x, asyncpg |
| Migrations | Alembic |
| Tenant isolation | Scoped PostgreSQL roles and RLS |
| Documents | Processor abstraction, with Docling evaluated first |
| Object storage | S3-compatible interface, MinIO locally |
| API client | Generated TypeScript client from FastAPI OpenAPI |
| Python tooling | Root uv workspace and pre-commit |
| Tests | pytest, Vitest, Playwright |

No BFF, graph database, vector database, message broker, domain microservices, or live commercial integrations are required initially.

## 3. Core boundaries

### Cases

Owns initial activation and amendment lifecycle, lineage, active document bundle, accepted intent, compilation attempts, concurrency version, and terminal or recoverable state.

### Documents

Owns originals, hashes, versions, parsed pages and items, source spans, classifications, authority, precedence, and amendment relationships.

### Contract intent

Owns immutable Contract Intent IR versions. Contract intent represents signed requirements independently from target identifiers and proposed operations.

### Discovery

Captures immutable reference-data, capability, and customer-state snapshots through adapters. It constructs a versioned Operational Capability Graph projection from those snapshots.

### Mappings

Owns proposed and reviewed relationships between intent and target objects. Mapping versions record provenance, scope, validity, review decisions, and invalidation.

### Obligations

Represents support and onboarding commitments in one generic model and persists their lifecycle in a bounded obligation ledger.

### Validation and planning

Validates intent structure, dates, billing arithmetic, entitlement compatibility, mapping feasibility, and billing-entitlement consistency. Planning computes affected domains and produces a minimal dependency-aware operational diff.

### Policies and decisions

Evaluates explicit materiality and authorization policies. It keeps contract clarification, mapping decisions, and policy authorization separate.

### Adapters and execution

Adapters expose system facts and bounded operations. Only the execution service may invoke mutations after validating plan hash, authorization, expected target versions, and idempotency keys.

### Evidence and evaluation

Evidence connects source, intent, snapshots, mappings, decisions, actions, receipts, and reconciliation. Evaluation exercises the same services as the application.

## 4. Operational representations

### Contract Intent IR

The IR contains parties, commercial terms, product access, quotas, obligations, triggers, dependencies, effective periods, document authority, interpretations, alternatives, unresolved terms, and exact source provenance.

It never absorbs a target identifier merely because the agent proposed a match.

### Operational snapshots and OCG

Adapters produce three immutable snapshot types:

- Reference data: target objects and identifiers
- Capabilities: supported operations, constraints, and preconditions
- Customer state: current configured values and target versions

The OCG is a PostgreSQL-backed graph projection using entity and relationship tables. It references exact snapshot versions and does not require a graph database.

### Operational mappings

A mapping connects one intent concept to one or more target entities and operations. Reuse scope is activation-only, customer-specific, contract-template-specific, product-family-specific, or organization-wide. Broadening scope requires explicit authorization.

### Contractual obligations

Support and onboarding initially share a typed obligation representation containing subject, parties, required outcome, trigger, due condition, dependencies, completion evidence, remedy, effective period, and provenance.

### Semantic change set

An amendment creates a new intent version plus an explicit difference from accepted prior intent. The change set drives impact analysis and prevents unaffected state from entering the delta plan.

## 5. Adapter contract

The detailed types will evolve with the first implemented slice. The required responsibilities are:

```python
class OperationalAdapter(Protocol):
    domain: OperationalDomain

    async def read_reference_data(...) -> ReferenceDataSnapshot: ...
    async def discover_capabilities(...) -> CapabilitySnapshot: ...
    async def read_customer_state(...) -> CustomerStateSnapshot: ...
    async def validate_mapping(...) -> list[Diagnostic]: ...
    async def validate_actions(...) -> list[Diagnostic]: ...
    async def simulate(...) -> SimulationResult: ...
    async def apply(...) -> ExecutionResult: ...
    async def reconcile(...) -> ReconciliationResult: ...
```

Reference data describes available target objects. Capabilities describe supported behavior and constraints. Customer state describes what is currently configured.

Billing and entitlement simulators keep independently versioned state and are accessible to the compiler only through adapters. The obligation ledger is the initial destination for support and onboarding commitments.

## 6. Compilation workflows

### Baseline activation

```text
Load case
  -> capture relevant target snapshots
  -> parse and relate documents
  -> construct source-cited Contract Intent IR
  -> search target entities and reviewed mappings
  -> propose and validate mappings
  -> validate intent and cross-domain invariants
  -> interrupt for material interpretation, mapping, or policy gaps
  -> compute affected-domain plan
  -> simulate and return for authorization
```

### Amendment

```text
Load accepted prior intent, mappings, and evidence
  -> capture current target snapshots
  -> interpret amendment authority and changed terms
  -> create amended intent version
  -> compute semantic change set
  -> build affected operational impact graph
  -> revalidate affected mappings and domains
  -> produce minimal delta plan
  -> simulate and return for authorization
```

Execution and reconciliation remain application-controlled stages. The model receives no mutation tool.

## 7. Persistence direction

The detailed relational schema, aggregate ownership, tenant boundaries, and migration sequence
are defined in `docs/context/schema-design.md`.

The initial relational design should cover:

- Organizations, users, memberships, and customers
- Cases, case lineage, runs, and audit events
- Documents, versions, relationships, parsed items, and source spans
- Connector instances and encrypted credential references
- Reference-data, capability, and customer-state snapshot versions
- Capability entities and relationships
- Contract Intent IR versions and diagnostics
- Operational mappings, versions, and decisions
- Organization policy versions
- Obligations and obligation versions
- Semantic change sets and impact graphs
- Plans, actions, simulations, authorizations, executions, receipts, and reconciliation
- LangGraph checkpoint ownership

Identity, tenancy, lifecycle, relationships, and commonly queried state remain relational. Large immutable artifacts may use versioned JSONB with schema versions and content hashes.

Feature tables and migrations are added with the vertical slice that uses them rather than creating the complete schema upfront.

## 8. Database security

- `enact_owner` owns application objects and cannot log in.
- `enact_migrate` explicitly assumes `enact_owner` for reviewed migrations.
- `enact_app` receives only runtime DML and function privileges and cannot bypass RLS or perform DDL.
- Tenant-owned rows carry `organization_id` and use `ENABLE` plus `FORCE ROW LEVEL SECURITY` with `USING` and `WITH CHECK` policies.
- FastAPI sets transaction-local tenant context inside the same transaction as every query.
- Foreign keys and uniqueness constraints enforce organization boundaries.
- Checkpoint ownership maps LangGraph threads to tenant-owned cases.
- Connector credentials are unavailable to models and are accessed only by bounded connector services.

## 9. API and web direction

The resource model centers on:

```text
/organizations
/connections
/mappings
/policies
/cases
/cases/{id}/documents
/cases/{id}/intent
/cases/{id}/capabilities
/cases/{id}/mappings
/cases/{id}/diagnostics
/cases/{id}/impact
/cases/{id}/plan
/cases/{id}/simulation
/cases/{id}/execution
/cases/{id}/reconciliation
/cases/{id}/evidence
```

The generated TypeScript client is the browser's API boundary. The UI centers on a case workspace with document evidence, discovered context, mapping review, decisions, intent and amendment diffs, affected state, execution, reconciliation, and timeline views. Administration is limited to connections, explicit policies, and reusable mappings.

## 10. Testing and evaluation

Each vertical slice includes unit, integration, API, UI, tenant-isolation, and relevant end-to-end tests before the next slice begins.

Critical test properties include:

- Immutable and reproducible snapshots
- Adapter contract compliance
- Mapping scope and invalidation
- Structured model output validation
- Billing arithmetic and entitlement compatibility
- Billing-entitlement quantity and scope agreement
- Affected-domain selection and delta minimality
- Idempotency, stale-version rejection, failure recovery, and reconciliation
- Complete evidence provenance

Evaluation compares fixed extraction and mapping, a single-pass structured model, and the bounded compiler. It measures citations, discovery coverage, mapping accuracy and reuse, human questions, amendment impact, preservation of unaffected state, reconciliation, cost, and latency.

## 11. Security, trust, and observability

Documents and connector responses are untrusted input. Enforce upload limits, type checks, conversion diagnostics, preview sanitization, connector allowlists, bounded reads, secret isolation, tenant authorization, and audit events for decisions and mapping promotion.

Structured logs include request, case, run, graph-node, connector, snapshot, model, plan, and execution identifiers. Persist timing, token use, discovery coverage, snapshot freshness, validation counts, adapter calls, and reconciliation outcomes without mixing logs with product evidence.

## 12. Repository and deployment

The existing `apps/server`, `apps/web`, `fixtures`, `infra`, `scripts`, and `docs` structure remains. Server modules are introduced only when their slice requires them and remain feature-oriented with explicit interfaces and dependency injection.

Docker Compose provides web, API, PostgreSQL, and object storage. Local model or worker services are optional profiles added only when justified. Production images remain multi-stage and exclude fixtures, tests, documentation, and development dependencies.

## 13. Delivery method

After the database foundation, implementation proceeds as complete vertical slices. A slice includes its migration, domain model, services, adapter or storage boundary, API, generated client, UI, tests, evidence, and documentation needed to operate it. Backend layers are not accumulated for several milestones before exposing a usable workflow.

The slice order is:

1. Case and document intake
2. Operational discovery and snapshots
3. Contract intent compilation
4. Mapping and clarification
5. Baseline planning, execution, and reconciliation
6. Amendment change compilation
7. Evaluation and hardening

## 14. Confirmed decisions

1. React/Vite calls FastAPI directly; there is no BFF.
2. FastAPI with LangGraph Python remains a modular monolith.
3. Python 3.13, root uv, app-local pnpm, and pre-commit remain the toolchain.
4. PostgreSQL, scoped roles, RLS, Alembic, and MinIO remain foundational.
5. Contract Intent IR and target-system representations remain separate.
6. Billing and entitlements receive full adapters; support and onboarding initially become generic obligations.
7. Operational context is discovered from adapters and imported artifacts rather than duplicated through broad configuration.
8. Compilation uses immutable operational snapshots.
9. Mapping reuse is explicit, scoped, reviewable, and invalidatable.
10. Amendment delta compilation is the signature demonstration.
11. Models cannot authorize or execute target mutations.
12. Workers and multiple agents require measured evidence.
