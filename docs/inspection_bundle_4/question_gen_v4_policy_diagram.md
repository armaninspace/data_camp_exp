# Question Generation V4 — Mermaid Policy Diagram

```mermaid
flowchart TD
    A[V3 candidate artifacts] --> B[Validity gate]

    B -->|fail| HR[hard_reject]
    B -->|pass| C[Family tagging]

    C --> D[Canonicalization]
    D --> E[Serviceability decision]
    D --> F[Curation decision]

    E -->|alias phrasing of canonical intent| AO[alias_only]
    E -->|servable yes| S1[Eligible for cache]
    E -->|servable no| A1[analysis_only]

    F -->|high pedagogical value + balance fit| CC[curated_core]
    F -->|not curated| G[Bucket assignment]

    CC --> H[Build canonical cache entry]
    S1 --> G

    G -->|servable and not curated| CS[cache_servable]
    G -->|nonfatal but not serviceable| A2[analysis_only]

    AO --> I[Map alias to canonical item]
    CS --> H

    H --> J[Q/A cache]
    I --> J

    subgraph K [Retained fully]
        CC
        CS
        AO
        A1
        A2
    end

    subgraph L [Audit only]
        HR
    end
```

## Notes

- `curated_core` and `cache_servable` can create active cache entries.
- `alias_only` should usually route to a canonical cache item rather than become its own served record.
- `analysis_only` is quarantined for tuning and reviewer workflows.
- `hard_reject` stores minimal audit metadata only.
