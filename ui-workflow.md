# Meridian Retail Case Study — End-to-End UI Workflow

This document describes how a user interacts with the Meridian Retail support-draft tool as a UI application, from launch to final disposition of a case. It reflects the actual behavior of `app.py` (now powered by Claude Sonnet hosted on Databricks) and the rules in `policy.md` (P1–P4).

## Actors

* **Support Agent** — the primary UI user. Selects cases, triggers draft generation, and asks the customer for missing information.
* **Human Reviewer** — reviews, edits, and approves or rejects every draft before any reply leaves the system.
* **Customer** — not a UI user; interacts only with the agent (asks questions, supplies missing facts such as the delivery date).

## End-to-End Interaction Flow

```mermaid
flowchart TD
    A[Agent launches Meridian Support Draft UI] --> B{Databricks credentials configured?}
    B -- "No" --> C[Settings screen: workspace URL + token hidden input + model service default system.ai.gpt-oss-120b]
    C --> C2[Save project-local .env - token never displayed]
    C2 --> D
    B -- "Yes" --> D[Case Queue screen: C1 / C2 / C3 cards with issue status and missing-field badges]
    D --> E[Agent selects a case]
    E --> F[Case Detail screen: Supplied Facts panel + Supplied Policy panel P1-P4]
    F --> G[Agent clicks Generate Draft]
    G --> H[UI builds prompt: case facts + policy + strict JSON output rules]
    H --> I[App calls the Databricks-hosted model (default system.ai.gpt-oss-120b) via Unity Gateway with timeout 20s, no retries]
    I --> J{Response passes validation: exact JSON fields, allowed review status, policy IDs only}
    J -- "Error, timeout, or invalid output" --> K[UNAVAILABLE state: empty draft + manual fallback banner]
    J -- "Valid" --> L{review_status}
    L -- READY_FOR_HUMAN_REVIEW --> M[Draft Review screen: editable draft_reply + evidence_refs chips + review banner]
    L -- NEEDS_INFORMATION --> N[Missing-Information panel: e.g. delivery_date missing - P2, P4]
    L -- BLOCKED --> O[Policy Block panel: cannot confirm resolution of an open issue - P3, P4]
    N --> N2[Agent asks customer for the missing fact via existing channels]
    N2 --> N3{Customer supplied it?}
    N3 -- "Yes" --> N4[Agent updates case facts in UI] --> G
    N3 -- "No" --> N5[Case stays parked with NEEDS_INFORMATION badge]
    M --> P{Human Reviewer decision}
    P -- "Edit" --> M
    P -- "Regenerate" --> G
    P -- "Approve" --> Q[Approved draft released to agent - sending is a human action outside this tool]
    O --> O2[Reviewer explains policy outcome; case closed as unsupported]
    K --> K2[Agent writes the reply manually using supplied facts and policy]
    Q --> R[Audit entry: case, model, status, reviewer, timestamp]
```

## Screen-by-Screen Specification

| # | Screen | Purpose | Key UI Elements | Exit Criteria |
| --- | --- | --- | --- | --- |
| 1 | Settings / First Run | Configure Databricks connection | Workspace URL field, hidden token field, model service selector (default `system.ai.claude-sonnet-4-5`), Test Connection button | Valid connection or credentials saved to project `.env` |
| 2 | Case Queue | Choose which case to work | Cards for C1–C3 showing product, question preview, `issue_status` badge, missing-field badge (e.g. C2: delivery_date missing) | A case is selected |
| 3 | Case Detail | Review evidence before drafting | Read-only Supplied Facts form, Supplied Policy panel (P1–P4), buttons: Generate Draft, Offline Demo, Simulate Timeout (classroom modes) | Agent clicks Generate Draft |
| 4 | Generating (in-flight) | Show model call in progress | Spinner, "Calling Claude Sonnet on Databricks…", disabled inputs, Cancel | Model response or failure received |
| 5 | Draft Review | Human-in-the-loop review | Editable `draft_reply` text area, `evidence_refs` chips that highlight the cited policy lines, `missing_information` list, `review_status` badge, Approve / Edit / Regenerate buttons, permanent banner: "Drafts are for human review only — this tool never sends messages, approves refunds, or changes records" | Reviewer approves, edits, or regenerates |
| 6 | Missing Information | Handle NEEDS_INFORMATION | Highlighted missing fields, suggested customer-facing question, Update Case Facts form, Regenerate button | Fact supplied and case updated, or case parked |
| 7 | Policy Block | Handle BLOCKED | Explanation citing P3/P4, guidance on what the agent may tell the customer, Close as Unsupported button | Case dispositioned |
| 8 | Fallback | Handle UNAVAILABLE | Red banner with manual fallback message, link back to Supplied Facts and Policy for manual drafting | Agent drafts the reply manually |
| 9 | Audit Log | Trace every run | Table of runs: case ID, model service, review status, reviewer, timestamp, mode (live / offline / simulated timeout) | N/A — always available |

## Status Routing Rules

| `review_status` | Meaning (from the model + validation) | UI Treatment | Agent Next Step |
| --- | --- | --- | --- |
| `READY_FOR_HUMAN_REVIEW` | Draft is complete and policy-cited (e.g. C1: damage reported within two days → P1, P4) | Draft Review screen with editable draft | Reviewer approves or edits; agent then responds to the customer manually |
| `NEEDS_INFORMATION` | A required fact is missing (e.g. C2: `delivery_date` absent → P2, P4) | Missing-Information panel with suggested question | Ask the customer, update facts, regenerate |
| `BLOCKED` | Policy cannot support the request (e.g. C3: issue is open, so resolution cannot be confirmed → P3, P4) | Policy Block panel | Explain outcome to customer without promising anything |
| `UNAVAILABLE` | Model call failed, timed out, or output was invalid | Fallback banner, empty draft, manual fallback message | Draft the reply manually from facts and policy |

## Design Guardrails (must hold in every screen)

* The tool drafts only for human review. It never sends a message, approves a refund, or changes a case record (P4).
* An open issue is never described as resolved in any draft (P3).
* A missing delivery date is surfaced as missing, never worked around (P2).
* Damage referrals state that review is possible, not that a refund is approved (P1).
* Every model response is validated (exact JSON fields, allowed status, policy IDs drawn from the supplied policy) before display; structure never substitutes for human review of content.
* All failure paths — provider errors, timeouts, invalid output — converge on the same safe `UNAVAILABLE` state with a manual fallback; no tracebacks or stale drafts are ever shown.
* The access token is entered once via hidden input and stored only in a project-local `.env`; it is never displayed in the UI or logs.

## Notes for This Workspace

* The app now defaults to `system.ai.gpt-oss-120b` (GPT-OSS 120B hosted by Databricks, verified live in this workspace) through the workspace's Unity Gateway Anthropic-compatible API. Set `APP_DATABRICKS_MODEL` to a service such as `system.ai.claude-sonnet-4-5` when it is available in your region.
* If the configured model service is not available in the workspace (for example Claude models in regions that do not offer them), live runs safely fall back to `UNAVAILABLE` with the manual fallback message; Offline Demo and Simulated Timeout modes keep working for classroom use.
* The Ollama variant in `Meridian Retail Ollama Demo/` follows this same workflow with a local model; its UI flow is identical except the Settings screen collects an Ollama model name instead of Databricks credentials.
