# Enact Technical Implementation Plan

**Status:** Accepted implementation baseline  
**Related product requirements:** `docs/context/prd.md`  
**Scope:** Initial contract activation, with amendments reserved for a supplemental phase

## 1. Purpose

This document proposes the technical architecture, implementation boundaries, repository structure, and delivery sequence for Enact. It is intentionally reviewable: decisions that still require validation are identified explicitly rather than hidden in implementation assumptions.

The plan optimizes for four goals:

1. Demonstrate credible agent engineering in a real operational workflow.
2. Treat billing, entitlements, support, and onboarding as equal operational domains.
3. Run locally without paid infrastructure through Docker Compose.
4. Remain understandable and deployment-ready without introducing services, workers, or multi-agent complexity before a measured need exists.

## 2. Proposed architecture

### 2.1 Application topology

```text
Browser
  │
  ├── React/Vite web application
  │     ├── Deal desk workspace
  │     ├── Organization administration
  │     ├── Source and evidence viewer
  │     └── Generated FastAPI client
  │
  └── FastAPI application API
        ├── Activation and document services
        ├── Docling document processor
        ├── LangGraph compilation workflow
        ├── Deterministic domain services
        ├── Policy and approval services
        ├── Simulated target adapters
        ├── Execution and reconciliation
        └── Evidence and evaluation services
              │
              ├── PostgreSQL
              ├── S3-compatible document storage
              └── Configurable LLM provider
```

The browser communicates directly with FastAPI. The React application is a static client and does not introduce a backend-for-frontend. FastAPI is the sole owner of application data and operational mutations.

### 2.2 Proposed technology stack

| Concern | Proposed technology | Rationale |
|---|---|---|
| Web application | React, Vite, and TypeScript | Keeps the frontend focused on the workflow-heavy product experience while FastAPI owns all server behavior |
| API | FastAPI | Strong typed Python boundary, generated OpenAPI, and natural integration with document and agent libraries |
| Agent orchestration | LangGraph Python | Existing expertise, persisted interrupts, explicit state transitions, and controlled deterministic/agentic composition |
| Schemas | Pydantic on the backend; generated TypeScript API types | Backend remains authoritative while avoiding hand-maintained cross-language request models |
| Relational persistence | PostgreSQL | Durable application state, audit records, JSON support, and LangGraph checkpoint storage |
| Migrations | Alembic | Versioned and reproducible database changes |
| Database access control | Scoped PostgreSQL roles and row-level security | Separates deployment-time DDL from runtime DML and provides defense-in-depth tenant isolation |
| ORM/data access | SQLAlchemy 2.x | Explicit transactions and broad PostgreSQL support |
| Document conversion | Docling behind an internal interface | Layout-aware PDF processing, tables, OCR options, and source geometry |
| Object storage | S3-compatible interface with MinIO locally | Keeps uploaded PDFs outside relational rows and supports local/deployed parity |
| Local model runtime | Provider abstraction with Ollama as an optional local implementation | Allows zero-cost local execution without coupling the workflow to one model provider |
| Python package management | `uv` | Fast, reproducible Python dependency and environment management |
| JavaScript package management | `pnpm` | Efficient monorepo dependency management |
| Backend tests | pytest | Unit, integration, adapter-contract, and evaluation tests |
| Frontend tests | Vitest and Playwright | Component logic and end-to-end workflow coverage |

Exact dependency versions will be pinned when the repository is scaffolded. Individual Docling model licenses must be reviewed before selecting the default OCR and layout models.

### 2.3 Deliberate exclusions

The initial architecture will not include:

- A backend-for-frontend proxy
- Separate services for operational domains
- Separate simulated target-system deployments
- Temporal, Celery, Redis, Kafka, or another workflow/message runtime
- Live billing, entitlement, support, or onboarding integrations
- A vector database unless evaluation demonstrates a retrieval need that PostgreSQL cannot meet

## 3. Durable workflow execution

Enact will begin with request-driven execution. A worker and queue may be introduced for a specific stage if runtime measurements or reliability requirements demonstrate that request-bound execution is unsuitable. Worker adoption is therefore an implementation decision made per workload, not a project-wide prohibition or default.

### 3.1 Execution behavior

1. The client starts or resumes compilation through a FastAPI endpoint.
2. FastAPI invokes the LangGraph workflow in the request lifecycle.
3. Each significant graph step writes a checkpoint and persists material domain artifacts.
4. The request returns when the graph completes, reaches a human interrupt, or encounters a recoverable failure.
5. A clarification, approval, or retry request invokes the graph again using the same activation and LangGraph thread identifiers.

The graph does not continue running when no request is active. Durability means that it resumes safely from persisted state; it does not mean that work continues in the background.

This behavior describes the initial implementation. If a stage moves to a worker, its persisted state, idempotency guarantees, progress events, and resume semantics must remain the same from the product's perspective.

### 3.2 Criteria for introducing a worker

A worker should be added only when a named stage demonstrates one or more of these characteristics:

- Typical or worst-case runtime exceeds practical HTTP request limits.
- CPU- or memory-intensive work, such as OCR or document conversion, degrades API responsiveness.
- Work must continue reliably after the initiating browser or API connection closes.
- Independent concurrency limits, retries, cancellation, or resource isolation are required.
- Deployment infrastructure imposes request-duration limits that checkpointing alone cannot address.

Document conversion and OCR are the first candidates to evaluate. Compilation, execution, and reconciliation remain request-driven unless their own measurements justify moving them. Introducing one worker does not require converting every stage to asynchronous processing.

### 3.3 Progress delivery

The proposed default is Server-Sent Events for compilation progress. The API streams coarse-grained workflow events such as document conversion completed, terms extracted, validation completed, or decision required. The UI also reads persisted activation state, so correctness does not depend on the stream remaining connected.

If streaming adds too much initial complexity, the first vertical slice may use a blocking compile endpoint followed by ordinary status reads. This should be decided during the architecture spike.

### 3.4 Interruption and recovery

- LangGraph checkpoints preserve graph execution state.
- Application tables preserve authoritative activation, diagnostic, decision, plan, and execution state.
- A dropped request may be resumed from the last successful checkpoint.
- Nodes that invoke models or external adapters must be safe to retry.
- Side-effecting actions require idempotency keys and must not execute before authorization.
- A stale compilation attempt must not overwrite a newer activation version.

## 4. Backend module boundaries

The backend will be a modular monolith. Modules communicate through typed service interfaces rather than HTTP calls.

### 4.1 Organizations

Owns organization configuration and configuration versions:

- Product and plan catalog
- Billing rules and price policies
- Entitlement compatibility and limits
- Support tiers and SLA policies
- Onboarding templates and ownership rules
- Document types and precedence policies
- Approval and exception policies

The initial demo organization will be seeded from version-controlled fixtures. Administrative editing can be added incrementally after the configuration schema is stable.

### 4.2 Activations

Owns the aggregate lifecycle:

- Customer and deal identity
- Current lifecycle state
- Active source-bundle version
- Organization-configuration version
- Current compilation version
- Concurrency version
- Terminal and retryable failure state

### 4.3 Documents

Owns:

- PDF storage and hashes
- Extracted document representation
- Pages, document items, and source spans
- Document classification
- Document relationships and precedence
- Conversion quality diagnostics

### 4.4 COIR

Owns versioned Contract Operational Intermediate Representations. It exposes schemas and services but does not call the model itself.

The COIR will contain common metadata plus equal first-class sections for:

- Billing
- Entitlements
- Support
- Onboarding

The exact COIR schema must be specified in `docs/context/coir-specification.md` before implementation of the compiler or adapters.

### 4.5 Validation

Owns deterministic validation and compiler diagnostics:

- Structural schema validation
- Date and period consistency
- Billing arithmetic and policy checks
- Entitlement compatibility and quota checks
- Support coverage and SLA checks
- Onboarding dependency and due-date checks
- Provenance completeness
- Required-configuration checks

Validation returns typed diagnostics and never silently repairs COIR values.

### 4.6 Policies and decisions

Owns deterministic classification of findings as:

- Standard and automatically authorized
- Warning
- Policy exception requiring a grouped decision
- Unsupported or ambiguous issue requiring clarification
- Blocking error

Policy evaluation operates on typed proposed changes and organization configuration. It is not delegated to the model.

### 4.7 Planning

Compiles validated COIR into a target-neutral dependency graph and then into target-specific actions. Planning owns action ordering, preconditions, expected before/after state, and impact summaries.

### 4.8 Adapters

Provides one adapter for each equal MVP domain. Adapters are modules in the FastAPI deployment, not separate services.

Each adapter implements the conceptual contract:

```python
class OperationalAdapter(Protocol):
    domain: OperationalDomain

    def read_state(self, customer_id: UUID) -> TargetState: ...
    def validate(self, actions: list[PlanAction]) -> list[Diagnostic]: ...
    def simulate(self, actions: list[PlanAction]) -> SimulationResult: ...
    def apply(self, actions: list[PlanAction], idempotency_key: str) -> ExecutionResult: ...
    def reconcile(self, intended: TargetState, actual: TargetState) -> ReconciliationResult: ...
```

The simulated adapters persist their own target state in dedicated PostgreSQL tables or schemas. They must behave like external systems by enforcing versions, uniqueness, constraints, and injectable failures.

### 4.9 Evidence

Owns the append-only evidence chain connecting:

```text
Source span
  → Candidate term
  → Interpretation or decision
  → COIR field
  → Diagnostic
  → Plan action
  → Authorization
  → Execution receipt
  → Reconciliation result
```

LangGraph checkpoints are runtime records, not the product audit log. User-facing evidence must be modeled independently in application data.

### 4.10 Evaluation

Owns benchmark fixtures, baseline runners, scoring, and reports. Evaluation code should call the same document, validation, planning, and adapter services used by the application.

## 5. Document-processing design

### 5.1 Processor abstraction

The compiler will depend on an internal interface rather than Docling-specific objects:

```python
class DocumentProcessor(Protocol):
    def process(self, document: StoredDocument) -> ParsedDocument: ...
```

`ParsedDocument` must preserve:

- Document and content hashes
- Page dimensions
- Ordered document items
- Item type such as heading, paragraph, list, or table
- Extracted text
- Page number
- Bounding box
- Character span when available
- Parent/child hierarchy
- Conversion strategy and model versions
- OCR usage
- Conversion warnings and quality signals

### 5.2 Proposed processing strategy

1. Validate file type, size, and encryption status.
2. Hash and store the original PDF.
3. Attempt born-digital extraction and layout conversion.
4. Measure text coverage and conversion quality by page.
5. Use OCR only for pages that require it, if the selected Docling configuration supports reliable partial fallback.
6. Normalize output into the internal `ParsedDocument` schema.
7. Store source items and geometry before any LLM call.
8. Create retrieval units that retain references to their original source items.

Document text is untrusted data. Instructions found inside a contract must never alter the agent’s tool permissions or system behavior.

### 5.3 Required document spike

Before the application commits to Docling, compare it against the minimum viable alternative on representative PDFs:

- Clean born-digital order form
- Multi-page MSA with headers, footers, and defined terms
- Pricing table
- Support schedule
- Onboarding SOW
- Scanned or mixed-content PDF
- Deliberately malformed or encrypted PDF

Measure text coverage, reading order, table fidelity, provenance quality, processing time, memory use, Docker image size, and licensing constraints. The result should be recorded as an architecture decision record.

## 6. Agent and LangGraph design

### 6.1 Initial orchestration model

The initial implementation will use one orchestrating graph because the required workflow can first be expressed as explicit nodes, tools, and deterministic services. Domain-specific extraction may use separate prompts or graph nodes.

This is an initial implementation choice, not a permanent restriction. The architecture may introduce multiple cooperating agents if evaluation shows that independently scoped context, reasoning, tools, or iteration materially improves quality or maintainability. Any such decomposition must preserve shared workflow state, bounded authority, deterministic validation, provenance, budgets, and a clear coordinating owner.

### 6.2 Proposed graph

```text
Load activation context
  → Inspect document bundle
  → Classify documents and propose relationships
  → Extract source-grounded candidate terms
  → Resolve definitions and cross-references
  → Propose document precedence applications
  → Construct candidate COIR
  → Run deterministic validation
      ├── Repairable diagnostic → revise candidate COIR within budget
      ├── Unsupported ambiguity → grouped clarification interrupt
      ├── Policy exception → continue and attach decision requirement
      └── Valid → compile activation plan
  → Simulate all four domains
  → Group exceptional decisions
      ├── Decision required → approval interrupt
      └── No decision required → authorize standard actions
  → Return ready-to-apply plan
```

Execution and reconciliation are application-controlled stages invoked after plan authorization. The model does not receive a general-purpose mutation tool.

### 6.3 Agent tools

Initial read-only or deterministic tools:

- Read document items and source spans
- Search within the contract bundle
- Retrieve document relationships and precedence policy
- Retrieve organization catalog and domain policies
- Retrieve current simulated target state
- Validate a candidate COIR
- Explain deterministic diagnostics
- Simulate a candidate plan

Tools return typed results and enforce organization and activation scope. The agent cannot query arbitrary database tables, execute code, write files, or call target-system mutation operations.

### 6.4 Structured output

All operational model output must validate against Pydantic schemas. Free-form model text may be stored as an explanation, but it cannot become executable state without typed parsing and deterministic validation.

### 6.5 Budgets and termination

The graph will enforce configurable limits for:

- Model calls per compilation
- Validation-repair loops
- Tool calls
- Input and output tokens
- Per-call timeout
- Total request duration

Exhausting a budget produces a visible diagnostic and resumable failure state rather than an unbounded retry.

### 6.6 Model-provider abstraction

Prompts and graph nodes depend on a small internal model interface. The application must support at least one zero-cost local path. Provider-specific structured-output behavior will be normalized and tested behind the interface.

## 7. Document precedence

Document precedence will combine agent proposals with deterministic resolution.

1. The agent identifies candidate document types, explicit supersession language, and term-level conflicts with citations.
2. The precedence service applies organization-configured rules.
3. Explicit, scoped amendments override only affected terms and periods.
4. Specific terms may override general terms when scope and authority match.
5. Recency is used only when policy permits and authority is equivalent.
6. Unresolved conflicts become clarification diagnostics.

Every resolution stores the competing source terms, selected term, rule applied, effective scope, and decision provenance.

## 8. Approval and execution design

### 8.1 Grouped decisions

The policy service evaluates the complete proposed plan and groups related exceptions into a small set of decision cases. Standard actions remain visible but do not require manual confirmation.

A decision case contains:

- Reason and policy rule
- Affected domains and actions
- Source evidence
- Operational impact
- Proposed resolution
- Allowed responses

Clarification and approval are separate concepts. Clarification supplies missing meaning; approval authorizes a known policy exception.

### 8.2 Execution safeguards

- Only the execution service can call adapter `apply` methods.
- The current plan hash and authorization version must match.
- Each action has a stable idempotency key.
- Each adapter checks expected target-state version before applying.
- Receipts are stored before advancing the activation state.
- Partial failure produces a recoverable state with completed and pending actions identified.
- Compensation is implemented only where the simulated domain supports a meaningful inverse action.

### 8.3 Reconciliation

After application, each adapter reads actual state and compares it with intended state. A successful write response is not considered completion. Activation becomes active only after required state reconciles or an authorized user accepts a documented deviation.

## 9. Persistence model

The initial schema is expected to include these aggregates or tables:

- `organizations`
- `organization_configuration_versions`
- `users` and `organization_memberships`
- `customers`
- `activations`
- `activation_runs`
- `documents`
- `document_versions`
- `document_items`
- `document_relationships`
- `source_spans`
- `candidate_terms`
- `coir_versions`
- `diagnostics`
- `decision_cases`
- `decisions`
- `activation_plans`
- `plan_actions`
- `simulation_runs`
- `execution_runs`
- `execution_receipts`
- `reconciliation_runs`
- `reconciliation_findings`
- `audit_events`
- Four sets of simulated target-state tables
- LangGraph checkpoint tables

Large structured snapshots such as COIR versions and plans may use JSONB while identity, lifecycle, relationships, and frequently queried fields remain relational. Snapshots must include schema versions and content hashes.

### 9.1 PostgreSQL roles and privileges

Database access will use separate credentials and least-privilege roles:

- `enact_owner` is a `NOLOGIN` role that owns application schemas, tables, policies, and functions.
- `enact_migrate` is the deployment-time login. It receives non-inheriting membership in `enact_owner` and explicitly uses `SET ROLE enact_owner` to run reviewed Alembic migrations, but it is not available to the running application.
- `enact_app` is the runtime login used by FastAPI and, unless a later workload requires a narrower role, any worker. It receives only the required schema usage, table DML, sequence usage, and function execution privileges. It cannot create or alter application objects, bypass RLS, assume `enact_owner`, or assume `enact_migrate`.
- A bootstrap administrator creates the database and roles for local or deployed environments, then has no part in normal application operation.

Migrations must revoke unnecessary `PUBLIC` access and explicitly grant privileges for new objects or configure owner-level default privileges. Application startup must not run migrations automatically. Docker Compose will use separate migration and runtime credentials rather than a shared PostgreSQL superuser credential.

If later components require materially different access—for example, a document processor that only updates conversion records—they should receive narrower roles instead of reusing migration privileges.

### 9.2 Tenant isolation and row-level security

Every organization-owned application table will carry an `organization_id` directly, including child records where practical. Foreign keys and uniqueness constraints must include or otherwise enforce organization boundaries so a row cannot reference another organization's aggregate.

FastAPI will authenticate the caller, establish the authorized organization, begin a database transaction, and set a transaction-local tenant context such as:

```sql
SET LOCAL app.organization_id = '00000000-0000-0000-0000-000000000000';
```

RLS policies will compare each tenant-owned row with the transaction-local organization identifier, using both `USING` rules for row visibility and `WITH CHECK` rules for inserts and updates. Tenant tables will use both `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`. `enact_app` will not have `BYPASSRLS` and will not own the protected tables. Missing or invalid tenant context must fail closed and expose no tenant rows.

RLS is defense in depth, not a replacement for authorization. API services and LangGraph tools must still validate organization membership and resource scope before querying or mutating data. System-wide reference tables must be explicitly classified and documented rather than silently excluded from RLS.

Connection-pool safety is mandatory: tenant context must be set with `SET LOCAL` inside the same transaction as the queries, never as persistent session state. Background or resumed processing must derive organization context from a trusted persisted activation mapping rather than model output or an arbitrary client-supplied thread identifier.

LangGraph checkpoint tables require an explicit isolation design during the persistence spike. The preferred design is to map every graph `thread_id` to an organization-owned activation and apply RLS-compatible policies to checkpoint access. If the selected checkpointer schema cannot enforce this safely, checkpoint access must be wrapped by a tenant-aware persistence adapter before multi-tenant workflows are enabled.

## 10. API outline

The first API surface should include:

```text
POST   /organizations
GET    /organizations/{id}/configuration
PUT    /organizations/{id}/configuration

POST   /activations
GET    /activations
GET    /activations/{id}
POST   /activations/{id}/documents
GET    /activations/{id}/documents
GET    /activations/{id}/evidence

POST   /activations/{id}/compile
POST   /activations/{id}/resume
GET    /activations/{id}/runs/{run_id}/events

GET    /activations/{id}/coir
GET    /activations/{id}/diagnostics
POST   /activations/{id}/decisions

GET    /activations/{id}/plan
POST   /activations/{id}/simulate
POST   /activations/{id}/apply
POST   /activations/{id}/reconcile

GET    /activations/{id}/timeline
```

The exact resource model and status codes will be defined through the OpenAPI contract before frontend implementation. Mutating endpoints accept idempotency keys where retries could duplicate work.

## 11. Frontend implementation

### 11.1 Primary routes

```text
/activations
/activations/new
/activations/:activationId
/activations/:activationId/documents
/activations/:activationId/terms
/activations/:activationId/diagnostics
/activations/:activationId/plan
/activations/:activationId/reconciliation
/admin/configuration
/evaluations
```

### 11.2 Activation workspace

The activation detail route should use one persistent workspace with navigation between:

- Bundle and precedence
- Source-grounded terms
- COIR
- Diagnostics and decisions
- Cross-domain plan
- Execution and reconciliation
- Evidence timeline

The four domains must use equal visual weight in summaries and plan views.

### 11.3 API access

- Generate a TypeScript client from FastAPI OpenAPI.
- Keep transport models separate from presentation view models.
- Do not access PostgreSQL from the frontend.
- Do not duplicate validation rules in the frontend.
- Use browser-to-FastAPI requests with explicit CORS configuration.
- Keep authentication portable so a same-origin ingress can be introduced later without a BFF.

## 12. Repository structure

```text
apps/
  api/
    src/enact/
      api/
      organizations/
      activations/
      documents/
      agent/
      coir/
      validation/
      policies/
      planning/
      adapters/
        billing/
        entitlements/
        support/
        onboarding/
      execution/
      reconciliation/
      evidence/
      evaluation/
    tests/
  web/
    src/
      routes/
      features/
      components/
      api/generated/
      lib/
    tests/
packages/
  benchmark-fixtures/
  organization-fixtures/
docs/
  context/
  reference/
infra/
  docker/
compose.yaml
```

Cross-language contracts are shared through OpenAPI and versioned JSON fixture schemas, not through a source-code package imported by both runtimes.

## 13. Testing and evaluation strategy

### 13.1 Test layers

- Unit tests for deterministic rules, precedence, policy evaluation, dates, arithmetic, and diffing
- Schema tests for every structured model output
- Document fixture tests for extraction and provenance
- Graph-node tests with deterministic fake models and tools
- Graph-path tests for valid, repair, clarification, approval, and failure branches
- Adapter contract tests reused by all four adapters
- Idempotency and optimistic-concurrency tests
- Database privilege tests proving `enact_app` cannot perform DDL, assume privileged roles, or bypass RLS
- Cross-tenant isolation tests for reads, inserts, updates, deletes, joins, graph checkpoints, and resumed runs
- Connection-pool tests proving tenant context cannot leak between transactions
- API integration tests against PostgreSQL and object storage
- Playwright end-to-end tests for the primary activation workflow
- Benchmark runs against fixed ground truth

### 13.2 Baselines

Implement three comparable compilation paths:

1. Fixed extraction-and-mapping pipeline
2. Single-pass structured LLM pipeline
3. Bounded LangGraph compiler with deterministic validation and replanning

All paths consume the same parsed documents and organization configuration and produce the same COIR schema.

### 13.3 Primary metrics

Citation accuracy should score at least:

- Correct document
- Correct page
- Source-span overlap or accepted clause match
- Whether the citation actually entails the operational claim

Successful activation should require:

- Correct final COIR for all four domains
- Correct blocking and exception behavior
- Correct target plan
- Successful idempotent execution
- Reconciled final state

Exact thresholds will be chosen after an initial benchmark establishes realistic baselines.

## 14. Security and trust boundaries

The MVP must include visible safeguards even when using synthetic data:

- Organization-scoped authorization checks in every service and tool, backed by PostgreSQL RLS
- Separate migration and runtime database credentials with no superuser or `BYPASSRLS` access at runtime
- File-size, file-type, and page-count limits
- PDF encryption and conversion-failure diagnostics
- Original document hashing
- Escaping and sanitization in document previews
- Contract content treated as untrusted input, including prompt-injection text
- No model access to secrets or unrestricted network tools
- No model-controlled SQL, filesystem, or adapter mutation
- Audit events for configuration changes, decisions, and execution
- Secrets supplied through environment variables and excluded from source control

## 15. Observability

The local system should provide useful diagnostics without requiring paid telemetry:

- Structured JSON logs with activation, run, graph-node, and request identifiers
- Persisted graph-node timing and result metadata
- Model provider, model identifier, token usage, latency, and retry count
- Document conversion strategy and duration
- Validation and policy diagnostic counts
- Adapter calls and reconciliation outcomes
- Optional OpenTelemetry export
- Optional LangSmith integration, disabled by default

The product audit trail and operational logs are separate concerns.

## 16. Docker Compose topology

```text
web          React/Vite application served as static assets
api          FastAPI, LangGraph, Docling, and domain services
postgres     Application data and LangGraph checkpoints
object-store S3-compatible local document storage
ollama       Optional profile for local model execution
```

The initial topology has no worker service. If a measured stage requires one, Compose will add a worker and the minimum queueing infrastructure needed for that stage. The API image must include or reproducibly obtain the selected local document models. Development and deployment configurations should use the same service interfaces even when credentials, execution modes, or storage implementations differ.

## 17. Implementation sequence

Each milestone should end in a demonstrable vertical outcome rather than isolated infrastructure.

### Milestone 0: Resolve foundational specifications

Deliver:

- One complete reference contract bundle and manually authored ground truth
- COIR specification
- Organization-configuration specification
- Activation lifecycle and graph-state specification
- Adapter contract specification
- Document-processing spike and architecture decision
- Initial evaluation fixture format

Exit condition: one contract can be represented manually from PDF source spans through expected target states across all four domains.

### Milestone 1: Repository and runtime foundation

Deliver:

- Monorepo structure
- React/Vite and FastAPI applications
- PostgreSQL migrations
- Scoped PostgreSQL roles, grants, and RLS policies
- Object-storage abstraction
- Docker Compose environment
- OpenAPI client generation
- Seeded organization and customer
- Continuous integration for linting, type checking, and tests

Exit condition: the browser can create and retrieve an empty activation through the generated API client, while automated tests prove that the runtime role cannot perform DDL or access another organization's rows.

### Milestone 2: Contract intake and evidence

Deliver:

- Multi-PDF upload
- Hashing and object storage
- Docling integration through `DocumentProcessor`
- Parsed document, page, item, and provenance persistence
- Document preview and source-item inspection
- Extraction quality diagnostics

Exit condition: a user can upload the reference bundle and inspect normalized text and source geometry for every material clause.

### Milestone 3: Deterministic domain foundation

Deliver:

- Versioned COIR Pydantic schemas
- Organization configuration for all four domains
- Deterministic validators
- Diagnostic types and display
- Manually loaded reference COIR

Exit condition: the manually authored reference COIR produces expected errors, warnings, exceptions, and valid results without an LLM.

### Milestone 4: Source-grounded compilation

Deliver:

- LangGraph state and PostgreSQL checkpointer
- Document and organization-context tools
- Structured candidate-term extraction
- Cross-reference and precedence proposal
- Candidate COIR construction
- Validation-repair loop with budgets
- Clarification interrupt

Exit condition: the reference bundle compiles into a source-cited candidate COIR and pauses rather than inventing an unsupported material term.

### Milestone 5: Planning and four-domain simulation

Deliver:

- Target-neutral action graph
- Billing adapter and simulator
- Entitlements adapter and simulator
- Support adapter and simulator
- Onboarding adapter and simulator
- Before/after diff and dependency view
- Failure injection controls

Exit condition: one validated COIR produces a coordinated, simulated plan with meaningful changes in every domain.

### Milestone 6: Grouped decisions and safe execution

Deliver:

- Configurable policy evaluation
- Grouped clarification and approval cases
- Human decision persistence and graph resume
- Idempotent apply operations
- Optimistic concurrency
- Partial-failure recovery
- Execution receipts

Exit condition: standard actions proceed without individual approval while one configured exception pauses, resumes, and executes exactly once.

### Milestone 7: Reconciliation and evidence experience

Deliver:

- Intended-versus-actual reconciliation for all adapters
- Mismatch attribution
- Activation completion rules
- Complete evidence timeline
- Source-to-result navigation
- Main activation queue and workspace polish

Exit condition: a reviewer can explain why each final price, entitlement, support commitment, and onboarding task exists and verify its actual state.

### Milestone 8: Evaluation and deployment hardening

Deliver:

- Ground-truth fixture suite
- Three baseline implementations
- Citation and activation scoring
- Cost and latency reporting
- End-to-end recovery scenarios
- Container hardening and deployment documentation
- Portfolio demo script and seeded failure scenario

Exit condition: benchmark results show where the agentic approach improves or fails relative to simpler baselines, and the complete demo runs through Docker Compose.

### Supplemental milestone: Amendments

Begin only after the initial activation acceptance criteria are satisfied.

Deliver:

- Amendment document relationships
- Prior and amended COIR comparison
- Impact graph
- Minimal delta plan
- Delta authorization, execution, and reconciliation
- Evidence linking original and amended terms

## 18. Principal risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Inline processing exceeds practical request duration | Interrupted user workflow | Keep stages resumable, measure runtime, enforce budgets, and move only the affected stage to a worker when Section 3.2 criteria are met |
| Request disconnect cancels current work | Partial compilation | Persist checkpoints and artifacts after each significant step; expose explicit resume and introduce background execution if continuity becomes a requirement |
| Docling is too heavy or inaccurate for contract fixtures | Poor citations or large image | Complete the document spike before coupling the compiler to Docling objects |
| OCR produces plausible but incorrect text | Unsupported operational claims | Record OCR provenance, expose source images, lower trust, and require clarification for material uncertain terms |
| Cross-language API contracts drift | Frontend/backend defects | Generate the TypeScript client in CI and fail on uncommitted contract changes |
| Local models cannot produce reliable structured output | Unstable compilation | Maintain provider abstraction, strict validation, repair budgets, and benchmark model candidates |
| Agent absorbs deterministic responsibilities | Unsafe or irreproducible behavior | Keep arithmetic, policies, planning, execution, and reconciliation in ordinary services |
| Four-domain scope becomes shallow | Weak portfolio story | Use one complete reference scenario with nontrivial behavior and tests in every domain |
| Approval design creates excessive manual work | Product contradicts its purpose | Auto-authorize standard changes and group only material exceptions |
| Simulators feel like simple CRUD tables | Weak operational demonstration | Enforce realistic constraints, version conflicts, idempotency, partial failures, and reconciliation mismatches |

## 19. Confirmed architecture decisions

The following decisions form the accepted implementation baseline. They may be revised later when feature work or measured evidence justifies a change; material revisions must be recorded in an architecture decision record and reflected in this plan.

1. Use React/Vite for the frontend and FastAPI with LangGraph Python for the backend.
2. Let the browser call FastAPI directly; do not create a BFF or second server layer.
3. Begin with request-driven, resumable processing; introduce a worker only for a stage that meets the criteria in Section 3.2.
4. Use Docling as the first document-processing candidate, subject to a fixture spike.
5. Include OCR capability in the architecture but activate it only where extraction quality requires it.
6. Use PostgreSQL for both application state and LangGraph checkpoints.
7. Use `enact_owner`, `enact_migrate`, and `enact_app` roles with distinct ownership, migration, and runtime privileges.
8. Require RLS for tenant-owned tables and a verified tenant-isolation design for LangGraph checkpoints.
9. Use S3-compatible document storage with MinIO locally.
10. Begin with one bounded LangGraph compiler; evaluate multi-agent decomposition later if measured complexity or quality warrants it.
11. Implement all four target systems as modules and simulated stores in one backend deployment.
12. Use a generated OpenAPI TypeScript client as the cross-language contract.
13. Use SSE for progress if the initial spike shows it is worth the added complexity.
14. Keep authentication realistic but small enough not to dominate the portfolio project.
