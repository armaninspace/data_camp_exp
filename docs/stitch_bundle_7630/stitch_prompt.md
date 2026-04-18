# Stitch Prompt

Design a refined visual theme for a course review web app using the attached
screenshots and course payload for `Introduction to R (7630)`.

The app is a documentation-style inspection surface, not a SaaS dashboard.
Use a calm editorial aesthetic with strong typography, generous spacing, soft
surfaces, and restrained accent color. The current design direction is already
close to an Aria-Docs style reading interface, but the new theme should feel
more intentional and polished.

## Core UI Regions

1. top bar with course picker and run badges
2. left content column with:
   - course header
   - metadata
   - summary
   - overview
   - chapters
   - derived-artifact tabs
   - raw YAML
3. right chat column with:
   - course-scoped chat header
   - chat thread
   - question input
   - visible `cache hit` or `cache miss` state

## Special Focus

Give extra design attention to the `Precomputed Q&A` tab. It should feel like a
review surface for prebuilt canonical question/answer pairs, with:

1. a clear canonical question treatment
2. a readable precomputed answer block
3. accepted variations shown as supporting material
4. a lightweight runtime or validated badge

## Visual Guidance

1. Make the left column feel like a document reader.
2. Make the chat column feel integrated, not like a pasted widget.
3. Preserve high scanability for chapter cards and derived cards.
4. Use tabs that feel crisp and editorial, not heavy enterprise pills.
5. Improve hierarchy for long text blocks and raw technical content.
6. Support both desktop and mobile.

## Avoid

1. generic analytics dashboard styling
2. loud neon accents
3. overly boxy card grids
4. visually flattening the source and derived layers into the same priority
5. hiding the precomputed Q/A inspection feature

## Deliverable

Produce a cohesive theme direction for this product, including:

1. typography direction
2. color system
3. surface treatment
4. tab styling
5. card styling for source content and precomputed Q/A pairs
6. mobile adaptation
