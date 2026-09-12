# Enact Reference SaaS Activation Scenario

## Reference Organization

Acme Cloud provides an enterprise cloud operations platform. The product is intentionally generic: its purpose is to exercise billing, entitlements, support, and onboarding without tying Enact to one SaaS industry.

Acme Cloud sells:

- An annual enterprise platform subscription
- Named user seats
- Metered monthly data processing with included usage and overage charges
- An advanced analytics add-on
- Production and sandbox workspaces
- Standard and premium support
- Guided enterprise onboarding

Its standard commercial position includes a maximum discount without exception approval, standard product limits, defined support tiers, and reusable onboarding templates. Exact machine-readable catalogs and policies will be defined during WP0.5.

## Reference Customer and Deal

Redwood Systems is purchasing Acme Cloud for an initial one-year term from January 1 through December 31, 2027.

The signed contract bundle will contain:

- An order form containing negotiated commercial and product terms
- A master services agreement containing general legal and commercial terms
- A product schedule defining standard product behavior and usage measurement
- A support schedule defining standard premium-support commitments
- An onboarding statement of work defining implementation activities and responsibilities

## Billing Terms

- Enterprise platform subscription: USD 96,000 per year
- 300 named user seats: USD 240 per seat per year, totaling USD 72,000
- Advanced analytics add-on: USD 24,000 per year
- Included data processing: 20 TB per month
- Overage: USD 450 per TB, billed monthly in arrears
- Discount: 15% on the fixed annual subscription charges
- Fixed annual charges after discount: USD 163,200
- Fixed annual charges are invoiced on the contract effective date with Net 30 payment terms
- A USD 12,000 onboarding fee is invoiced when the kickoff meeting is completed

The fixed-charge total is derived deterministically:

```text
USD 96,000 platform
+ USD 72,000 seats
+ USD 24,000 analytics
= USD 192,000 gross annual fixed charges
- 15% discount
= USD 163,200 net annual fixed charges
```

## Entitlement Terms

- Enterprise platform edition
- 300 named user seats
- Advanced analytics enabled
- Two production workspaces
- One sandbox workspace
- SSO and SCIM provisioning enabled
- 20 TB of included data processing per month
- Entitlements become active on January 1, 2027
- Entitlements expire at the end of December 31, 2027 unless renewed or amended

## Support Terms

- Premium support tier
- 24-hour coverage, seven days per week for Priority 1 incidents
- Priority 1 initial response within 30 minutes
- Priority 2 initial response within two business hours
- Web and telephone support channels
- Escalation to a support duty manager for unresolved Priority 1 incidents
- Service-credit eligibility follows the support schedule

The order form's 30-minute Priority 1 response commitment is more specific than the one-hour target in the standard premium-support schedule.

## Onboarding Terms

- Provider schedules kickoff within five business days after the effective date
- Provider conducts an architecture and data-integration workshop
- Provider assists with SSO and SCIM configuration
- Customer supplies identity-provider access and names its administrators before the configuration session
- Provider configures initial production and sandbox workspaces
- Provider delivers administrator training
- Both parties complete a production-readiness review
- Target production launch is within 30 calendar days after kickoff
- The USD 12,000 onboarding fee becomes billable when kickoff is recorded as completed

The onboarding plan must represent provider responsibilities, customer prerequisites, dependencies, owners, and relative due dates rather than flattening everything into an unordered task list.

## Document Precedence Cases

The reference bundle must exercise term-specific precedence:

- The product schedule states that the enterprise edition normally includes 10 TB per month; the order form grants Redwood Systems 20 TB per month.
- The support schedule defines a one-hour Priority 1 initial response target; the order form grants a 30-minute target.
- The specific negotiated order-form terms override the corresponding standard schedule terms only for Redwood Systems, the stated quantities, and the contract term.
- Both selected and non-selected terms remain available in the evidence trail with the applied precedence reason.

## Approval Exceptions

Acme Cloud's reference policies will treat these negotiated terms as exceptions:

- The 15% fixed-charge discount exceeds the standard automatically permitted discount.
- The 30-minute Priority 1 response target is more demanding than the standard premium-support commitment.

The standard actions remain automatically authorized. The two non-standard commitments are presented as a concise deal-exception decision rather than requiring approval for every billing, entitlement, support, and onboarding action.

For the reference successful-activation path, the authorized reviewer approves the exception decision.

## Material Ambiguity

The order form describes the entitlement as "20 TB monthly data processing capacity" but does not state whether the allowance is pooled across the two production workspaces or applies separately to each workspace.

This ambiguity is material to both billing and entitlements:

- A pooled interpretation provides 20 TB total before overage charges.
- A per-workspace interpretation provides 40 TB total before overage charges.

Neither the contract bundle nor the reference organization configuration resolves the scope. Enact must stop the affected compilation path, show the competing interpretations and citations, and request clarification instead of selecting a value.

For the reference successful-activation path, the deal desk user clarifies that the 20 TB allowance is pooled across the two production workspaces.

## Cross-Domain Dependencies

The resulting activation plan must preserve at least these dependencies:

- The customer account exists before any domain-specific configuration is applied.
- The enterprise edition exists before the analytics add-on and workspace entitlements are enabled.
- The included-usage quantity used for entitlement enforcement matches the quantity used for billing overage calculation.
- The premium-support profile references the activated customer and contracted product term.
- SSO and SCIM configuration depends on the customer's identity-provider prerequisite.
- Production-readiness review depends on workspace configuration, identity setup, and administrator training.
- The onboarding fee is not billable until kickoff completion is recorded.

## Expected Activation Outcome

After clarification and exception approval, Enact should produce and reconcile:

### Billing

- One annual fixed-charge invoice for USD 163,200 on January 1, 2027
- Net 30 payment terms
- Monthly overage calculation above a pooled 20 TB allowance at USD 450 per TB
- A pending USD 12,000 onboarding charge triggered by kickoff completion

### Entitlements

- Enterprise platform access for the contract term
- 300 named seats
- Advanced analytics
- Two production workspaces and one sandbox workspace
- SSO and SCIM
- A pooled 20 TB monthly data-processing allowance

### Support

- Premium support for the contract term
- 24x7 Priority 1 coverage
- 30-minute Priority 1 and two-business-hour Priority 2 initial-response targets
- Web, telephone, and duty-manager escalation access

### Onboarding

- A kickoff milestone due within five business days of January 1, 2027
- Architecture and data-integration workshop
- Customer identity-provider prerequisite
- SSO and SCIM configuration
- Production and sandbox workspace setup
- Administrator training
- Production-readiness review
- Production launch target due within 30 calendar days after kickoff

## Required Demonstration Behavior

The scenario is successful when it causes Enact to:

- Extract material terms across all four domains with source citations
- Apply term-specific document precedence without discarding conflicting evidence
- Calculate billing amounts and dates deterministically
- Detect and stop on the pooled-versus-per-workspace ambiguity
- Resume after recording the clarification as explicit evidence
- Group the negotiated discount and support commitment into a concise exception decision
- Generate a dependency-aware plan across all four target systems
- Apply authorized actions idempotently
- Reconcile intended and actual state
- Trace every material final value to contract evidence, organization policy, or a recorded human decision
