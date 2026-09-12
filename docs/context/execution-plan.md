# Enact Execution Plan

Related: `docs/context/prd.md`, `docs/context/implementation-plan.md`

## WP0 — Reference Scenario and Specifications

- [x] **WP0.1** Define the reference SaaS organization and activation scenario across all four domains.
- [ ] **WP0.2** Create the synthetic reference contract PDF bundle.
- [ ] **WP0.3** Author the source-to-target ground-truth fixtures for the reference activation.
- [ ] **WP0.4** Define COIR version 1 in `docs/context/coir-specification.md`.
- [ ] **WP0.5** Define organization configuration version 1 in `docs/context/organization-configuration-specification.md`.
- [ ] **WP0.6** Define activation and graph lifecycles in `docs/context/workflow-specification.md`.
- [ ] **WP0.7** Define target adapter contracts in `docs/context/adapter-specification.md`.
- [ ] **WP0.8** Define benchmark fixtures and scoring in `docs/context/evaluation-specification.md`.
- [ ] **WP0.9** Evaluate Docling and the minimum viable alternative against representative PDFs.
- [ ] **WP0.10** Record the document-processing architecture decision.

## WP1 — Repository, Runtime, and Tenant Security

- [ ] **WP1.1** Scaffold the React/Vite and FastAPI applications with shared developer commands.
- [ ] **WP1.2** Add typed backend configuration, liveness, and readiness endpoints.
- [ ] **WP1.3** Add the React application shell, routing, and global error handling.
- [ ] **WP1.4** Add the local Docker Compose environment for web, API, PostgreSQL, and object storage.
- [ ] **WP1.5** Bootstrap `enact_owner`, `enact_migrate`, and `enact_app` with scoped privileges.
- [ ] **WP1.6** Establish Alembic ownership, grants, and downgrade conventions.
- [ ] **WP1.7** Implement transaction-scoped PostgreSQL tenant context.
- [ ] **WP1.8** Add reusable RLS migration helpers and tenant-isolation tests.
- [ ] **WP1.9** Add the S3-compatible object-storage interface and MinIO implementation.
- [ ] **WP1.10** Establish reproducible OpenAPI TypeScript client generation.
- [ ] **WP1.11** Add structured logging and request correlation.
- [ ] **WP1.12** Add continuous integration for frontend, backend, migrations, RLS, and generated contracts.

## WP2 — Organizations, Identity, Configuration, and Activations

- [ ] **WP2.1** Add organization, user, membership, and customer persistence with RLS.
- [ ] **WP2.2** Implement the replaceable authentication boundary.
- [ ] **WP2.3** Implement membership and application-role authorization.
- [ ] **WP2.4** Implement versioned organization-configuration schemas.
- [ ] **WP2.5** Persist immutable organization-configuration versions with RLS.
- [ ] **WP2.6** Seed the reference organization, users, customer, catalogs, and policies.
- [ ] **WP2.7** Expose organization-configuration read APIs.
- [ ] **WP2.8** Add activation and activation-run persistence with lifecycle enforcement and RLS.
- [ ] **WP2.9** Expose activation create, list, and detail APIs.
- [ ] **WP2.10** Build the activation queue and activation creation flow.
- [ ] **WP2.11** Add append-only audit-event persistence with RLS.
- [ ] **WP2.12** Audit configuration and activation lifecycle changes.

## WP3 — Contract Intake and Document Evidence

- [ ] **WP3.1** Add document bundle, document, and document-version persistence with RLS.
- [ ] **WP3.2** Implement secure, idempotent multi-PDF upload to object storage.
- [ ] **WP3.3** Expose document upload, list, metadata, and processing-status APIs.
- [ ] **WP3.4** Build the contract bundle upload interface.
- [ ] **WP3.5** Implement the processor-neutral parsed-document contract.
- [ ] **WP3.6** Integrate the selected document processor behind the processor interface.
- [ ] **WP3.7** Persist parsed pages, items, tables, and source spans with RLS.
- [ ] **WP3.8** Add extraction-quality assessment and selective OCR fallback.
- [ ] **WP3.9** Add typed handling for encrypted, malformed, oversized, and failed PDFs.
- [ ] **WP3.10** Evaluate whether document processing requires a worker and record the decision.
- [ ] **WP3.11** If required, add a document-processing worker and its minimum queue infrastructure.
- [ ] **WP3.12** Add document classification and relationship persistence with RLS.
- [ ] **WP3.13** Expose document classification and relationship correction APIs.
- [ ] **WP3.14** Build the PDF and source-span evidence viewer.
- [ ] **WP3.15** Build the document relationship and precedence editor.

## WP4 — COIR and Deterministic Validation

- [ ] **WP4.1** Implement shared COIR primitives, provenance, and schema versioning.
- [ ] **WP4.2** Implement the billing COIR schema.
- [ ] **WP4.3** Implement the entitlements COIR schema.
- [ ] **WP4.4** Implement the support COIR schema.
- [ ] **WP4.5** Implement the onboarding COIR schema.
- [ ] **WP4.6** Persist immutable COIR versions with RLS.
- [ ] **WP4.7** Implement compiler diagnostic schemas and blocking semantics.
- [ ] **WP4.8** Implement common provenance and temporal validation.
- [ ] **WP4.9** Implement deterministic billing validation.
- [ ] **WP4.10** Implement deterministic entitlement validation.
- [ ] **WP4.11** Implement deterministic support validation.
- [ ] **WP4.12** Implement deterministic onboarding validation.
- [ ] **WP4.13** Implement cross-domain validation.
- [ ] **WP4.14** Load and validate the manually authored reference COIR.
- [ ] **WP4.15** Build the COIR and diagnostics inspector.

## WP5 — Source-Grounded Agentic Compilation

- [ ] **WP5.1** Implement the model-provider abstraction with deterministic fake and local implementations.
- [ ] **WP5.2** Add prompt, model, tool, and compilation-budget versioning.
- [ ] **WP5.3** Implement tenant-safe LangGraph checkpoint persistence.
- [ ] **WP5.4** Implement the typed compilation graph skeleton and termination rules.
- [ ] **WP5.5** Add activation-scoped document retrieval tools.
- [ ] **WP5.6** Add activation-scoped organization-context and target-state tools.
- [ ] **WP5.7** Compile document classifications and relationships into cited proposals.
- [ ] **WP5.8** Extract source-grounded candidate terms for all four domains.
- [ ] **WP5.9** Resolve definitions, cross-references, and document precedence.
- [ ] **WP5.10** Construct immutable candidate COIR versions.
- [ ] **WP5.11** Add the bounded deterministic validation and COIR-revision loop.
- [ ] **WP5.12** Add grouped clarification interrupts and durable resume.
- [ ] **WP5.13** Expose compilation start, resume, status, and event APIs.
- [ ] **WP5.14** Deliver compilation progress through SSE or status polling based on the approved decision.
- [ ] **WP5.15** Build candidate-term review and clarification flows.
- [ ] **WP5.16** Evaluate whether compilation requires background execution and record the decision.
- [ ] **WP5.17** If required, move only the justified compilation stages to a worker.

## WP6 — Cross-Domain Planning and Simulation

- [ ] **WP6.1** Implement the target-neutral action graph.
- [ ] **WP6.2** Implement the adapter protocol and reusable contract test suite.
- [ ] **WP6.3** Implement the billing simulator adapter.
- [ ] **WP6.4** Implement the entitlements simulator adapter.
- [ ] **WP6.5** Implement the support simulator adapter.
- [ ] **WP6.6** Implement the onboarding simulator adapter.
- [ ] **WP6.7** Compile validated COIR into a dependency-aware cross-domain plan.
- [ ] **WP6.8** Persist immutable plan versions and actions with RLS.
- [ ] **WP6.9** Implement whole-plan simulation and before-and-after state capture.
- [ ] **WP6.10** Add controlled validation, version-conflict, partial-failure, and drift scenarios.
- [ ] **WP6.11** Expose plan and simulation APIs.
- [ ] **WP6.12** Build the cross-domain plan and simulation workspace.

## WP7 — Policy Decisions and Safe Execution

- [ ] **WP7.1** Implement versioned approval-policy schemas.
- [ ] **WP7.2** Implement deterministic plan policy evaluation.
- [ ] **WP7.3** Group related clarification and approval cases.
- [ ] **WP7.4** Persist decision cases and immutable responses with RLS.
- [ ] **WP7.5** Expose decision review APIs with stale-plan protection.
- [ ] **WP7.6** Resume compilation and planning after recorded decisions.
- [ ] **WP7.7** Build grouped clarification and exception review.
- [ ] **WP7.8** Implement the execution authorization boundary.
- [ ] **WP7.9** Implement idempotent action execution with optimistic concurrency.
- [ ] **WP7.10** Implement dependency-aware execution and partial-failure state.
- [ ] **WP7.11** Implement execution retry, recovery, and supported compensation.
- [ ] **WP7.12** Persist and expose execution receipts with RLS.
- [ ] **WP7.13** Build execution status and recovery controls.

## WP8 — Reconciliation and Evidence

- [ ] **WP8.1** Implement intended-versus-actual reconciliation primitives.
- [ ] **WP8.2** Add reconciliation behavior to all four adapters.
- [ ] **WP8.3** Attribute reconciliation mismatches to their likely workflow stage.
- [ ] **WP8.4** Persist reconciliation runs and findings with RLS.
- [ ] **WP8.5** Enforce activation completion and accepted-deviation rules.
- [ ] **WP8.6** Expose reconciliation and deviation-acceptance APIs.
- [ ] **WP8.7** Build the reconciliation workspace.
- [ ] **WP8.8** Materialize the complete source-to-result evidence graph.
- [ ] **WP8.9** Expose evidence and timeline APIs.
- [ ] **WP8.10** Build bidirectional source-to-result navigation.
- [ ] **WP8.11** Complete the activation queue and lifecycle workspace.

## WP9 — Evaluation, Hardening, and Portfolio Delivery

- [ ] **WP9.1** Expand the synthetic benchmark suite.
- [ ] **WP9.2** Implement the fixed extraction-and-mapping baseline.
- [ ] **WP9.3** Implement the single-pass structured LLM baseline.
- [ ] **WP9.4** Implement the bounded compiler benchmark runner.
- [ ] **WP9.5** Implement citation-accuracy scoring.
- [ ] **WP9.6** Implement successful-activation scoring.
- [ ] **WP9.7** Add cost, latency, and human-intervention reporting.
- [ ] **WP9.8** Publish the initial evaluation report.
- [ ] **WP9.9** Add adversarial document and prompt-injection tests.
- [ ] **WP9.10** Add end-to-end restart, retry, stale-state, partial-failure, and resume tests.
- [ ] **WP9.11** Harden document upload, preview, browser, and secret handling.
- [ ] **WP9.12** Harden production containers and Docker Compose.
- [ ] **WP9.13** Document deployment, migrations, backups, observability, scaling, and recovery.
- [ ] **WP9.14** Create the deterministic portfolio demo dataset and walkthrough.
- [ ] **WP9.15** Complete project setup, architecture, security, evaluation, limitation, and roadmap documentation.

## WP10 — Supplemental Amendment Processing

- [ ] **WP10.1** Define amendment lifecycle, authority, scope, and safety invariants.
- [ ] **WP10.2** Add amendment relationships and activation lineage with RLS.
- [ ] **WP10.3** Implement amendment precedence resolution.
- [ ] **WP10.4** Compute semantic differences between prior and amended COIR versions.
- [ ] **WP10.5** Build the cross-domain amendment impact graph.
- [ ] **WP10.6** Compile the minimal authorized delta plan.
- [ ] **WP10.7** Execute and reconcile amendment deltas.
- [ ] **WP10.8** Build amendment comparison and evidence views.
- [ ] **WP10.9** Add amendment benchmark cases and scoring.
