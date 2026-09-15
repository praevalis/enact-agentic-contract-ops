# Enact: Agentic Contract Change Compiler

> Repository: `enact-agentic-contract-ops`
> Status: Revised product direction accepted

## Product thesis

Enact compiles signed B2B contracts and amendments into source-grounded operational diffs against the systems a company already runs. It discovers relevant capabilities and current customer state, asks humans only about material unresolved mappings or exceptions, and preserves an auditable path from signed language to reconciled state.

A signed contract is operational intent, but it cannot be executed safely without knowing what the organization's systems support. Enact must obtain that context from authoritative systems rather than requiring an administrator to recreate the organization inside Enact.

## Problem

After a B2B agreement is signed, deal desk and operations teams repeatedly translate negotiated language into billing, product access, support commitments, and onboarding work. Amendments are especially risky because teams must determine what changed, which systems are affected, and what must remain untouched.

The work is difficult because:

- Relevant terms are distributed across related documents.
- Specific negotiated language may override standard schedules.
- Equivalent business intent is expressed using different terminology.
- Target systems use organization-specific identifiers and constraints.
- Existing state may have changed since the agreement was interpreted.
- Manual implementation leaves weak evidence connecting a result to its source.

## Adoption constraint

Enact must not require a customer to manually reproduce its product catalogs, pricing, entitlement rules, support model, and onboarding process before receiving value.

Operational context is obtained in this order:

1. Discover reference data, capabilities, constraints, and customer state from connected systems.
2. Import existing machine-readable artifacts when a system cannot expose the information directly.
3. Reuse previously reviewed mappings within their authorized scope.
4. Apply narrowly administered organization policies.
5. Ask a targeted human question for the remaining material gap.

Missing information remains explicit. It is not converted into an inferred target capability.

## Compilation model

```text
Contract bundle, prior agreement, or amendment
    -> source-grounded Contract Intent IR
    -> versioned operational capability and customer-state snapshots
    -> reviewed semantic mappings
    -> deterministic validation and affected-domain analysis
    -> minimal dependency-aware operational diff
    -> simulation and authorization
    -> idempotent execution
    -> reconciliation and evidence
```

Contract intent, external-system facts, organization policy, mappings, and human decisions remain separate versioned artifacts.

## MVP scope

Billing and entitlements receive complete adapters because they demonstrate a strong invariant: the quantity and scope enforced as product access must agree with the quantity and scope used for charging.

Support and onboarding remain required contract domains, but initially compile into typed contractual obligations. They do not require complete simulated support and project-management products.

The baseline activation establishes accepted intent, mappings, and target state. The signature demonstration is a subsequent amendment that produces a minimal operational delta while preserving unaffected state.

## Agent boundary

The agent may interpret documents, investigate references, construct cited intent candidates, search target snapshots, propose mappings, identify ambiguity, and ask focused questions.

Deterministic services remain authoritative for schemas, arithmetic, dates, compatibility, policies, mapping validation, affected-domain analysis, action ordering, authorization, execution, concurrency, reconciliation, and audit records.

The model cannot mutate target systems, access arbitrary databases, invent capabilities, authorize exceptions, or promote a case-specific mapping to broader scope.

## Primary user

The primary user is the deal desk team responsible for handing signed commercial intent to operations. Organization administrators manage connections, explicit policies, and reusable mapping scope. Operations reviewers handle exceptional decisions. Auditors inspect provenance and results.

## Reference demonstration

The Acme Cloud and Redwood Systems baseline contract exercises billing, entitlements, support obligations, onboarding obligations, document precedence, negotiated exceptions, and a material ambiguity concerning whether monthly data capacity is shared across production workspaces.

A subsequent signed amendment increases seats and included capacity on a mid-term effective date. Enact must identify the changed intent, discover current billing and entitlement state, calculate the prospective billing effect, preserve unchanged products and obligations, apply only the required delta, and reconcile the result.

## Definition of success

A reviewer can:

1. Upload the baseline agreement and observe relevant operational context discovered from independently seeded target systems.
2. Inspect source-cited Contract Intent IR and proposed target mappings.
3. Resolve one material ambiguity or missing mapping.
4. Simulate, authorize, apply, and reconcile billing, entitlement, and obligation state.
5. Upload the amendment and inspect its semantic and operational impact.
6. Verify that only affected state changes and stale state cannot be applied silently.
7. Trace each changed value through source evidence, snapshots, mappings, decisions, actions, receipts, and reconciliation.
8. Review evaluation results against simpler baselines.

## Constraints

- The project must run locally through Docker Compose without paid services.
- The application remains a React/Vite static client calling FastAPI directly.
- FastAPI and LangGraph Python form a modular monolith.
- PostgreSQL uses scoped migration and runtime roles plus row-level security.
- Uploaded documents live behind an S3-compatible interface with MinIO locally.
- Workers, additional services, and multiple agents are introduced only when measured requirements justify them.
- Live commercial integrations are not required; simulators must behave through credible adapter boundaries.
