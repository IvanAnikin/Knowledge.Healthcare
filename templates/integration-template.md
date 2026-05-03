# Integration: <!-- Source Application --> to <!-- Target Application -->

> Use this template to document an integration point between two applications or between an application and an external service.

## Summary

<!-- What data or functionality flows between these systems? Why? 1-2 sentences. -->

## Applications Involved

| Role | Application | Owner |
|------|-------------|-------|
| Producer / Source | <!-- App name --> | <!-- Team or person --> |
| Consumer / Target | <!-- App name --> | <!-- Team or person --> |

## Interface Details

- **Type:** <!-- REST API / Event / Database / File Transfer / etc. -->
- **Protocol:** <!-- HTTPS / gRPC / AMQP / etc. -->
- **Endpoint or topic:** <!-- URL, queue name, table, etc. -->
- **Authentication:** <!-- How the consumer authenticates -->
- **Versioning:** <!-- How the interface is versioned -->

## Data Contract

<!-- What data is exchanged? Define the schema or reference an external spec. -->

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| <!-- field --> | <!-- type --> | <!-- yes/no --> | <!-- description --> |

## Behavior

- **Trigger:** <!-- What causes data to flow? -->
- **Frequency:** <!-- Real-time / Batch / On-demand -->
- **Idempotency:** <!-- Is the operation idempotent? -->
- **Error handling:** <!-- What happens on failure? Retries? Dead letter? -->

## Testing

- <!-- How is this integration tested? -->
- <!-- Contract tests, integration tests, or manual verification? -->

## Failure Modes

| Failure | Impact | Detection | Recovery |
|---------|--------|-----------|----------|
| <!-- What can go wrong --> | <!-- What happens --> | <!-- How we know --> | <!-- How we fix it --> |

## Dependencies

<!-- What must be in place for this integration to work? -->

- <!-- Dependency -->

## Open Questions

- <!-- Question -->
