# Web App Requirements

## Purpose

Build a simple course inspection web app with a cache-first chatbot.

The app should let a reviewer:

1. choose a course from a combo box at the top
2. inspect the standardized course source in a readable layout
3. ask course-scoped questions in a chatbot
4. see whether the answer was a `cache hit` or `cache miss`
5. receive an LLM answer when the cache misses

This document is expanded for design and layout work, so it describes not only
behavior but also the full information pieces that should be visible for a
course.

## Product Framing

This is a course-scoped inspection and Q/A app.

It is:

1. a viewer for standardized course artifacts
2. a reviewer surface for cache-backed answers
3. a debugging surface for cache hit or miss behavior

It is not:

1. a full tutoring product
2. a learner dashboard
3. a multi-course search app
4. a personalized adaptive teaching system

## Primary Screen Model

The app should have one main screen with three persistent regions:

1. top bar
2. course information area
3. chatbot area

Recommended desktop layout:

1. top bar across full width
2. two-column body
   1. left column: course source and structured metadata
   2. right column: chatbot thread and input

Recommended mobile layout:

1. top bar
2. course info panel
3. chatbot panel
4. stacked vertically

## Top Bar Requirements

The top bar should contain:

1. app title or label
2. course combo box
3. optional run/version badge
4. optional cache status indicator

### Course combo box

The combo box should:

1. support typing to filter courses
2. show both title and course ID
3. be wide enough to accommodate long course names
4. allow quick switching without full page reload

Suggested option format:

- `Introduction to R (7630)`

## Main Information Architecture

When a course is selected, the designer should lay out the following
information pieces.

These pieces should not be shown as one giant raw blob by default.
The first view should be structured and scannable.

## Course Information Area

The course information area should be organized into sections.

Recommended sections:

1. Course header
2. Core metadata
3. Summary and overview
4. Chapter outline
5. Optional semantic layer
6. Optional raw source toggle

## 1. Course Header

The course header should display:

1. `title`
2. `course_id`
3. `provider`
4. optional `level`
5. optional short subject chips

Recommended visual hierarchy:

1. title as the strongest text
2. provider and course ID as secondary metadata
3. level and subjects as chips or small badges

## 2. Core Metadata

This section should display the normalized scalar fields.

Fields to include:

1. `provider`
2. `course_id`
3. `level`
4. `duration_hours`
5. `pricing`
6. `language`
7. `source_url`
8. optional `final_url`

Recommended layout:

1. compact definition-list style on desktop
2. two-column metadata grid where space allows
3. single column on mobile

## 3. Summary And Overview

This section should display:

1. `summary`
2. `overview`

Design guidance:

1. show `summary` first because it is shorter
2. show `overview` in a readable long-form block
3. collapse long text by default with a “show more” control if needed

## 4. Subjects

Subjects should be displayed as chips, tags, or a compact inline list.

This should be visually lightweight and near the course header or metadata.

## 5. Chapter Outline

The chapter area is one of the most important parts of the source viewer.

Each chapter item should show:

1. `chapter_index`
2. `title`
3. `summary`
4. `source`
5. `confidence`

### Why this matters

The chapter list is the best bridge between the source course artifact and the
later semantic/chat behavior.

The designer should make it easy to scan chapter boundaries quickly.

### Recommended chapter card layout

Each chapter row or card should include:

1. a chapter number badge
2. chapter title
3. chapter summary text
4. a small provenance line such as:
   1. `source: syllabus`
   2. `source: overview_inferred`
5. a confidence indicator only if useful

### Provenance styling

Chapter provenance should be visually visible but subtle.

Recommended:

1. `syllabus` as neutral/positive
2. `overview_inferred` as lower-confidence or subdued

## 6. Ratings And Raw Details

If ratings or extra details exist, they should not dominate the page.

Recommended treatment:

1. put `ratings` in a collapsible panel or tertiary metadata section
2. put raw `details` in a secondary “Raw normalized fields” accordion

This avoids cluttering the main reading flow.

## 7. Optional Semantic Layer Panels

If semantic artifacts exist for the selected course, the app should support
showing them below or beside the source viewer.

Optional panels:

1. learning outcomes
2. question-cache groups

These should be clearly marked as derived artifacts, not source truth.

### Learning outcomes panel

If shown, each learning outcome should display:

1. `id`
2. `claim`
3. `knowledge_type`
4. `process_level`
5. `confidence`
6. `citations`

Recommended layout:

1. claim as the headline
2. taxonomy labels as chips
3. citations in a collapsible evidence block

### Question-cache panel

If shown, each question group should display:

1. `question_group_id`
2. `claim_id`
3. `canonical_question`
4. `validator_status`
5. `canonical_answer`
6. accepted or rejected variations

This panel is especially useful for internal review builds.

## Raw Source Toggle

The app should provide an optional raw source view.

Recommended options:

1. `Structured`
2. `Raw YAML`
3. `Raw JSON`

Default:
- `Structured`

The raw view is useful for debugging and reviewer trust, but it should not be
the default design mode.

## Chatbot Area

The chatbot area should contain:

1. conversation header
2. message thread
3. input row
4. response metadata display

## Chatbot Header

The chatbot header should include:

1. selected course title
2. short line indicating course scope
3. optional cache layer status

Example:

- `Chatting about: Introduction to R`
- `Scope: course 7630`

## Message Thread

Each message should include:

1. sender identity
2. message body
3. timestamp or sequence indicator
4. metadata for assistant messages

### Assistant message metadata

For every assistant answer, visibly show:

1. `cache hit` or `cache miss`
2. optional match score
3. optional question group ID
4. optional claim ID
5. optional fallback reason

Recommended styling:

1. `cache hit` badge in one color
2. `cache miss` badge in another
3. metadata line below the answer, not above it

## Input Row

The input row should include:

1. a text field
2. a send button
3. loading state while waiting

Recommended behavior:

1. disable input while request is in flight
2. keep the course selector usable
3. clear the input after successful send

## Designer Notes On Information Priority

The designer should prioritize information in this order:

1. course title and selection
2. chapter structure
3. summary and overview
4. chat interaction
5. semantic-derived artifacts
6. raw fields and debug details

This means the page should feel like:

1. a course reading surface first
2. a cache-debugging and question-answering surface second

## State Requirements

The design must include these states.

### 1. Empty state

When no course is selected:

1. show an instruction to select a course
2. disable chat input

### 2. Loading state

When a course is loading:

1. show skeleton or loading placeholders in the source area
2. disable chat input until the course context is ready

### 3. No semantic data state

If the course has standardized source but no semantic artifacts:

1. show the source normally
2. show a light notice that no learning outcomes or cache artifacts are
   available yet

### 4. Cache hit state

When a chat response is served from cache:

1. show `cache hit`
2. show the answer
3. optionally show provenance metadata

### 5. Cache miss state

When the cache does not serve the answer:

1. show `cache miss`
2. show the LLM answer
3. optionally show the miss reason

### 6. Error state

When course loading or chat fails:

1. show a clear error message
2. do not collapse the whole screen
3. allow retry

## Backend Requirements

### Course list endpoint

Must return:

1. course ID
2. title
3. optional provider

### Course detail endpoint

Must return the standardized course artifact for the selected course.

At minimum:

1. `course_id`
2. `title`
3. `summary`
4. `overview`
5. `subjects`
6. `level`
7. `duration_hours`
8. `pricing`
9. `language`
10. `chapters`
11. optional semantic artifacts if available

### Chat endpoint

Must accept:

1. `course_id`
2. `question`
3. optional conversation history

Must return:

1. `status`: `cache_hit` or `cache_miss`
2. `answer_markdown`
3. `course_id`
4. optional `claim_id`
5. optional `question_group_id`
6. optional `match_score`
7. optional `fallback_reason`

## Logging Requirements

For every question asked, log:

1. `course_id`
2. incoming question
3. normalized question
4. hit or miss
5. match score if hit
6. question group ID if hit
7. canonical answer ID if hit
8. miss reason if miss

## Recommended Implementation Slices

### Slice 1: Course browser

1. combo box
2. structured course viewer
3. raw source toggle

### Slice 2: Basic chatbot

1. chat thread
2. send flow
3. cache hit or miss label
4. LLM fallback on miss

### Slice 3: Review metadata

1. learning-outcome panel
2. question-cache panel
3. provenance and cache metadata drawer

## Acceptance Criteria

The first design-ready version is acceptable when:

1. every course information piece needed for layout is explicitly defined
2. the main screen structure is clear on desktop and mobile
3. the source viewer hierarchy is clear
4. the chat area clearly distinguishes cache hit from cache miss
5. semantic-derived panels are clearly marked as derived, not source truth
