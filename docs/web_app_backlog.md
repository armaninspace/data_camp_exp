# Web App Backlog

## Design Direction

The web app should take clear aesthetic inspiration from:

- Aria-Docs GitHub repo: https://github.com/nisabmohd/Aria-Docs
- Aria-Docs site: https://ariadocs.vercel.app/

Use the reference for:

1. calm documentation-first layout
2. clean typography hierarchy
3. restrained color system
4. spacious reading surfaces
5. simple but polished navigation chrome

Do **not** turn this into a generic dashboard.
The visual direction should feel like a documentation reader with an integrated
chat workflow, not a SaaS admin panel.

## Visual Principles

The design backlog should preserve these principles.

1. Documentation-first visual language:
   content should feel readable before it feels interactive.
2. Strong typographic hierarchy:
   course title, section headings, chapter titles, and chat metadata should all
   be visually distinct.
3. Clean structural rhythm:
   spacing should separate content blocks clearly without heavy borders
   everywhere.
4. Minimal accent usage:
   use accent color sparingly for active state, selected course state, and cache
   hit or miss badges.
5. Soft surfaces:
   panels should feel lightweight and editorial, not boxy enterprise UI.

## Product Backlog

## Slice 1: Information Architecture And Design System

Goal:
- establish the shared visual and structural language before implementation

Tasks:

1. Define the page shell:
   1. top bar
   2. left source column
   3. right chatbot column
2. Define responsive breakpoints for desktop and mobile.
3. Define typography scale for:
   1. page title
   2. course title
   3. section headings
   4. metadata labels
   5. body text
   6. code and YAML text
4. Define surface styles for:
   1. cards
   2. section containers
   3. chat bubbles
   4. badges
5. Define color tokens for:
   1. background
   2. text
   3. muted text
   4. borders
   5. accent
   6. cache hit
   7. cache miss

Deliverables:

1. page layout spec
2. spacing and typography tokens
3. basic component style inventory

## Slice 2: App Shell And Navigation

Goal:
- build the persistent frame of the app

Tasks:

1. Implement the top bar.
2. Add the course combo box with typeahead.
3. Add app title and short sublabel.
4. Add a place for run/version badges.
5. Add a stable two-column layout on desktop.
6. Add stacked layout on mobile.

Acceptance criteria:

1. the app shell feels like a docs application, not a dashboard
2. the course selector remains visible while reading and chatting

## Slice 3: Structured Course Source Viewer

Goal:
- make the normalized course artifact readable and scannable

Tasks:

1. Build the course header block:
   1. title
   2. course ID
   3. provider
   4. level
   5. subjects
2. Build a metadata grid for:
   1. duration
   2. pricing
   3. language
   4. source URL
3. Build summary and overview sections.
4. Build the chapter outline list with provenance and confidence treatment.
5. Add optional raw YAML or raw JSON toggle.

Design notes:

1. chapter cards should be easy to scan vertically
2. `syllabus` vs `overview_inferred` provenance should be visible but subtle
3. long overview text should be readable and collapsible if necessary

Acceptance criteria:

1. a reviewer can understand the course artifact without opening raw files
2. the chapter section is visually strong enough to anchor the left column

## Slice 4: Semantic Artifact Panels

Goal:
- expose derived artifacts without confusing them with source truth

Tasks:

1. Add optional learning-outcomes panel.
2. Add optional question-cache panel.
3. Visually label these panels as derived.
4. Support collapse and expansion.
5. Show claim citations in a compact expandable pattern.

Design notes:

1. source content should remain visually primary
2. semantic artifacts should feel layered underneath or beside the source
3. avoid overwhelming the page with all artifacts expanded by default

Acceptance criteria:

1. reviewers can inspect semantic outputs without losing context
2. the distinction between source and derived content is visually obvious

## Slice 5: Chatbot Interface

Goal:
- build a clean course-scoped conversation surface

Tasks:

1. Build the chat thread.
2. Build the message input row.
3. Add loading and disabled states.
4. Add course-scoped chat header text.
5. Clear or explicitly reset chat on course change.

Design notes:

1. chat should feel integrated with the docs shell, not like an embedded widget
2. message spacing and line length should favor readability
3. metadata should not visually drown out the answer text

Acceptance criteria:

1. user can ask a question against the selected course
2. chat remains readable on long answers

## Slice 6: Cache Hit Or Miss UX

Goal:
- make cache behavior visible and trustworthy

Tasks:

1. Add `cache hit` badge styling.
2. Add `cache miss` badge styling.
3. Add metadata row for:
   1. match score
   2. claim ID
   3. question group ID
   4. miss reason
4. Add optional expand/collapse for technical metadata.

Design notes:

1. hit or miss state should be immediately visible
2. technical details should be available but secondary
3. hit or miss color should not dominate the whole message card

Acceptance criteria:

1. every assistant response clearly indicates hit or miss
2. provenance details are inspectable without cluttering the main answer

## Slice 7: Frontend Data Flows

Goal:
- wire the UI to the backend data surfaces

Tasks:

1. Course list loading.
2. Course detail loading.
3. Semantic artifact loading by selected course.
4. Chat request submission.
5. Hit or miss response rendering.
6. Error handling and retry states.

Acceptance criteria:

1. course switching updates the left column correctly
2. chat always uses the current selected course

## Slice 8: Backend APIs

Goal:
- support the web app with minimal clear endpoints

Tasks:

1. Add course list endpoint.
2. Add course detail endpoint.
3. Add semantic artifact endpoint or embed semantic artifacts in course detail.
4. Add chat endpoint with cache-first logic.
5. Add request and response typing.

Acceptance criteria:

1. frontend can render all required information pieces from stable APIs
2. chat endpoint returns explicit `cache_hit` or `cache_miss`

## Slice 9: Cache-First Chat Backend

Goal:
- connect UI chat to the current runtime cache behavior

Tasks:

1. Resolve selected course ID from the request.
2. Query runtime-eligible cache artifacts only.
3. Return cached answer on hit.
4. Return LLM answer on miss.
5. Include hit or miss metadata in the response.
6. Log the interaction.

Acceptance criteria:

1. hit path is fast and deterministic
2. miss path is explicit and inspectable

## Slice 10: Interaction Logging And Review Hooks

Goal:
- preserve enough information for debugging and future cache warming

Tasks:

1. Log incoming question.
2. Log normalized question.
3. Log course ID.
4. Log hit or miss.
5. Log score and group lineage on hit.
6. Log miss reason on miss.
7. Make logs queryable for review.

Acceptance criteria:

1. every chat interaction is diagnosable later
2. fallback traffic can be reviewed for cache warming

## Slice 11: Polishing Pass

Goal:
- make the app feel intentionally designed rather than merely functional

Tasks:

1. refine spacing and alignment
2. refine typography weights and sizes
3. tune section density
4. improve chapter list readability
5. polish chat message layout
6. tune empty, loading, and error states

Acceptance criteria:

1. the app visibly reflects the documentation-inspired aesthetic
2. the reading experience feels calm and deliberate

## Slice 12: Internal Review Mode

Goal:
- support reviewer workflows without exposing all internals in the default view

Tasks:

1. add a reviewer toggle or debug drawer
2. expose validation state for question-cache artifacts
3. expose citations and provenance more deeply
4. expose raw artifact links where useful

Acceptance criteria:

1. default view stays clean
2. reviewer detail is still accessible when needed

## Suggested Build Order

1. Slice 1
2. Slice 2
3. Slice 3
4. Slice 5
5. Slice 8
6. Slice 9
7. Slice 6
8. Slice 7
9. Slice 10
10. Slice 4
11. Slice 11
12. Slice 12

## Definition Of Done

The web app is ready for internal review when:

1. the course selector works smoothly
2. the standardized course source is clearly laid out
3. the chatbot is course-scoped
4. every answer clearly shows cache hit or miss
5. cache provenance is inspectable
6. the visual design clearly reflects the documentation-first reference
   direction inspired by Aria-Docs without copying it mechanically
