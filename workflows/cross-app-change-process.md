# Cross-Application Change Process

Use this process when a change spans more than one application. Cross-app changes carry higher risk because they require coordination across codebases, teams, and deployment schedules.

## When This Applies

- A feature requires changes in two or more applications
- A shared interface, API contract, or data format is being modified
- A shared dependency is being updated
- A data migration affects multiple applications

## Process

### 1. Identify Impacted Applications

- List every application affected by the change.
- For each application, identify the specific components, endpoints, or data structures involved.
- Confirm with the relevant application overview (`applications/app-*-overview.md`).

### 2. Record Contracts and Interfaces

- Document the current state of any shared interface (API contract, event schema, database schema, etc.).
- Define the target state after the change.
- Note any versioning implications.

### 3. Define Sequencing

- Determine the order in which changes must be applied.
- Identify whether changes can be deployed independently or must be coordinated.
- Plan for backward compatibility during the transition period.

| Step | Application | Change | Dependencies | Notes |
|------|-------------|--------|-------------|-------|
| 1 | <!-- App --> | <!-- What changes --> | <!-- What must happen first --> | <!-- --> |
| 2 | <!-- App --> | <!-- What changes --> | <!-- What must happen first --> | <!-- --> |

### 4. Validate Integration Points

- Define how the integration will be tested during and after the change.
- Identify contract tests, integration tests, or manual verification steps.
- Plan for testing in a staging environment before production.

### 5. Document Rollout and Rollback

- **Rollout plan:** How will the change be deployed? In what order? Over what timeframe?
- **Rollback plan:** If something goes wrong, how will each application revert? Is rollback independent or coordinated?
- **Communication:** Who needs to be informed before, during, and after the rollout?

## After the Change

- Update the affected application overviews in `applications/`.
- Update `system-landscape.md` if integrations or data flows changed.
- Create an ADR if the change involved a significant architectural decision.
- Write a handoff note summarizing the change and any follow-up needed.
