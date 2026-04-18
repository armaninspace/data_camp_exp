# Interrogation V4.1

## Core diagnosis

The current V4.1 output proves that auditability is improved, but policy
protection for beginner entry questions is still not being enforced as a hard
delivery guarantee.

The system now tells us when beginner questions are:

- generated and hidden
- never generated
- present only as hidden correct variants

But it still allows foundational entry questions to remain non-visible.

## Answers

### Why are questions tagged `required_entry=true` still being assigned `delivery_class: analysis_only` instead of being promoted to `curated_visible` or at least `cache_servable`?

Because `required_entry` is currently only an audit tag. It is persisted on
the candidate record, but it does not override the selector. The selector
still classifies from score thresholds and visible-bucket logic inherited from
V4, so required entry items can still be routed to `analysis_only`.

### Why is `low_distinctiveness` allowed to demote canonical beginner definition questions like “What is exponential smoothing?” and “What is white noise?” when those are exactly the entry questions the policy is supposed to protect?

Because `low_distinctiveness` is still treated as a general-purpose pruning
signal rather than a signal that must be bypassed for protected entry
questions. That is structurally wrong for anchor definitions. Canonical
beginner definitions should be exempt from distinctiveness demotion when they
are the designated first-contact question for an anchor.

### Why does the selector emit `only_hidden_correct_entry_exists` warnings without automatically promoting one visible canonical entry question for that anchor?

Because V4.1 currently implements audit, not auto-remediation. The coverage
audit runs after classification and visible selection. It reports the failure,
but no promotion rule is attached to that warning yet.

### Why are `definition_generation_failed` warnings for foundational anchors not treated as generation failures that block the inspection bundle?

Because the current implementation treats them as quality warnings, not fatal
pipeline errors. That is defensible for inspection, since the point is to show
the failure. But if the goal is “no beginner-anchor gaps allowed,” then these
should become blocking failures or at least fail a strict mode.

### How exactly is the system deciding which anchors deserve mandatory “What is X?” questions, and why are some foundational concepts still missing those candidates altogether?

Right now anchors are inferred heuristically from V3 topics using topic type
and confidence. That identifies many core concepts, but generation is still
driven by the existing V3 candidate templates. So an anchor can be detected
correctly while no `definition` candidate is ever produced for it. That is why
`seasonality`, `trend`, and `benchmark methods` can be flagged as anchors while
still lacking `What is X?` candidates.

### How is `required_entry` enforced in code today: as a hard constraint, a soft prior, or just a tag with no downstream effect?

Today it is just a tag with audit value. It is not a hard constraint and not a
meaningful selection prior. It exists to mark that a candidate should have
been protected, but it does not yet force protection.

### What logic causes a validated-correct beginner question to bypass both `curated_visible` and `cache_servable` and land in `analysis_only` instead?

Two things:

- it inherits V4-style serviceability and curation logic
- V4.1 then re-routes many non-visible items into `analysis_only` when they do
  not meet the hidden-cache threshold or are labeled low distinctiveness

So a question can be valid and grounded, but still be hidden because the
selector optimizes for richer or more distinctive prompts instead of protected
entry coverage.

### Why are there only 8 cache entries when there are 35 validated-correct questions and 27 hidden-but-correct questions? What cache eligibility rule is excluding the rest?

Because the current V4.1 implementation is conservative and effectively keeps
only visible curated items as active cache entries in this run. Hidden correct
items are persisted, but most are not being exported as active cache entries
because the stricter hidden-cache rule is excluding them or they are being
routed straight to `analysis_only`.

### How can we change the pipeline so that every validated-correct question is persisted first, then classified non-destructively, and then surfaced according to policy instead of disappearing behind ranking heuristics?

That structure is mostly in place already. The missing step is to treat
classification and surface selection as separate layers with explicit
promotion/protection rules:

`generate -> validate -> persist ledger -> canonicalize -> assign delivery class -> enforce anchor coverage -> choose visible subset`

The visible subset must not be allowed to contradict anchor coverage rules.

### How can we guarantee that every foundational anchor gets at least one visible canonical entry question before any richer comparison, diagnostic, or transfer questions are selected? The source clearly introduces core concepts early and reuses them later.

Add a hard pre-allocation rule:

1. detect foundational anchors
2. require a canonical definition candidate for each anchor
3. reserve one visible slot per anchor before filling the remaining visible set
   with richer questions

If no definition candidate exists, fail generation or emit a blocking warning.

### Why is the generator producing awkward canonical forms like “What is repeated cycles?” and “What is ljung-box test?” instead of normalized learner-facing forms? Where should canonical noun-phrase rewriting happen?

Because candidate generation is templating directly over extracted labels
without a noun-phrase normalization pass. Canonical rewriting should happen
between topic extraction and question templating, or immediately after raw
candidate generation and before canonicalization. That layer should normalize:

- casing: `Ljung-Box test`
- number: `repeated cycles` -> likely `What are repeated cycles?`
- article choice where needed

### How should canonicalization distinguish between a visible canonical question, a cache-servable canonical question, and alias variants that should only route to the canonical item?

Canonicalization should decide intent grouping only. Delivery should be a later
decision:

- one canonical intent representative
- canonical may be `curated_visible` or `cache_servable`
- aliases should always route to that canonical item and never compete for
  independent visibility unless the intent is actually different

### What post-generation coverage audit should fail when a foundational concept has no visible entry question even though hidden correct variants exist?

A strict audit should fail on:

- `only_hidden_correct_entry_exists`

for any foundational anchor marked required. That means generation succeeded
but selection failed, and the bundle should not be considered policy-clean.

### How should we change the selector so that protected entry questions are exempt from `low_distinctiveness` pruning?

Add a rule:

- if `anchor=true` and `required_entry=true` and the candidate is canonical,
  ignore `low_distinctiveness` as a demotion reason

Distinctiveness can still matter for secondary variants, but not for the one
protected canonical beginner question.

### What regression tests will prove this is fixed, specifically for the pattern where beginner “What is X?” questions are either missing or hidden even though the source clearly introduces X as a core concept?

At minimum:

- `seasonality` in `24491` produces a `What is seasonality?` candidate
- `trend` in `24491` produces a `What is trend?` candidate
- `benchmark methods` produces a definition candidate
- a valid required-entry candidate cannot end as non-visible unless a stronger
  visible canonical definition for the same anchor already exists
- `only_hidden_correct_entry_exists` is impossible in a passing strict run
- `definition_generation_failed` is impossible for required anchors in a
  passing strict run

### How should we redefine the visible-selection objective so it stops over-indexing on pedagogical richness and starts reserving slots for first-contact learner vocabulary questions? The current visible set is almost entirely richer “why/when/how do I know” prompts.

Visible selection should become two-stage:

1. satisfy beginner anchor coverage
2. optimize the remaining slots for richer pedagogical diversity

Right now the system effectively does step 2 only. That is why the visible set
leans toward diagnostic and comparison questions.

### What exact promotion rule should fire when `anchor=true` and `required_entry=true` but there is no visible canonical entry question for that anchor?

The rule should be:

- choose the highest-quality canonical required-entry candidate for that anchor
- promote it to `curated_visible`
- mark displacement reason on the question it replaced, if a visible quota is
  capped

If no candidate exists, emit a blocking `definition_generation_failed`.

### How should the inspection bundle display hidden-but-correct required entry questions so it becomes obvious whether the failure was generation, canonicalization, or selection?

It should show a dedicated section per anchor with three states:

- `generated and visible`
- `generated but hidden`
- `not generated`

And for hidden items, show:

- canonical id
- delivery class
- non-visible reasons
- whether aliasing was involved

That makes the failure source obvious:

- no candidate -> generation failure
- alias only -> canonicalization/routing issue
- hidden canonical required-entry -> selection failure

## Sharpened summary

Required entry questions are still hidden because `required_entry` is only a
tag, not an enforcement rule. Some foundational `What is X?` questions are
never generated because anchor detection and definition generation are still
decoupled. The fix is to make canonical visible entry questions a hard
guarantee by:

- forcing `What is X?` generation for every foundational anchor
- reserving visible slots for anchor definitions
- exempting protected entry questions from low-distinctiveness pruning
- promoting one canonical required-entry question whenever an anchor lacks
  visible entry coverage
- failing strict audits when a required anchor has only hidden or missing
  definition coverage
