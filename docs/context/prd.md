# Enact Product Requirements Document

**Product:** Enact - Agentic Contract-to-Operations Compiler  
**Repository:** `enact-agentic-contract-ops`  
**Document status:** Initial product requirements draft  
**Primary user:** Deal desk team  
**Product type:** Portfolio demonstration with deployment-ready architecture

## 1. Product summary

Enact converts a signed B2B contract bundle into a validated, source-cited operational activation plan. It helps the deal desk pass a contract into exact operational configuration across four equally important domains:

- Billing
- Entitlements
- Support
- Onboarding

Enact is not an autonomous system that allows a language model to edit business records directly. The agent interprets contract language, investigates relevant context, identifies uncertainty, and proposes structured changes. Deterministic services validate, authorize, execute, and reconcile those changes.

The initial product focuses on activating a new customer. Amendment processing and differential recompilation are supplemental phases after the initial activation workflow is reliable.

## 2. Problem statement

After a B2B deal is signed, deal desk and operations teams must repeatedly reinterpret contract language and manually configure multiple systems. Important terms may be distributed across an order form, MSA, SOW, pricing schedule, support terms, and amendments.

This creates operational risk:

- Incorrect prices, discounts, billing schedules, or credits
- Missing or excessive product access
- Support commitments that do not match the contracted SLA
- Onboarding obligations that are not tracked or assigned
- Conflicting or superseded terms being implemented incorrectly
- Changes being applied in one system but missed in another
- Poor traceability from a downstream value back to the signed agreement

Enact addresses the translation gap between negotiated commercial intent and operational execution.

## 3. Product vision

The long-term vision is for a signed contract to function as executable operational intent. Enact should compile contract bundles into a durable, explainable, and reproducible operational state that can be applied, verified, amended, and audited over time.

## 4. Goals

### MVP goals

The MVP must allow a deal desk user to:

1. Create an activation for an organization and customer.
2. Upload a bundle of PDF contract documents.
3. Inspect document classification, versions, relationships, and precedence.
4. Review source-cited operational terms extracted from the bundle.
5. See the proposed canonical operational representation.
6. Detect ambiguities, conflicts, unsupported requirements, and policy exceptions.
7. Resolve targeted questions or approve grouped exceptional decisions.
8. Preview coordinated changes across billing, entitlements, support, and onboarding.
9. Apply the approved plan to simulated operational systems.
10. Reconcile intended state with resulting actual state.
11. Inspect an evidence trail connecting source terms to interpretations, decisions, actions, and results.

### Portfolio goals

The project should demonstrate:

- Agent planning and bounded tool use
- Structured model outputs
- Source-grounded document interpretation
- A canonical intermediate representation
- Deterministic validation around probabilistic reasoning
- Policy-based human-in-the-loop control
- Durable workflow behavior
- Idempotent execution and failure handling
- Reconciliation and auditability
- Evaluation against simpler alternatives

## 5. Non-goals

The MVP will not:

- Replace contract authoring, negotiation, signature, or storage systems
- Provide legal advice or determine the legal meaning of a contract
- Allow an LLM to directly mutate operational records
- Support every possible product, billing model, or contract structure
- Require live production integrations
- Fully automate amendments, renewals, or long-term drift remediation
- Require users to manually approve every generated change
- Treat confidence scores as objective measures of legal certainty

## 6. Primary users and roles

### Deal desk user

Owns the activation handoff after signature. The deal desk user uploads documents, reviews the compilation result, answers targeted clarification questions, and approves or routes exceptional decisions.

### Organization administrator

Configures the organization’s operational vocabulary and policies, including products, billing rules, entitlement limits, support plans, onboarding templates, document precedence rules, and approval policies.

### Operations reviewer

May review domain-specific changes or exceptions in billing, entitlements, support, or onboarding. The exact organizational role can remain configurable for the prototype.

### Auditor or observer

Inspects source evidence, decisions, execution receipts, reconciliation results, and the activation timeline.

The MVP may use a small number of application roles, but the workflow must make ownership and accountability visible.

## 7. Product concepts

### Contract bundle

A set of related PDF documents for a customer activation. It may contain an order form, MSA, SOW, pricing schedule, support terms, amendments, or other applicable documents.

### Organization configuration

The organization-specific context needed to interpret and validate contracts. It includes:

- Product and plan catalog
- Standard prices, discounts, billing rules, and billing calendars
- Entitlement limits and compatibility rules
- Support tiers, coverage, severity definitions, and SLA policies
- Onboarding templates, tasks, milestones, and ownership rules
- Document types and precedence policies
- Approval policies and escalation rules

The product should ship with a reference SaaS organization configuration for development and demonstration. The architecture must allow an organization administrator to manage or import organization-specific configuration rather than relying on hardcoded assumptions.

### Contract Operational Intermediate Representation (COIR)

The canonical operational representation between contract interpretation and target-system execution. It is independent of the source document wording and downstream system APIs.

The COIR must preserve the distinction between:

- Contract facts
- Agent interpretations
- Organization policy facts
- Human decisions
- Explicit assumptions
- Unresolved ambiguities

Each interpreted operational value must have provenance and must be traceable to one or more source locations or explicitly identified external context.

### Compilation

The controlled process that transforms a contract bundle and organization configuration into an operational change plan.

### Activation plan

An ordered, target-specific set of proposed changes, dependencies, policy diagnostics, approval requirements, and expected results.

## 8. Core user workflow

```text
Create activation
    ↓
Upload PDF contract bundle
    ↓
Classify and relate documents
    ↓
Interpret terms with citations
    ↓
Construct COIR
    ↓
Validate against organization configuration
    ↓
Resolve ambiguity or grouped exceptions
    ↓
Generate cross-domain activation plan
    ↓
Simulate changes
    ↓
Apply approved changes
    ↓
Reconcile intended and actual state
    ↓
Review evidence and activation timeline
```

The workflow must be durable. It must survive process restarts, wait for human decisions, resume safely, and preserve the history of each compilation and execution attempt.

## 9. Functional requirements

### 9.1 Activation intake

The system shall:

- Allow a deal desk user to create an activation for a customer and organization.
- Accept multiple PDF files as one contract bundle.
- Preserve file names, hashes, upload timestamps, and versions.
- Extract document text and retain page or source-location references.
- Allow the user to identify or correct document classifications when needed.
- Show the current activation state and processing history.

### 9.2 Document lineage and precedence

The system shall:

- Identify likely document types and relationships.
- Represent amendments and supersession relationships explicitly.
- Preserve the original documents and extracted source locations.
- Explain why one term was selected over another.
- Surface unresolved conflicts instead of silently selecting a value.

The default precedence strategy should be:

1. An explicit amendment or supersession clause wins for the specific term and effective period it changes.
2. A specific term overrides a general term when the scope is the same—for example, an order-form price may override a standard MSA price.
3. A later document wins only when its authority and scope are applicable; “latest document wins” is not sufficient by itself.
4. An unresolved conflict becomes a diagnostic requiring clarification or an authorized decision.

Precedence must be configurable by organization. The system must retain both the selected and non-selected interpretations, with their evidence and resolution reason.

### 9.3 Source-grounded interpretation

The system shall:

- Identify contract language with operational consequences.
- Resolve defined terms and cross-references where possible.
- Extract candidate terms for all four MVP domains.
- Attach page, section, clause, or equivalent source citations.
- Record interpretation notes and supporting context.
- Distinguish explicit terms from inferred terms.
- Stop or request clarification when an operationally material assumption is not supported by contract evidence or organization configuration.

The agent may propose interpretations and alternatives, but it must not present unsupported assumptions as contract facts.

### 9.4 Operational domains

Each domain has equal MVP importance and must have its own operational model, validation rules, plan changes, and simulated target adapter.

#### Billing

The system should support terms such as:

- Plan and quantity
- Price and billing frequency
- Discount amount or period
- Credits and billing triggers
- Effective dates
- Usage or overage rules

Arithmetic, date calculations, prorations, and other deterministic billing logic must be handled by deterministic services.

#### Entitlements

The system should support terms such as:

- Product edition
- Seat or usage quantity
- Feature access
- Quotas and limits
- Environments or deployment scope
- Effective and expiration dates

Compatibility and maximum-limit checks must be deterministic and based on organization configuration.

#### Support

The system should support terms such as:

- Support tier
- Coverage hours and holidays
- Severity definitions
- Initial response targets
- Resolution or workaround targets when specified
- Channels and escalation paths
- Named support obligations
- Exclusions, remedies, or service credits

The system must distinguish materially different commitments such as coverage, response, and resolution. It must not treat them as interchangeable.

#### Onboarding

The system should support terms such as:

- Workshops and implementation activities
- Deliverables and milestones
- Due dates or relative time windows
- Dependencies and prerequisites
- Customer and provider responsibilities
- Internal owners

The system should convert supported obligations into trackable tasks or milestones in the simulated onboarding system.

### 9.5 Validation and diagnostics

The system shall validate the proposed COIR against:

- COIR schema requirements
- Product and entitlement compatibility
- Billing and pricing policies
- Support policy constraints
- Onboarding task and ownership rules
- Date consistency and effective periods
- Required organization configuration
- Approval policies

Diagnostics should be compiler-like and categorized as:

- **Error:** Processing cannot safely continue.
- **Warning:** Processing may continue, but the issue should be visible.
- **Exception:** Processing can continue after an authorized decision.
- **Information:** Relevant context with no blocking impact.

Every material diagnostic should identify its affected domain, source evidence, operational impact, and recommended next step.

### 9.6 Uncertainty and clarification

The product must balance automation with caution.

- If a conclusion is directly supported by contract language or organization configuration, processing may continue.
- If the agent makes a low-impact, policy-supported inference, it must label the inference and preserve its basis.
- If an unsupported assumption would materially affect billing, access, support, or onboarding, processing must stop for that issue.
- The system should ask targeted questions that present the relevant evidence and, where possible, candidate interpretations.
- A user response must become an explicit decision recorded in the activation evidence.

### 9.7 Policy-based approvals

Approval is an exception-control mechanism, not a manual confirmation step for every generated change.

Organization administrators shall configure policies that determine when an activation requires a decision. Policies may use:

- Domain
- Change type
- Threshold or deviation from standard terms
- Contract value or customer tier
- Non-standard product, entitlement, support, or onboarding commitment
- Risk or impact classification
- Presence of unresolved ambiguity

At runtime:

- Standard, policy-compliant changes should proceed automatically.
- Exceptional changes should be grouped into a small number of meaningful decisions.
- Materially unsafe or unsupported changes should block processing.
- Users should be able to approve, reject, edit, or request clarification for a grouped exception.

The user should see the complete activation plan but should not be required to approve every standard billing, entitlement, support, or onboarding action individually.

### 9.8 Planning and simulation

The system shall:

- Generate a coordinated plan across all four domains.
- Show proposed before-and-after state for each affected target.
- Show dependencies and execution order.
- Identify which changes are automatic, exceptional, blocked, or informational.
- Provide a dry-run result before application.
- Simulate success, validation failure, partial failure, retry, and reconciliation mismatch.
- Explain the expected operational effect of each change.

### 9.9 Execution

The system shall:

- Apply only authorized and validated changes.
- Use bounded, typed adapter operations.
- Make operations idempotent.
- Enforce optimistic concurrency or equivalent protection against stale state.
- Record action requests, responses, timestamps, and execution receipts.
- Support safe retry behavior.
- Make partial failures visible and recoverable.

The MVP may use simulated billing, entitlement, support, and onboarding systems. Adapter boundaries should be designed so real integrations can replace the simulators later.

### 9.10 Reconciliation

After application, the system shall:

- Read actual state from each target adapter.
- Compare it with the intended state derived from the approved plan.
- Identify mismatches by domain and change.
- Explain whether a mismatch likely originated in interpretation, planning, execution, or downstream state.
- Mark activation as reconciled only when required state matches or an explicit deviation is accepted.

### 9.11 Evidence and auditability

For each material operational value, the system should be able to show:

```text
Source clause
    → Extracted term
    → Interpretation or decision
    → COIR value
    → Validation result
    → Approval, if required
    → Target action
    → Execution receipt
    → Reconciliation result
```

The system shall preserve an immutable activation timeline and version the relevant source documents, organization configuration, policies, agent/model configuration, tools, decisions, and outputs.

## 10. User interface requirements

The primary product experience should be an operational workspace rather than a chat interface.

The MVP should include:

- Activation queue and status view
- Contract bundle and document relationship view
- Source clause beside interpreted term
- COIR or operational terms inspector
- Diagnostics panel
- Grouped exception and clarification review
- Cross-domain before-and-after diff
- Dependency-aware execution plan
- Simulation and application status
- Reconciliation view
- Activation timeline and evidence detail

A chat panel may support explanations or focused corrections, but it must not be the primary workflow.

## 11. Lifecycle and state model

The initial activation lifecycle is:

```text
Received
  → Interpreting
  → Validating
  → Needs Clarification or Decision
  → Ready
  → Simulating
  → Awaiting Approval, when required
  → Applying
  → Reconciling
  → Active
```

An activation may move to:

- **Blocked** when safe processing cannot continue.
- **Failed** when execution or reconciliation fails and recovery is not yet complete.
- **Cancelled** when an authorized user stops the case.

The design must support future states for amendment recompilation and drift investigation without requiring a complete lifecycle redesign.

## 12. Evaluation requirements

The benchmark should contain synthetic PDF contract bundles with known ground truth, including:

- Standard terms
- Non-standard billing and entitlement terms
- Support SLA variations
- Onboarding obligations and dependencies
- Document conflicts
- Unsupported or ambiguous language
- Amendments for the later phase

The primary evaluation measures are:

### Citation accuracy

Whether each material operational value is correctly supported by the relevant source clause, source location, or explicit organization configuration.

### Successful activation rate

Whether Enact produces and safely applies the correct cross-domain operational state, with required decisions handled appropriately and the final state reconciled.

Additional useful measures include:

- Ambiguity and conflict detection
- False unsupported assumptions
- Validity of generated plans
- Number of unnecessary human decisions
- Recovery from injected target failures
- Amendment delta correctness
- Cost and latency per activation

The project should compare at least:

1. A fixed extraction-and-mapping pipeline.
2. A single-pass LLM workflow.
3. The bounded agentic compiler with deterministic validation and replanning.

## 13. Technical and operating constraints

- The project must be developable without paid services.
- It must run locally through Docker Compose.
- It should be deployable with environment-based configuration.
- The architecture should support local or zero-cost model options for the portfolio demonstration.
- Real integrations should not be required for the MVP, but target adapters must be replaceable.
- The system must not depend on undocumented assumptions about a customer’s organization.
- Security, access control, and sensitive document handling should be represented in the architecture even if the demo uses synthetic data.

## 14. Initial acceptance criteria

The MVP is successful when a reviewer can upload a contract bundle and observe Enact:

1. Classify and relate the documents.
2. Extract material terms across billing, entitlements, support, and onboarding.
3. Display source citations for those terms.
4. Construct a coherent operational representation.
5. Detect at least one ambiguity, conflict, or policy exception.
6. Ask a targeted clarification question or request a grouped exception decision.
7. Generate a valid cross-domain activation plan.
8. Apply the plan safely to simulated target systems.
9. Reconcile intended and actual state.
10. Show an evidence chain from contract clause to final operational result.

Amendment processing is not required for initial MVP acceptance, but the data model and lifecycle should leave a clear path for the later amendment phase.

## 15. Open decisions for the next design documents

The PRD establishes product behavior. The following should be specified separately before implementation:

- Exact COIR schema and versioning strategy
- Organization configuration schema and admin experience
- Supported PDF extraction and OCR approach
- Agent tools, permissions, budgets, and replanning triggers
- Workflow persistence model
- Simulated target-system schemas and adapter contracts
- Detailed approval policy language
- Evaluation fixture format and target thresholds
- Deployment topology and observability design
