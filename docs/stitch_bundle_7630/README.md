# Stitch Bundle: Introduction to R (7630)

This bundle is for theme and layout design work against the current course
review app using the real `Introduction to R (7630)` content.

## What Is Included

1. Screenshots from the live app:
   - [7630-overview-desktop.png](/code/docs/stitch_bundle_7630/screenshots/7630-overview-desktop.png)
   - [7630-precomputed-qa-desktop.png](/code/docs/stitch_bundle_7630/screenshots/7630-precomputed-qa-desktop.png)
   - [7630-precomputed-qa-mobile.png](/code/docs/stitch_bundle_7630/screenshots/7630-precomputed-qa-mobile.png)
2. Full course payload from the running app:
   - [course_7630_payload.json](/code/docs/stitch_bundle_7630/course_7630_payload.json)
3. Condensed content and section inventory:
   - [content_inventory.json](/code/docs/stitch_bundle_7630/content_inventory.json)
4. A direct Stitch prompt:
   - [stitch_prompt.md](/code/docs/stitch_bundle_7630/stitch_prompt.md)

## What Stitch Should Design

Design a calm documentation-style theme for a course inspection app with:

1. a top course picker
2. a primary source-reading column
3. a secondary chat column
4. a derived-artifacts area with tabs
5. a dedicated `Precomputed Q&A` inspection view

## Important Product Constraints

1. This is not a dashboard.
2. The standardized course source remains the primary artifact.
3. Derived semantic artifacts should feel inspectable, but visually secondary.
4. Cache hit or miss state should be visible inside chat, but not dominate the
   whole page.
5. The precomputed Q/A pairs need their own clear inspection treatment because
   they are one of the core review surfaces.

## Key Facts From This Course

1. `course_id`: `7630`
2. title: `Introduction to R`
3. provider: `DataCamp`
4. level: `beginner`
5. chapters: `6`
6. learning outcomes: `8`
7. question-cache groups: `21`
8. runtime-eligible precomputed Q/A pairs: `5`

## Recommended Stitch Input Order

1. Give Stitch the screenshots first.
2. Give it [stitch_prompt.md](/code/docs/stitch_bundle_7630/stitch_prompt.md).
3. If Stitch needs structure or exact content shape, attach
   [content_inventory.json](/code/docs/stitch_bundle_7630/content_inventory.json).
4. If Stitch needs full real content, attach
   [course_7630_payload.json](/code/docs/stitch_bundle_7630/course_7630_payload.json).
