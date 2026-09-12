# Enact Execution Plan

Related: `docs/context/prd.md`, `docs/context/implementation-plan.md`

## WP0 — Repository Scaffold

- [x] **WP0.1** Establish the root uv workspace, Python 3.13 toolchain, repository layout, and shared pre-commit hooks.
- [x] **WP0.2** Scaffold the FastAPI server package with versioned API composition, Alembic, and unit and integration test boundaries.
- [x] **WP0.3** Scaffold the React/Vite application with TypeScript, app-local pnpm, linting, formatting, unit testing, and browser-testing configuration.
- [x] **WP0.4** Add the manually dispatched frontend and backend CI baseline.
- [x] **WP0.5** Add the local Docker Compose topology and optimized production containers for the web application, API, PostgreSQL, and object storage.
- [x] **WP0.6** Verify that the production images build and the scaffolded Docker Compose topology starts successfully.

## WP1 — Reference Scenario and Specifications

- [x] **WP1.1** Define the reference SaaS organization and activation scenario across all four domains.
- [x] **WP1.2** Create the synthetic reference contract PDF bundle.
- [ ] **WP1.3** Author the source-to-target ground-truth fixtures for the reference activation.
- [ ] **WP1.4** Define COIR version 1 in `docs/context/coir-specification.md`.
- [ ] **WP1.5** Define organization configuration version 1 in `docs/context/organization-configuration-specification.md`.
- [ ] **WP1.6** Define activation and graph lifecycles in `docs/context/workflow-specification.md`.
- [ ] **WP1.7** Define target adapter contracts in `docs/context/adapter-specification.md`.
- [ ] **WP1.8** Define benchmark fixtures and scoring in `docs/context/evaluation-specification.md`.
- [ ] **WP1.9** Evaluate Docling and the minimum viable alternative against representative PDFs.
- [ ] **WP1.10** Record the document-processing architecture decision.

## WP2 — Runtime and Tenant Security

- [ ] **WP2.1** Add typed backend configuration, liveness, and readiness endpoints.
- [ ] **WP2.2** Add the React application shell, routing, and global error handling.
- [x] **WP2.3** Bootstrap `enact_owner`, `enact_migrate`, and `enact_app` with scoped privileges.
- [ ] **WP2.4** Establish Alembic ownership, grants, and downgrade conventions.
- [ ] **WP2.5** Implement transaction-scoped PostgreSQL tenant context.
- [ ] **WP2.6** Add reusable RLS migration helpers and tenant-isolation tests.
- [ ] **WP2.7** Add the S3-compatible object-storage interface and MinIO implementation.
- [ ] **WP2.8** Establish reproducible OpenAPI TypeScript client generation.
- [ ] **WP2.9** Add structured logging and request correlation.
- [ ] **WP2.10** Extend continuous integration to cover migrations, RLS, and generated contracts.

## WP3 — Organizations, Identity, Configuration, and Activations

- [ ] **WP3.1** Add organization, user, membership, and customer persistence with RLS.
- [ ] **WP3.2** Implement the replaceable authentication boundary.
- [ ] **WP3.3** Implement membership and application-role authorization.
- [ ] **WP3.4** Implement versioned organization-configuration schemas.
- [ ] **WP3.5** Persist immutable organization-configuration versions with RLS.
- [ ] **WP3.6** Seed the reference organization, users, customer, catalogs, and policies.
- [ ] **WP3.7** Expose organization-configuration read APIs.
- [ ] **WP3.8** Add activation and activation-run persistence with lifecycle enforcement and RLS.
- [ ] **WP3.9** Expose activation create, list, and detail APIs.
- [ ] **WP3.10** Build the activation queue and activation creation flow.
- [ ] **WP3.11** Add append-only audit-event persistence with RLS.
- [ ] **WP3.12** Audit configuration and activation lifecycle changes.

## WP4 — Contract Intake and Document Evidence

- [ ] **WP4.1** Add document bundle, document, and document-version persistence with RLS.
- [ ] **WP4.2** Implement secure, idempotent multi-PDF upload to object storage.
- [ ] **WP4.3** Expose document upload, list, metadata, and processing-status APIs.
- [ ] **WP4.4** Build the contract bundle upload interface.
- [ ] **WP4.5** Implement the processor-neutral parsed-document contract.
- [ ] **WP4.6** Integrate the selected document processor behind the processor interface.
- [ ] **WP4.7** Persist parsed pages, items, tables, and source spans with RLS.
- [ ] **WP4.8** Add extraction-quality assessment and selective OCR fallback.
- [ ] **WP4.9** Add typed handling for encrypted, malformed, oversized, and failed PDFs.
- [ ] **WP4.10** Evaluate whether document processing requires a worker and record the decision.
- [ ] **WP4.11** If required, add a document-processing worker and its minimum queue infrastructure.
- [ ] **WP4.12** Add document classification and relationship persistence with RLS.
- [ ] **WP4.13** Expose document classification and relationship correction APIs.
- [ ] **WP4.14** Build the PDF and source-span evidence viewer.
- [ ] **WP4.15** Build the document relationship and precedence editor.

## WP5 — COIR and Deterministic Validation

- [ ] **WP5.1** Implement shared COIR primitives, provenance, and schema versioning.
- [ ] **WP5.2** Implement the billing COIR schema.
- [ ] **WP5.3** Implement the entitlements COIR schema.
- [ ] **WP5.4** Implement the support COIR schema.
- [ ] **WP5.5** Implement the onboarding COIR schema.
- [ ] **WP5.6** Persist immutable COIR versions with RLS.
- [ ] **WP5.7** Implement compiler diagnostic schemas and blocking semantics.
- [ ] **WP5.8** Implement common provenance and temporal validation.
- [ ] **WP5.9** Implement deterministic billing validation.
- [ ] **WP5.10** Implement deterministic entitlement validation.
- [ ] **WP5.11** Implement deterministic support validation.
- [ ] **WP5.12** Implement deterministic onboarding validation.
- [ ] **WP5.13** Implement cross-domain validation.
- [ ] **WP5.14** Load and validate the manually authored reference COIR.
- [ ] **WP5.15** Build the COIR and diagnostics inspector.

## WP6 — Source-Grounded Agentic Compilation

- [ ] **WP6.1** Implement the model-provider abstraction with deterministic fake and local implementations.
- [ ] **WP6.2** Add prompt, model, tool, and compilation-budget versioning.
- [ ] **WP6.3** Implement tenant-safe LangGraph checkpoint persistence.
- [ ] **WP6.4** Implement the typed compilation graph skeleton and termination rules.
- [ ] **WP6.5** Add activation-scoped document retrieval tools.
- [ ] **WP6.6** Add activation-scoped organization-context and target-state tools.
- [ ] **WP6.7** Compile document classifications and relationships into cited proposals.
- [ ] **WP6.8** Extract source-grounded candidate terms for all four domains.
- [ ] **WP6.9** Resolve definitions, cross-references, and document precedence.
- [ ] **WP6.10** Construct immutable candidate COIR versions.
- [ ] **WP6.11** Add the bounded deterministic validation and COIR-revision loop.
- [ ] **WP6.12** Add grouped clarification interrupts and durable resume.
- [ ] **WP6.13** Expose compilation start, resume, status, and event APIs.
- [ ] **WP6.14** Deliver compilation progress through SSE or status polling based on the approved decision.
- [ ] **WP6.15** Build candidate-term review and clarification flows.
- [ ] **WP6.16** Evaluate whether compilation requires background execution and record the decision.
- [ ] **WP6.17** If required, move only the justified compilation stages to a worker.

## WP7 — Cross-Domain Planning and Simulation

- [ ] **WP7.1** Implement the target-neutral action graph.
- [ ] **WP7.2** Implement the adapter protocol and reusable contract test suite.
- [ ] **WP7.3** Implement the billing simulator adapter.
- [ ] **WP7.4** Implement the entitlements simulator adapter.
- [ ] **WP7.5** Implement the support simulator adapter.
- [ ] **WP7.6** Implement the onboarding simulator adapter.
- [ ] **WP7.7** Compile validated COIR into a dependency-aware cross-domain plan.
- [ ] **WP7.8** Persist immutable plan versions and actions with RLS.
- [ ] **WP7.9** Implement whole-plan simulation and before-and-after state capture.
- [ ] **WP7.10** Add controlled validation, version-conflict, partial-failure, and drift scenarios.
- [ ] **WP7.11** Expose plan and simulation APIs.
- [ ] **WP7.12** Build the cross-domain plan and simulation workspace.

## WP8 — Policy Decisions and Safe Execution

- [ ] **WP8.1** Implement versioned approval-policy schemas.
- [ ] **WP8.2** Implement deterministic plan policy evaluation.
- [ ] **WP8.3** Group related clarification and approval cases.
- [ ] **WP8.4** Persist decision cases and immutable responses with RLS.
- [ ] **WP8.5** Expose decision review APIs with stale-plan protection.
- [ ] **WP8.6** Resume compilation and planning after recorded decisions.
- [ ] **WP8.7** Build grouped clarification and exception review.
- [ ] **WP8.8** Implement the execution authorization boundary.
- [ ] **WP8.9** Implement idempotent action execution with optimistic concurrency.
- [ ] **WP8.10** Implement dependency-aware execution and partial-failure state.
- [ ] **WP8.11** Implement execution retry, recovery, and supported compensation.
- [ ] **WP8.12** Persist and expose execution receipts with RLS.
- [ ] **WP8.13** Build execution status and recovery controls.

## WP9 — Reconciliation and Evidence

- [ ] **WP9.1** Implement intended-versus-actual reconciliation primitives.
- [ ] **WP9.2** Add reconciliation behavior to all four adapters.
- [ ] **WP9.3** Attribute reconciliation mismatches to their likely workflow stage.
- [ ] **WP9.4** Persist reconciliation runs and findings with RLS.
- [ ] **WP9.5** Enforce activation completion and accepted-deviation rules.
- [ ] **WP9.6** Expose reconciliation and deviation-acceptance APIs.
- [ ] **WP9.7** Build the reconciliation workspace.
- [ ] **WP9.8** Materialize the complete source-to-result evidence graph.
- [ ] **WP9.9** Expose evidence and timeline APIs.
- [ ] **WP9.10** Build bidirectional source-to-result navigation.
- [ ] **WP9.11** Complete the activation queue and lifecycle workspace.

## WP10 — Evaluation, Hardening, and Portfolio Delivery

- [ ] **WP10.1** Expand the synthetic benchmark suite.
- [ ] **WP10.2** Implement the fixed extraction-and-mapping baseline.
- [ ] **WP10.3** Implement the single-pass structured LLM baseline.
- [ ] **WP10.4** Implement the bounded compiler benchmark runner.
- [ ] **WP10.5** Implement citation-accuracy scoring.
- [ ] **WP10.6** Implement successful-activation scoring.
- [ ] **WP10.7** Add cost, latency, and human-intervention reporting.
- [ ] **WP10.8** Publish the initial evaluation report.
- [ ] **WP10.9** Add adversarial document and prompt-injection tests.
- [ ] **WP10.10** Add end-to-end restart, retry, stale-state, partial-failure, and resume tests.
- [ ] **WP10.11** Harden document upload, preview, browser, and secret handling.
- [ ] **WP10.12** Harden production containers and Docker Compose.
- [ ] **WP10.13** Document deployment, migrations, backups, observability, scaling, and recovery.
- [ ] **WP10.14** Create the deterministic portfolio demo dataset and walkthrough.
- [ ] **WP10.15** Complete project setup, architecture, security, evaluation, limitation, and roadmap documentation.

## WP11 — Supplemental Amendment Processing

- [ ] **WP11.1** Define amendment lifecycle, authority, scope, and safety invariants.
- [ ] **WP11.2** Add amendment relationships and activation lineage with RLS.
- [ ] **WP11.3** Implement amendment precedence resolution.
- [ ] **WP11.4** Compute semantic differences between prior and amended COIR versions.
- [ ] **WP11.5** Build the cross-domain amendment impact graph.
- [ ] **WP11.6** Compile the minimal authorized delta plan.
- [ ] **WP11.7** Execute and reconcile amendment deltas.
- [ ] **WP11.8** Build amendment comparison and evidence views.
- [ ] **WP11.9** Add amendment benchmark cases and scoring.
