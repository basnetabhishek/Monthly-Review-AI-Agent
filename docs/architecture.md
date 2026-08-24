# MVP Architecture

```mermaid
flowchart TB
    O[Global Superstore file] --> BO[bronze.raw_orders]
    BO --> SO[silver.orders_clean]
    SO --> MP[gold.monthly_performance]
    SO --> OS[gold.order_summary]
    SO --> POLICY[Documented synthetic-target policy]
    POLICY --> MT[gold.monthly_targets]
    MP --> V[Controlled reporting views]
    OS --> V
    MT --> V
    V --> WH[Databricks SQL Warehouse]
    WH --> API[Report orchestrator]
    API --> PAYLOAD[Typed KPI payload]
    PAYLOAD --> RULES[Deterministic materiality rules]
    RULES --> LLM[Structured narrative generation]
    LLM --> VALIDATE[Claim validator]
    PAYLOAD --> UI[Executive report UI]
    VALIDATE --> UI
    API --> HISTORY[Report history]
```

The first deployment target is a Databricks App. Outbound access to the selected LLM provider must be tested early. If Free Edition blocks the request, the frontend and orchestration API can be hosted externally while Databricks remains the data and SQL platform.
