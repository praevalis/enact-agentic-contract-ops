# Enact: Agentic Contract-to-Operations Compiler

> Repository: `enact-agentic-contract-ops`
>
> Status: Concept selected; application and architecture planning not yet completed

## 1. Purpose of this document

This document captures the product idea, architectural thesis, scope boundaries, and design constraints for Enact. It is intended to give enough context to help plan the application without prematurely committing the project to a specific implementation or technology stack.

The next planning phase should turn this brief into:

1. A specification.
2. A domain model and system architecture.
3. Agent, workflow, and deterministic service boundaries.
4. A staged implementation roadmap.
5. An evaluation and demonstration plan.

## 2. Project identity

**Project name:** Enact: Agentic Contract-to-Operations Compiler  
**Repository:** `enact-agentic-contract-ops`

**One-line description:**

> An agentic system that compiles negotiated B2B contracts into validated operational configurations across billing, entitlements, support, and customer onboarding.

**Short thesis:**

> A signed contract should be executable operational intent, not a document that humans must repeatedly reinterpret and manually implement across disconnected systems.

## 3. Problem

When a B2B company closes a non-standard deal, its terms must be translated into operational reality. Information spread across an order form, master services agreement, statement of work, pricing schedule, amendments, and negotiation notes may affect:

- CRM fields and account metadata
- Product editions, features, quotas, and entitlements
- Billing schedules, prices, discounts, credits, and usage rules
- Service-level commitments and support priority
- Onboarding tasks and implementation milestones
- Renewal, termination, and notification dates
- Approval requirements and internal ownership

This translation is usually performed through manual handoffs among sales, deal desk, legal, finance, implementation, support, and engineering. The receiving teams must interpret prose, reconcile conflicting documents, understand product-specific constraints, and configure several systems correctly.

The resulting failures are not merely document-management problems. They include:

- Incorrect invoices or discount periods
- Missing or excessive product access
- Unfulfilled onboarding commitments
- Support plans that do not match contractual SLAs
- Revenue leakage
- Delayed customer activation
- Configurations that cannot be traced back to signed terms
- Amendments implemented in one system but missed in others

Traditional contract lifecycle management products primarily help create, negotiate, sign, store, search, and monitor contracts. Enact begins after commercial terms have been negotiated and focuses on compiling those terms into coordinated operational changes.

## 4. Product concept

Enact treats a contract bundle as source material for a controlled compilation process.

```text
Contract bundle
    ↓
Source-grounded interpretation
    ↓
Contract Operational Intermediate Representation
    ↓
Semantic and policy validation
    ↓
Target-specific execution plan
    ↓
Dry run and human approval
    ↓
Configuration across operational systems
    ↓
Reconciliation, evidence, and drift monitoring
```

The central artifact is a canonical **Contract Operational Intermediate Representation (COIR)**. It represents the operational meaning of the agreement independently of both the original legal wording and any particular downstream application.

The COIR may contain:

- Parties, accounts, products, and environments
- Commercial terms and pricing periods
- Entitlements, limits, and feature flags
- Billing triggers and schedules
- Service levels and support coverage
- Deliverables, dependencies, and milestones
- Effective dates, renewals, and termination rules
- Preconditions and conditional obligations
- Owners and approval requirements
- Source citations and confidence for every interpreted term
- Unresolved ambiguities and conflicts

Target adapters compile this representation into changes for simulated or real operational systems.

## 5. Why an agent is justified

Enact must not use an LLM for tasks that schemas, rules, parsers, or transactional software can perform more reliably.

Agentic reasoning is justified at the boundary between negotiated natural language and company-specific operational semantics. Each contract can express equivalent intentions differently, contain bespoke exceptions, depend on definitions elsewhere, or conflict with standard product and billing models. The correct next step may depend on evidence collected from several documents and systems.

The agent may be responsible for:

- Planning how to investigate a contract bundle
- Identifying terms with operational consequences
- Resolving cross-references across agreements, schedules, and amendments
- Mapping non-standard language to the canonical operational model
- Recognizing conflicting, incomplete, or infeasible requirements
- Retrieving product catalog, policy, pricing, and account context
- Proposing alternative implementations when a literal mapping is impossible
- Determining when human clarification or approval is necessary
- Revising the compilation plan after validation or dry-run failures
- Producing source-grounded explanations for proposed changes

Deterministic components must remain authoritative for:

- Schema validation
- Dates, arithmetic, prices, taxes, and prorations
- Product compatibility and entitlement constraints
- Approval thresholds and organizational policies
- Dependency ordering
- Change-set generation and diffing
- Idempotency and transactional execution
- Access control
- Reconciliation and drift detection
- Audit records

The architecture should therefore demonstrate an agent operating inside a governed software system, not an LLM directly editing business records.

## 6. Primary users

The initial product should be framed for a reference B2B SaaS company with moderately complex enterprise agreements.

Likely users include:

- Deal desk or revenue operations personnel initiating activation
- Implementation managers reviewing onboarding commitments
- Finance or billing operators approving commercial configuration
- Product operations teams reviewing entitlement mappings
- Legal operations personnel resolving contract interpretations
- System administrators managing target adapters and policies
- Auditors examining the relationship between terms and actions

The MVP does not need to model every role separately, but its workflows should make multi-party review and accountability visible.

## 7. Representative scenario

A customer signs an order form and an accompanying amendment containing these terms:

- Enterprise plan for 750 seats
- 12-month term beginning on a specified activation date
- First three months billed at a negotiated discount
- SSO and audit-log retention enabled
- A custom API quota above the standard plan limit
- Premium support with a one-hour response commitment
- Two onboarding workshops due within 30 days
- Renewal notice required 60 days before the term ends

Enact should:

1. Ingest and relate the contract documents.
2. Identify the governing and superseded terms.
3. Produce source-cited operational terms.
4. Map those terms into the COIR.
5. Validate them against the product catalog, pricing rules, and company policies.
6. Detect that the requested API quota requires an exception approval.
7. Generate a coordinated plan for CRM, billing, entitlements, support, and onboarding.
8. Simulate the changes and display their effects.
9. Route only the exceptional decision for human approval.
10. Apply approved changes through idempotent adapters.
11. Reconcile actual system state with the compiled contract state.
12. Retain an evidence chain connecting each configuration value to its source clause and execution receipt.

If an amendment later changes the seat count, discount period, or service commitment, Enact should compile a differential change plan rather than reimplementing the entire agreement.

## 8. Proposed compilation model

The compiler metaphor should be reflected in the architecture rather than used only as branding.

| Compiler concept | Enact equivalent |
|---|---|
| Source program | Contract bundle and amendments |
| Parsing | Document structure and clause interpretation |
| Symbols and references | Defined terms, parties, products, dates, and cross-references |
| Intermediate representation | COIR |
| Semantic analysis | Product, policy, pricing, and feasibility validation |
| Diagnostics | Ambiguities, conflicts, missing information, and unsupported terms |
| Optimization | Selecting a lower-risk or simpler valid implementation |
| Target backends | CRM, billing, entitlement, support, and onboarding adapters |
| Build plan | Ordered operational change set |
| Execution | Approved application of changes |
| Verification | Reconciliation against intended state |

Compilation should be restartable, inspectable, and reproducible. The same source documents, contextual data, policy versions, and agent version should be replayable to explain why a plan was produced.

## 9. Core product capabilities

### Contract intake and document lineage

- Upload a bundle containing an order form, MSA, SOW, schedules, and amendments.
- Classify documents and establish precedence relationships.
- Preserve versions, hashes, and source locations.
- Associate contracts with a customer and deal.

### Source-grounded term interpretation

- Extract candidate operational terms with precise source citations.
- Link definitions and cross-references.
- Record confidence and interpretation notes.
- Surface conflicts rather than silently resolving them.

### Canonical operational representation

- Normalize terms into typed, versioned COIR objects.
- Distinguish facts, interpretations, decisions, and assumptions.
- Support conditions, effective periods, dependencies, and amendments.
- Allow human corrections without losing the original proposal.

### Validation and diagnostics

- Validate the COIR against schemas and company policies.
- Check product compatibility, date consistency, pricing constraints, and required approvals.
- Return compiler-like errors and warnings tied to source terms.
- Permit the agent to repair a proposal or request a decision.

### Planning and simulation

- Generate target-specific changes and dependencies.
- Present before-and-after state for every affected system.
- Simulate success, failure, partial application, and rollback implications.
- Estimate the blast radius of amendments.

### Approval and execution

- Route only policy-defined exceptions or high-impact actions for approval.
- Execute changes through bounded, typed tools.
- Enforce idempotency and optimistic concurrency.
- Support retries, compensating actions, and partial-failure recovery.

### Reconciliation and drift

- Compare contract-derived intended state with downstream actual state.
- Explain mismatches and identify their likely origin.
- Reapply, accept, or escalate deviations.
- Detect later manual changes that violate the compiled agreement.

### Evidence and auditability

- Connect every operational value to a source clause, interpretation, approval, action, and result.
- Provide an immutable activation timeline.
- Allow a reviewer to answer: “Why does this customer have this price, feature, or SLA?”

## 10. Durable lifecycle

A contract activation is a persistent case, not a single request-response interaction.

Suggested conceptual states:

```text
Received → Interpreting → Validating → Needs Decision → Ready
        → Simulating → Awaiting Approval → Applying → Reconciling → Active

Active → Amendment Received → Recompiling → Applying Delta → Active
Active → Drift Detected → Investigating → Correcting or Accepting Drift → Active
```

The workflow must survive process restarts, wait for human decisions, resume safely, and preserve the state and evidence of each attempt.

## 11. User interface concept

The UI should make the compilation and operational lifecycle visible.

Potential views:

- Contract activation queue
- Contract bundle and document precedence
- Source clause beside interpreted operational term
- COIR inspector
- Compiler diagnostics with errors, warnings, and required decisions
- Cross-system before-and-after diff
- Dependency-aware execution plan
- Approval inbox
- Execution and reconciliation timeline
- Intended-versus-actual state comparison
- Amendment impact view
- Evidence graph for a selected price, entitlement, SLA, or task

A chat panel may be offered for explanations or targeted corrections, but it should not be the primary product experience.

## 12. Evaluation strategy

The project should empirically test whether the agent improves contract activation rather than assuming that it does.

Create a benchmark suite of synthetic contract bundles with known ground truth. Include standard cases, negotiated exceptions, contradictions, amendments, and infeasible terms.

Measure:

- Accuracy of operational term extraction
- Accuracy of COIR construction
- Source-citation correctness
- Conflict and ambiguity detection recall
- False assumptions or unsupported interpretations
- Validity of generated change plans
- Successful activation rate
- Downstream reconciliation accuracy
- Human decisions requested per case
- Unnecessary or invalid tool calls
- Recovery from injected target-system failures
- Correctness of amendment deltas
- Cost and latency per activation

Compare at least:

1. A fixed extraction-and-mapping pipeline.
2. A single-pass LLM workflow.
3. The bounded agentic compiler with deterministic validation and replanning.

The agentic design is justified only if it improves success on non-standard and failure-injected cases without producing unacceptable errors, cost, or review burden.

## 13. Portfolio value to demonstrate

Enact should visibly demonstrate:

- Agent planning and tool use
- Structured LLM outputs
- Durable asynchronous workflows
- Document intelligence grounded in citations
- Domain modeling and intermediate representations
- Deterministic validation around probabilistic reasoning
- Dependency graphs and change-impact analysis
- Human-in-the-loop approvals
- Idempotent integrations and failure recovery
- Reconciliation and drift detection
- Auditability and provenance
- Evaluation of agentic versus conventional approaches
- Backend, frontend, infrastructure, and architectural judgment

The portfolio story should emphasize that the LLM is not trusted as the execution engine. It interprets ambiguous commercial intent and proposes a structured compilation; deterministic services validate and enact it.

## 14. Important design principles

1. **No uncited operational claims.** Every interpreted term must point to its contractual source or be explicitly marked as an external policy, decision, or assumption.
2. **No direct LLM mutations.** The model proposes typed plans; governed services authorize and execute them.
3. **Ambiguity is a valid output.** The system must prefer a targeted question over an invented answer.
4. **Compilation is reproducible.** Inputs, policies, prompts, models, tools, decisions, and outputs are versioned.
5. **Execution is idempotent.** Retrying a workflow must not duplicate subscriptions, tasks, or entitlements.
6. **Amendments are deltas.** A changed agreement should produce an explainable impact graph and minimal change set.
7. **Actual state is verified.** A successful API response is not sufficient; downstream state must be reconciled.
8. **Agents handle uncertainty, not arithmetic.** Rules and conventional services own deterministic work.
9. **Complexity must earn its place.** Multi-agent coordination, distributed services, and specialized infrastructure require a demonstrated need.
10. **The demo must show operation, not conversation.** The user should see cases progressing, decisions being requested, changes being applied, and discrepancies being resolved.

## 15. Open decisions for the planning phase

Resolve the following before implementation:

### Product scope

- Which contract and product vocabulary gives the smallest credible MVP?
- Which three downstream systems best communicate the value?
- What is the minimum amendment scenario needed to demonstrate differential compilation?
- Which user roles and approvals must be represented?

### Domain and compiler design

- What is the exact COIR schema?
- How are document precedence and supersession represented?
- How are conditional, recurring, and time-bound terms modeled?
- Which diagnostics are errors, warnings, or approval requirements?
- How are interpretation confidence and provenance represented without pretending confidence scores are objective truth?

### Agent design

- Is one orchestrating agent sufficient for the MVP?
- What tools can it call, and what permissions does each tool have?
- What is the plan/action/result state model?
- What budgets constrain model calls, steps, retries, and elapsed time?
- How is replanning triggered after validation, simulation, or execution failure?
- What information may the agent see at each stage?

### Workflow and execution

- Which workflow engine or persisted state model is appropriate?
- Where are approvals inserted?
- How are partial failures, retries, and compensations handled?
- What constitutes a completed activation?
- How are concurrent amendments or manual downstream edits handled?

### Evaluation

- How will ground-truth contract bundles be authored?
- Which baselines are fair and implementable?
- Which failure conditions should be injected?
- What thresholds define a credible result?

### Implementation

- Which stack best fits fast iteration and the developer's existing strengths?
- Should target systems be separate services or modular adapters inside one deployment?
- Which local model is adequate for the initial benchmark?
- What observability is required for both workflows and agent traces?

## 16. Requested next planning sequence

When beginning implementation planning should proceed in this order:

1. Challenge the product assumptions and identify any remaining ambiguity in the problem definition.
2. Define one complete reference scenario and its ground truth.
3. Specify the COIR and domain model before selecting frameworks.
4. Separate agent decisions from deterministic rules and services.
5. Design the compilation, approval, execution, and reconciliation lifecycle.
6. Produce a logical architecture and data-flow model.
7. Select an implementation stack based on the required capabilities and cost constraints.
8. Divide the MVP into vertical milestones, each ending in a demonstrable workflow.
9. Define evaluation fixtures and baselines alongside development milestones.
10. Only then create the repository structure and implementation plan.

Ask focused questions when a decision materially changes the product or architecture. It should not add agents, services, infrastructure, or integrations merely to increase apparent complexity.

## 17. Initial definition of success

The project is successful when a reviewer can provide a contract bundle (real / synthetic) and observe Enact:

1. Derive a source-cited operational representation.
2. Detect at least one ambiguity, conflict, or policy exception.
3. Obtain a targeted human decision.
4. Produce a valid cross-system change plan.
5. Apply that plan safely to simulated operational systems.
6. Reconcile the resulting state.
7. Process an amendment as an explainable delta.
8. Demonstrate through benchmark results where the agentic approach performs better—or fails to perform better—than simpler alternatives.

The final portfolio presentation should make the operational problem, the compiler architecture, the agent's bounded role, and the engineering safeguards understandable within a few minutes.
