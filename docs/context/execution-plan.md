# Enact Execution Plan

Related: `docs/context/prd.md`, `docs/context/implementation-plan.md`

Each unchecked task is intended to be an independent, meaningful commit. After the database foundation, every work package is a complete vertical product slice.

## WP0 — Repository Scaffold

- [x] **WP0.1** Establish the root uv workspace, Python 3.13 toolchain, repository layout, and shared pre-commit hooks.
- [x] **WP0.2** Scaffold the FastAPI server package with versioned API composition, Alembic, and test boundaries.
- [x] **WP0.3** Scaffold the React/Vite application with TypeScript, app-local pnpm, linting, formatting, and test tooling.
- [x] **WP0.4** Add the manually dispatched frontend and backend CI baseline.
- [x] **WP0.5** Add the local Docker Compose topology and optimized production containers.
- [x] **WP0.6** Verify that the production images build and the Docker Compose topology starts successfully.

## WP1 — Product Pivot and Reference Inputs

- [x] **WP1.1** Define the Acme Cloud and Redwood Systems baseline scenario.
- [x] **WP1.2** Generate and verify the baseline reference contract bundle.
- [x] **WP1.3** Adopt operational discovery and contract change compilation as the revised product direction.
- [x] **WP1.4** Revise the project brief and PRD around the accepted pivot.
- [x] **WP1.5** Replace the implementation and execution plans with slice-based delivery.
- [x] **WP1.6** Define the signed Redwood amendment scenario and update the reference narrative.
- [x] **WP1.7** Generate and verify the signed Redwood amendment PDF.

## WP2 — Database and Runtime Foundation

- [x] **WP2.1** Design the relational schema, aggregate ownership, tenant boundaries, and migration sequence needed by the planned slices.
- [x] **WP2.2** Add typed settings, environment loading, and startup validation.
- [x] **WP2.3** Add async SQLAlchemy engine, session, transaction, and dependency-injection boundaries using asyncpg.
- [x] **WP2.4** Bootstrap `enact_owner`, `enact_migrate`, and `enact_app` with scoped privileges.
- [x] **WP2.5** Establish Alembic ownership, grant, default-privilege, and downgrade conventions.
- [x] **WP2.6** Implement transaction-local tenant context and fail-closed database access.
- [x] **WP2.7** Add reusable RLS migration helpers and tenant-isolation tests.
- [x] **WP2.8** Add liveness and dependency-aware readiness endpoints.
- [x] **WP2.9** Implement the S3-compatible object-storage boundary and MinIO adapter.
- [ ] **WP2.10** Establish reproducible OpenAPI TypeScript client generation.
- [ ] **WP2.11** Add structured logging and request correlation.
- [ ] **WP2.12** Extend CI for migrations, PostgreSQL privileges, RLS, generated contracts, and container builds.

## WP3 — Case and Document Intake Slice

- [ ] **WP3.1** Add organization, membership, customer, case, case-lineage, and audit persistence with RLS.
- [ ] **WP3.2** Implement the replaceable authentication boundary and role authorization.
- [ ] **WP3.3** Expose case create, list, detail, and lifecycle APIs.
- [ ] **WP3.4** Build the case queue and case creation experience using the generated client.
- [ ] **WP3.5** Add document bundle, document, version, and relationship persistence with RLS.
- [ ] **WP3.6** Implement secure, idempotent multi-PDF upload to object storage.
- [ ] **WP3.7** Implement the processor-neutral parsed-document and source-span model.
- [ ] **WP3.8** Evaluate Docling and the minimum viable alternative against the reference PDFs and record the decision.
- [ ] **WP3.9** Integrate the selected processor with extraction-quality and failure diagnostics.
- [ ] **WP3.10** Expose document, classification, relationship, processing-status, and source APIs.
- [ ] **WP3.11** Build document upload, lineage, classification correction, PDF preview, and source-span inspection.
- [ ] **WP3.12** Add unit, integration, tenant-isolation, API, UI, and end-to-end tests for the complete intake slice.
- [ ] **WP3.13** Evaluate whether document processing requires a worker and add one only if measurements justify it.

## WP4 — Operational Discovery and Snapshot Slice

- [ ] **WP4.1** Implement connector-instance persistence, credential references, and connector authorization with RLS.
- [ ] **WP4.2** Implement the asynchronous operational-adapter protocol and reusable contract tests.
- [ ] **WP4.3** Build independently versioned billing and entitlement simulator stores.
- [ ] **WP4.4** Implement billing and entitlement reference-data discovery.
- [ ] **WP4.5** Implement capability and constraint discovery.
- [ ] **WP4.6** Implement customer-state reads through adapters.
- [ ] **WP4.7** Persist immutable reference-data, capability, and customer-state snapshots with hashes and provenance.
- [ ] **WP4.8** Build the PostgreSQL-backed Operational Capability Graph projection.
- [ ] **WP4.9** Add snapshot freshness, comparison, and stale-context diagnostics.
- [ ] **WP4.10** Expose connection, discovery, snapshot, capability, and customer-state APIs.
- [ ] **WP4.11** Build connection status and discovered operational-context views.
- [ ] **WP4.12** Add complete slice tests for discovery isolation, reproducibility, partial results, constraints, and stale snapshots.

## WP5 — Contract Intent Compilation Slice

- [ ] **WP5.1** Implement common Contract Intent IR primitives, provenance, versioning, and unresolved alternatives.
- [ ] **WP5.2** Implement billing and entitlement intent models.
- [ ] **WP5.3** Implement the generic contractual-obligation model for support and onboarding.
- [ ] **WP5.4** Persist immutable intent and obligation versions with RLS.
- [ ] **WP5.5** Implement document-authority, effective-period, and deterministic intent validation.
- [ ] **WP5.6** Implement billing arithmetic, entitlement compatibility, and billing-entitlement consistency validation.
- [ ] **WP5.7** Implement compiler diagnostics and affected-path blocking semantics.
- [ ] **WP5.8** Add the model-provider abstraction with deterministic fake and local implementations.
- [ ] **WP5.9** Implement the bounded LangGraph interpretation workflow, checkpoints, budgets, and termination rules.
- [ ] **WP5.10** Add source retrieval, document relationship, target-snapshot, and deterministic validation tools.
- [ ] **WP5.11** Construct source-cited intent candidates and pause on the reference ambiguity rather than inventing scope.
- [ ] **WP5.12** Expose compilation, resume, intent, obligation, diagnostic, and event APIs.
- [ ] **WP5.13** Build the source-to-intent and diagnostics workspace.
- [ ] **WP5.14** Add complete slice tests for structured output, provenance, precedence, validation, graph paths, and resume.
- [ ] **WP5.15** Evaluate progress delivery and background execution from measured compilation behavior.

## WP6 — Operational Mapping and Clarification Slice

- [ ] **WP6.1** Implement operational mapping, version, decision, scope, and invalidation models with RLS.
- [ ] **WP6.2** Search target snapshots and reviewed mappings for candidate target objects.
- [ ] **WP6.3** Propose mappings without embedding target identifiers into Contract Intent IR.
- [ ] **WP6.4** Implement deterministic mapping and target-capability validation.
- [ ] **WP6.5** Separate contract interpretation, target mapping, unsupported capability, and policy diagnostics.
- [ ] **WP6.6** Implement targeted mapping questions with evidence, candidates, consequences, and reuse scope.
- [ ] **WP6.7** Persist reviewed decisions and require authorization before broad mapping promotion.
- [ ] **WP6.8** Resume compilation after mapping or interpretation decisions.
- [ ] **WP6.9** Expose mapping registry, candidate, decision, promotion, and invalidation APIs.
- [ ] **WP6.10** Build mapping inspection, clarification, and reusable-knowledge views.
- [ ] **WP6.11** Demonstrate that a reviewed mapping is reused safely by a later case.
- [ ] **WP6.12** Add complete slice tests for mapping accuracy, scope, reuse, promotion, invalidation, and tenant isolation.

## WP7 — Baseline Planning, Execution, and Reconciliation Slice

- [ ] **WP7.1** Implement affected-domain analysis and the target-neutral action graph.
- [ ] **WP7.2** Compile mapped billing and entitlement intent into dependency-aware actions.
- [ ] **WP7.3** Compile support and onboarding intent into the obligation ledger.
- [ ] **WP7.4** Persist immutable plan versions, actions, preconditions, expected versions, and unaffected-state assertions with RLS.
- [ ] **WP7.5** Implement whole-plan simulation and before-and-after state capture.
- [ ] **WP7.6** Implement explicit organization policy versions and deterministic exception evaluation.
- [ ] **WP7.7** Group policy exceptions without requiring approval for every standard action.
- [ ] **WP7.8** Implement plan authorization with stale-plan protection.
- [ ] **WP7.9** Implement idempotent adapter execution, optimistic concurrency, retries, and partial-failure state.
- [ ] **WP7.10** Persist execution receipts and append-only evidence.
- [ ] **WP7.11** Implement intended-versus-actual reconciliation and accepted deviations.
- [ ] **WP7.12** Expose plan, simulation, decision, execution, reconciliation, and evidence APIs.
- [ ] **WP7.13** Build the affected-state plan, authorization, execution, reconciliation, and timeline workspace.
- [ ] **WP7.14** Add complete slice tests for invariants, policy decisions, idempotency, concurrency, failures, reconciliation, and evidence.
- [ ] **WP7.15** Establish the accepted Redwood baseline state required by amendment compilation.

## WP8 — Amendment Change Compilation Slice

- [ ] **WP8.1** Implement amendment authority, supersession, and prior-case lineage.
- [ ] **WP8.2** Construct amended intent while preserving accepted prior intent and mappings.
- [ ] **WP8.3** Compute versioned semantic change sets with effective periods.
- [ ] **WP8.4** Build the affected operational impact graph.
- [ ] **WP8.5** Revalidate only affected mappings and domains while proving unaffected-state preservation.
- [ ] **WP8.6** Calculate prospective billing changes and matching entitlement deltas deterministically.
- [ ] **WP8.7** Compile the minimal dependency-aware amendment plan.
- [ ] **WP8.8** Detect stale target state before delta authorization and execution.
- [ ] **WP8.9** Execute and reconcile the amendment delta without duplicate effects.
- [ ] **WP8.10** Expose amendment lineage, semantic diff, impact, and delta-plan APIs.
- [ ] **WP8.11** Build prior-versus-amended intent, impact, and operational-diff views.
- [ ] **WP8.12** Materialize amendment-to-result evidence and unaffected-state assertions.
- [ ] **WP8.13** Add complete slice tests for impact accuracy, delta minimality, stale state, idempotency, and reconciliation.

## WP9 — Evaluation, Hardening, and Portfolio Delivery

- [ ] **WP9.1** Author sequential reference ground truth for baseline, mapping reuse, and amendment cases.
- [ ] **WP9.2** Expand the benchmark with terminology variation, conflicts, unsupported capabilities, and adversarial documents.
- [ ] **WP9.3** Implement fixed extraction and mapping and single-pass structured-model baselines.
- [ ] **WP9.4** Implement the bounded compiler benchmark runner.
- [ ] **WP9.5** Score citations, intent, discovery coverage, mappings, human questions, affected domains, impact, delta minimality, and reconciliation.
- [ ] **WP9.6** Report cost, latency, failure recovery, mapping reuse, and incorrect broad promotion.
- [ ] **WP9.7** Add prompt-injection, upload, preview, connector, secret, and browser hardening.
- [ ] **WP9.8** Add end-to-end restart, retry, stale-state, partial-failure, and resume scenarios.
- [ ] **WP9.9** Harden production containers and Docker Compose.
- [ ] **WP9.10** Document deployment, migrations, backups, observability, scaling, recovery, and limitations.
- [ ] **WP9.11** Create the deterministic portfolio dataset, benchmark report, and amendment-centered walkthrough.
