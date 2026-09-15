# Enact Product Requirements Document

**Product:** Enact - Agentic Contract Change Compiler
**Status:** Revised MVP requirements
**Primary user:** Deal desk team
## 1. Product summary

Enact compiles signed B2B contracts and amendments into source-grounded operational diffs against connected systems. It discovers relevant operational capabilities and customer state, maps contract intent to target objects, asks humans only about material unresolved mappings and exceptions, and preserves evidence through execution and reconciliation.

The product does not require an organization to recreate its operational catalogs inside Enact. Connected systems and imported artifacts remain the sources of operational truth.

## 2. Problem statement

Deal desk and operations teams must translate negotiated language into coordinated operational changes. This translation is repeated for every agreement and amendment, even though much of the target context already exists in billing, entitlement, support, and workflow systems.

Failures include incorrect charges, mismatched access, missed obligations, inconsistent cross-system changes, amendment overreach, stale-state writes, and poor traceability.

## 3. Goals

The MVP shall:

1. Interpret related contract documents with precise source provenance.
2. Represent contract intent independently from target-system mappings.
3. Discover relevant reference data, capabilities, constraints, and customer state through adapters.
4. Create versioned operational snapshots for reproducible compilation.
5. Propose and validate mappings between contract language and target objects.
6. Ask targeted questions only for material unresolved interpretation, mapping, or policy gaps.
7. Apply reviewed mappings only within their authorized scope.
8. Produce a minimal plan for affected domains.
9. Simulate, authorize, execute, and reconcile supported changes safely.
10. Treat support and onboarding terms as typed obligations.
11. Compile a signed amendment into a semantic and operational delta.
12. Preserve unaffected intent and target state.
13. Expose an evidence chain from source clause to reconciled result.

## 4. Non-goals

The revised MVP will not:

- Recreate an organization's complete operational model inside Enact.
- Provide a comprehensive organization-configuration wizard.
- Replace CRM, CPQ, billing, entitlement, support, or project-management systems.
- Implement full commercial integrations with multiple vendors.
- Provide complete support or onboarding target adapters.
- Infer approval authority or materiality policies automatically.
- Promote reviewed mappings to broad scope without authorization.
- Support every contract type, product model, or pricing structure.
- Provide legal advice or complete legal interpretation.
- Allow an LLM to mutate operational state directly.
- Require every standard action to receive manual approval.

## 5. Users and responsibilities

### Deal desk user

Creates a case, uploads signed documents, reviews intent and mappings, answers targeted questions, and routes exceptional decisions.

### Organization administrator

Connects operational systems, manages narrowly scoped policies, reviews reusable mappings, and controls mapping promotion.

### Operations reviewer

Reviews domain-specific incompatibilities or policy exceptions and authorizes changes within assigned authority.

### Auditor

Inspects source evidence, snapshots, mappings, decisions, execution receipts, and reconciliation results.

## 6. Core concepts

### Case

A durable unit of work for either an initial activation or a contract change. Cases retain lifecycle, lineage, inputs, snapshots, compilation attempts, decisions, and outcomes.

### Contract Intent IR

A typed, versioned representation of what the signed agreement appears to require. It includes commercial terms, access, quotas, obligations, effective periods, authority, ambiguity, and provenance. It does not contain target identifiers merely because a model proposed a mapping.

### Operational snapshots

Immutable versions of externally sourced information:

- Reference data: products, prices, features, meters, and identifiers
- Capabilities: supported actions, constraints, and preconditions
- Customer state: current subscriptions, entitlements, and obligations

### Operational Capability Graph

A versioned projection connecting relevant snapshot entities, constraints, operations, and customer state. Every fact identifies its source connector or imported artifact.

### Operational mapping

A reviewable relationship between contract intent and one or more target objects. Mapping scope may be activation-only, customer-specific, contract-template-specific, product-family-specific, or organization-wide.

### Contractual obligation

A typed support or onboarding commitment containing subject, responsible party, beneficiary, action or outcome, trigger, due condition, dependencies, evidence, remedy, effective period, and source provenance.

### Semantic change set

The difference between accepted prior Contract Intent IR and amended intent, including changed effective periods and explicitly unaffected terms.

### Operational diff

The minimal set of target actions needed to move current state to the mapped contractual state.

## 7. Core workflow

```text
Connect or select operational systems
    -> Create an activation or amendment case
    -> Upload signed documents
    -> Capture relevant operational snapshots
    -> Interpret source-grounded contract intent
    -> Propose and validate target mappings
    -> Resolve material gaps
    -> Inspect affected-domain operational diff
    -> Simulate and authorize exceptions
    -> Apply idempotently
    -> Reconcile actual state
    -> Inspect evidence and reusable mappings
```

An amendment case additionally loads accepted prior intent and mappings, computes a semantic change set, identifies affected operational entities, and preserves unaffected state.

## 8. Functional requirements

### 8.1 Case and document intake

The system shall accept multi-PDF bundles, preserve originals and hashes, classify documents, represent relationships and amendments, retain source locations, and expose case status and history.

### 8.2 Operational discovery

Adapters shall expose independently versioned reference data, capabilities, constraints, and customer state. Compilation shall use immutable snapshots rather than uncontrolled live reads. Partial discovery shall produce explicit diagnostics.

### 8.3 Interpretation and authority

The system shall identify operationally material language, resolve definitions and cross-references where supported, preserve competing terms, apply scoped precedence, and construct cited Contract Intent IR candidates. Unsupported material assumptions shall stop the affected path.

### 8.4 Mapping

The system shall search discovered target objects and previously reviewed mappings, propose candidate mappings, validate compatibility, and explain consequences. A human decision shall record both its answer and reuse scope. Broad promotion requires explicit authority.

### 8.5 Domain behavior

Billing and entitlements receive full validation, planning, execution, and reconciliation. Deterministic services own pricing arithmetic, periods, compatibility, quotas, and the invariant that billable allowance and enforced allowance use the same quantity and scope.

Support and onboarding terms compile into contractual obligations. The MVP may persist them in an internal obligation ledger rather than simulate complete downstream products.

Only affected domains are required for a successful compilation.

### 8.6 Diagnostics and decisions

Diagnostics shall distinguish errors, warnings, policy exceptions, unsupported capabilities, contract ambiguities, and unresolved mappings. Interpretation clarification, mapping confirmation, and policy authorization are separate decision types.

### 8.7 Planning and simulation

Plans shall identify affected and unaffected state, dependencies, preconditions, expected versions, and before-and-after values. The amendment plan shall contain only actions caused by the semantic change set.

### 8.8 Authorization and execution

Only deterministic application services may invoke typed adapter mutations. Execution requires a current plan and authorization version, stable idempotency keys, and optimistic concurrency. Standard policy-compliant actions do not require individual approval.

### 8.9 Reconciliation

The system shall read actual target state after execution and compare it with intended state. A successful write response is insufficient. Mismatches remain visible and attributable to interpretation, mapping, planning, execution, or downstream state.

### 8.10 Evidence

Every material result shall be traceable through:

```text
Source span
  -> Contract Intent IR field
  -> target snapshot
  -> operational mapping or decision
  -> diagnostic
  -> plan action
  -> authorization
  -> execution receipt
  -> reconciliation result
```

## 9. Amendment requirements

The signature demonstration shall:

- Relate the amendment to the governing agreement.
- Preserve accepted prior intent and mappings.
- Identify changed terms and effective periods.
- Compute a semantic change set and impact graph.
- Revalidate only affected mappings and domains where safe.
- Calculate prospective billing changes without rewriting prior invoices.
- Produce matching billing and entitlement changes.
- Exclude unchanged products and obligations from the execution plan.
- Detect stale target state before applying the delta.
- Apply and reconcile without duplicate effects.

## 10. User interface

The primary interface is an operational workspace, not chat. It shall include:

- Case queue and lifecycle status
- Document bundle, lineage, and authority
- Source clause beside interpreted intent
- Discovered capabilities and provenance
- Mapping review and reuse scope
- Clarification and exception decisions
- Prior-versus-amended intent
- Affected and unaffected operational state
- Minimal execution plan
- Simulation, execution, reconciliation, and evidence timeline

Administration focuses on connections, explicit policies, reusable mappings, and discovery gaps.

## 11. Lifecycle

```text
Received -> Discovering Context -> Interpreting -> Mapping -> Validating
         -> Needs Clarification or Decision -> Ready -> Simulating
         -> Awaiting Authorization -> Applying -> Reconciling -> Active

Active -> Amendment Received -> Discovering Current State
       -> Recompiling Affected Intent -> Computing Impact
       -> Applying Delta -> Reconciling -> Active
```

The workflow shall survive restarts and preserve durable artifacts at each material boundary.

## 12. Evaluation

Primary measures are:

- Citation accuracy
- Contract-intent correctness
- Operational-context discovery coverage
- Mapping accuracy and incorrect broad reuse
- Human questions per case and reduction across repeated cases
- Billing and entitlement consistency
- Correct affected-domain identification
- Amendment impact precision and recall
- Delta-plan minimality and preservation of unaffected state
- Stale-state detection
- Final reconciliation accuracy
- Cost and latency

Compare fixed extraction and mapping, a single-pass structured model, and the bounded agentic compiler. The benchmark shall include sequential cases for the same organization so mapping reuse can be measured.

## 13. Technical and operating constraints

- Development and demonstration require no paid service.
- The product runs locally through Docker Compose and remains deployment-ready.
- Real contract PDFs are accepted; the system does not distinguish them from generated reference documents.
- Contract and connector content are untrusted input.
- Tenant-owned records use authorization checks and PostgreSQL row-level security.
- Models cannot access secrets, arbitrary SQL, unrestricted networks, or mutation operations.
- Worker and multi-agent adoption require measured justification.

## 14. MVP acceptance

The MVP is successful when a reviewer can establish the Redwood baseline from independently seeded billing and entitlement systems, resolve a material ambiguity or mapping, apply and reconcile the supported state, then upload the signed amendment and observe a correct minimal delta with complete evidence and no change to unaffected state.
