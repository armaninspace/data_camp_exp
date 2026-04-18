# Airspace + OSM Context Visualization POC Requirements (Extended)
## Client-Facing Mapbox Demo for U.S. Airspace Layers and OSM Objects Within 13 Miles of a Point of Interest

**Version:** 0.3  
**Date:** April 7, 2026  
**Status:** Extended after review of sister-project engineering note, compatibility memo, post-implementation debrief, and a second sister-project pattern for OSM object ingestion

---

## 1. Why this extension exists

The prior revision sharpened the airspace-class demo around a lesson from the ADS-B / historical-air-risk sister project:

- local persisted data beats live-demo fragility
- technically honest claims beat inflated product language
- visual polish matters as much as backend correctness in front of a client

This extension adds another sister-project pattern:

**download and persist surrounding ground-context objects from OpenStreetMap within a 13-mile radius around a point of interest, then display them as inspectable layers in the same Mapbox experience.**

That changes the POC again.

This is no longer just an “airspace class overlay” demo. It becomes a **multi-source geospatial context demo** showing that we can:

1. ingest official FAA airspace geometry on a cycle basis
2. ingest local OSM feature context around a point of interest
3. normalize and persist both into PostGIS
4. serve them through typed APIs
5. render them as a clean, inspectable, client-ready map experience

This is a stronger demo of technical capability than either layer on its own.

---

## 2. Lessons from the sister projects that should directly shape this POC

### 2.1 Local data first, always

The historical air-risk POC proved that a strong architecture can still produce a weak demo if the visible behavior depends on an upstream service that does not actually provide the expected data. The cleanest lesson is simple:

**The demo should run from locally persisted data, not live provider calls.**

That applies even more strongly here.

For this combined POC:

- FAA airspace data shall be imported ahead of time from the selected NASR cycle
- OSM objects shall be pulled ahead of time for chosen preset points of interest
- the frontend shall query only the local backend and local PostgreSQL/PostGIS store during the demo

This makes the demo repeatable, deterministic, and resilient.

### 2.2 Demonstration presets are part of the product

The first sister project had to shift defaults because the “correct” operational default was visually weak in the available dataset.

The same principle applies here.

The demo should not open on a random point and hope the client appreciates the geometry. It should open on places where both the airspace and the OSM object layers visibly prove value.

### 2.3 Be precise about the claim

The strongest honest claim for this extended POC is:

**“We can fuse official FAA airspace boundaries and localized OSM context around a selected point of interest into a single persisted geospatial system and render it cleanly in a Mapbox interface.”**

The demo should not claim:

- real-time operational airspace awareness
- complete legal interpretation of every drone-related rule
- guaranteed completeness of every OSM feature in the world
- measured heights for every building or object

### 2.4 Styling and interaction are required, not optional polish

The sister debrief showed that map defaults are rarely good enough for client work.

For this combined POC:

- airspace layers must be clearly styled and distinguishable
- OSM layers must not visually overwhelm the airspace layers
- hover, click, selection, legend, and provenance affordances are required
- height display must be visually clear about whether a value is explicit, inferred, or unknown

### 2.5 Demo mode and operational mode may differ

A client-facing demo may use carefully chosen presets, tuned layer defaults, and prebuilt imports.

That is acceptable as long as:

- the architecture is real
- the data is real
- the claims are accurate
- the code path is compatible with later production work

---

## 3. Product question this POC should answer

This demo should answer the question:

**“What controlled airspace classes and surrounding surface-context objects exist within 13 miles of a selected point of interest, and can they be explored, filtered, and inspected cleanly in a reusable operational map experience?”**

The client story should be:

1. open a clean web app
2. choose a preset or enter a point of interest
3. instantly see official FAA class-airspace overlays
4. toggle nearby OSM objects of interest on and off
5. click an object or airspace area to inspect attributes, provenance, and height information where available
6. see that all visible data is coming from a typed backend and local PostGIS database, not from hardcoded frontend mock layers

---

## 4. Core POC requirement

The system shall support display of:

1. **official U.S. FAA class-airspace overlays**, and  
2. **OSM-derived objects of interest within a 13-mile radius of a point of interest**

on a Mapbox map, backed by a local PostgreSQL/PostGIS database.

### 4.1 Required airspace scope for v1

The first pass shall explicitly support:

- **Class B**
- **Class C**
- **Class D**
- **Class E**

### 4.2 Required OSM scope for v1

The first pass shall support ingestion and display of curated OSM feature families within the selected radius.

At minimum, the UI should support these families:

- **Education**
  - schools
  - colleges
  - universities
  - kindergartens
- **Healthcare**
  - hospitals
  - clinics
- **Public safety / civic**
  - fire stations
  - police
  - government / civic facilities where mapped
- **Critical infrastructure / tall structures**
  - substations
  - generators where mapped
  - towers / masts / water towers where mapped
- **Transportation context**
  - airports / aeroway features where relevant
  - rail corridors
  - major roads
  - bridges where tagged
- **Buildings / structures**
  - buildings with explicit or inferable height data
- **Water / land context**
  - waterways or landuse features only if helpful for orientation and not visually noisy

### 4.3 Strong requirement on the phrase “any object”

The backend may ingest and persist a broad raw OSM result set, but the client-facing map should expose **curated layer groups**, not an undifferentiated firehose of every OSM tag.

That means:

- the system may store any returned nodes / ways / relations in the radius
- the UI should present objects through meaningful categories and toggles
- the demo should avoid a claim that every possible OSM feature is equally normalized or equally useful in v1

This is an honesty and usability requirement.

---

## 5. The 13-mile spatial contract

The OSM portion of the demo shall center on a point-of-interest workflow.

### 5.1 Required input contract

The backend shall accept:

- `latitude`
- `longitude`
- optional `label`
- optional `radiusMiles`, defaulting to **13**

Example request payload:

```json
{
  "pointOfInterest": {
    "latitude": 34.7305,
    "longitude": -86.5861,
    "label": "Huntsville demo point"
  },
  "radiusMiles": 13
}
```

### 5.2 Radius conversion requirement

The canonical radius for the OSM query pipeline shall be stored in meters as well as miles.

For the default:

- `13 miles = 20,921.472 meters`

The backend should round or normalize this to a practical integer value for provider queries and database storage.

### 5.3 Spatial implementation requirement

The system shall:

- store the point of interest as a PostGIS geography point
- store OSM feature geometry in PostGIS geometry or geography columns as appropriate
- apply the 13-mile rule on the backend, not in frontend code
- persist the exact point and exact query radius used for each ingestion run

---

## 6. Source data requirements

### 6.1 FAA source

The primary airspace source shall be the FAA **28-Day NASR Subscription**.

Preferred airspace inputs:

- Class B/C/D/E shapefiles
- class-airspace CSV metadata
- effective cycle metadata

### 6.2 OSM source

The primary surface-context source shall be **OpenStreetMap data retrieved through Overpass queries**.

The retrieval strategy should be:

- query by point and radius
- query by curated feature-family templates
- persist the raw returned tags and canonicalized feature model locally
- avoid runtime dependence on Overpass during the demo

### 6.3 Source posture requirement

The system shall:

- download or query source data ahead of time
- normalize and validate required fields
- persist source provenance
- serve the UI from the local database only during normal demo interactions

### 6.4 Licensing and attribution requirement

Because OSM data is reused in this product surface, the demo must include:

- visible OpenStreetMap attribution
- internal tracking of source provenance for OSM-derived objects
- a lightweight legal review of how exported or persisted derivative data is being used in the POC

The purpose here is not to overcomplicate the demo. It is to avoid quietly creating a licensing problem.

---

## 7. OSM ingestion requirements

We need a backend ingestion flow that pulls OSM features for a geographic area, normalizes them, and stores them locally.

### 7.1 Ingestion flow

The ingestion component shall:

1. accept a center point and radius
2. choose one or more feature-family query templates
3. execute the OSM retrieval
4. capture the raw result payload
5. normalize returned nodes / ways / relations into a canonical schema
6. validate required fields
7. deduplicate where needed
8. persist both normalized geometry and raw tag payloads
9. retain source query text, retrieval time, and provenance

### 7.2 Query strategy requirement

The system should not begin with a single giant “everything in radius” query as the primary demo path.

Instead it should:

- maintain explicit query templates per feature family
- allow manual or scripted refreshes per point of interest
- optionally support a broader raw-capture mode for engineering use
- expose only curated layer groups to the client-facing UI

This keeps the demo performant, understandable, and maintainable.

### 7.3 Raw and canonical data requirement

For each ingestion run, the system should persist both:

- a **raw source snapshot** for provenance and debugging
- a **canonical feature representation** for querying, filtering, exporting, and rendering

### 7.4 Required outputs

At minimum, each stored OSM feature record should include:

- OSM element type (`node`, `way`, `relation`)
- OSM element ID
- canonical feature name, if present
- feature family
- primary tag classification
- geometry in PostGIS
- centroid where useful
- source tags JSON
- point-of-interest relation or ingestion-run relation
- retrieval timestamp
- source query metadata

---

## 8. Height and elevation requirements

This is one of the most important places to stay technically honest.

The demo may show heights for schools and other objects **only when the underlying data supports it, or when a clearly labeled inference rule is applied.**

### 8.1 Explicit height fields

The normalization pipeline should recognize, at minimum:

- `height`
- `min_height`
- `building:levels`
- deprecated `building:height` where present in source data

### 8.2 Canonical height posture

The canonical schema should distinguish between:

- `explicitHeightM`
- `minHeightM`
- `buildingLevels`
- `estimatedHeightM`
- `heightSource`

Recommended `heightSource` enum values:

- `explicit_height_tag`
- `deprecated_building_height_tag`
- `inferred_from_levels`
- `external_enrichment`
- `unknown`

### 8.3 Inference rule requirement

If the system infers height from `building:levels`, that logic must be:

- explicit
- documented
- configurable
- clearly marked in the UI and exports

For example, a simple demo heuristic might use:

- `estimatedHeightM = buildingLevels * configurableMetersPerLevel`

That can be acceptable for a POC as long as it is not presented as surveyed truth.

### 8.4 Important requirement for schools

A school may exist as:

- a point feature
- a campus polygon
- a building polygon
- an amenity tag without explicit height

Therefore:

- the system shall not assume that every school has a meaningful height
- the system shall allow height to be null
- the UI should clearly distinguish “unknown” from “0”

### 8.5 Stretch option

A future enhancement may enrich building or terrain elevation from additional sources, but that should be treated as optional and separately labeled from OSM-native height data.

---

## 9. Database requirements

The POC shall use **PostgreSQL with PostGIS** as the system of record.

### 9.1 Core tables

Recommended minimum schema:

#### `users`
- `id`
- `email`
- `passwordHash`
- `role`
- `createdAt`
- `updatedAt`

#### `sessions`
- `id`
- `userId`
- `sessionToken`
- `expiresAt`
- `createdAt`

#### `points_of_interest`
- `id`
- `label`
- `latitude`
- `longitude`
- `locationGeog`
- `createdBy`
- `createdAt`

#### `airspace_ingestion_runs`
- `id`
- `sourceName`
- `faaCycle`
- `status`
- `rowsFetched`
- `rowsInserted`
- `retrievedAt`
- `errorSummary`

#### `airspace_features`
- `id`
- `sourceName`
- `faaCycle`
- `airspaceClass`
- `designation`
- `lowerText`
- `upperText`
- `geom`
- `retrievedAt`
- `rawPayloadJson`

#### `osm_ingestion_runs`
- `id`
- `sourceName`
- `pointOfInterestId`
- `requestedRadiusMeters`
- `queryTemplateName`
- `queryText`
- `status`
- `rowsFetched`
- `rowsInserted`
- `retrievedAt`
- `errorSummary`

#### `osm_features`
- `id`
- `osmType`
- `osmId`
- `pointOfInterestId` or query-time relation
- `featureFamily`
- `primaryCategory`
- `name`
- `geom`
- `centroidGeom`
- `heightM`
- `minHeightM`
- `buildingLevels`
- `estimatedHeightM`
- `heightSource`
- `tagsJson`
- `retrievedAt`

#### `exports`
- `id`
- `userId`
- `format`
- `filterJson`
- `generatedAt`
- `filePath`

### 9.2 Indexing

Required indexes:

- spatial index on `airspace_features.geom`
- spatial index on `osm_features.geom`
- optional spatial index on `osm_features.centroidGeom`
- index on `osm_features.featureFamily`
- index on `osm_features.osmType, osm_features.osmId`
- index on `retrievedAt`
- optional composite indexes for common filter patterns

### 9.3 Canonical geometry posture

Geometry shall live in PostGIS columns, not only in frontend GeoJSON or raw JSON blobs.

The database is the system of record.

---

## 10. Filtering and query requirements

### 10.1 Required map filters

The UI and API should support, at minimum:

- point of interest
- radius
- airspace class toggle
- OSM feature family toggle
- “show only features with explicit height” toggle
- minimum height threshold where relevant
- search by object name when present

### 10.2 Height filter behavior

If a user filters by height, the system should allow one or both of the following modes:

- explicit height only
- explicit + inferred height

This prevents silent mixing of measured and estimated values.

### 10.3 Combined spatial queries

The backend should be able to answer queries such as:

- all OSM objects of selected families within 13 miles of the point of interest
- all OSM objects in the current viewport
- all visible OSM objects intersecting the selected airspace polygons
- counts of objects by family and height-source category

These are useful not only for product value but for demonstrating real spatial backend capability.

---

## 11. API requirements

The API should use Fastify with Zod-based request and response contracts.

### Suggested routes

#### Auth
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

#### Reference / config
- `GET /reference/points-of-interest`
- `POST /reference/points-of-interest`
- `GET /reference/presets`
- `GET /reference/filter-options`

#### Ingestion
- `POST /ingestion/airspace/import`
- `GET /ingestion/airspace/runs`
- `POST /ingestion/osm/pull`
- `GET /ingestion/osm/runs`
- `GET /ingestion/osm/runs/:id`

#### Map / data
- `GET /map/airspace`
- `GET /map/osm-features`
- `GET /map/combined-summary`
- `GET /map/feature/:source/:id`
- `GET /map/export`

#### Health
- `GET /health`

Each route should have:

- a Zod request schema
- a Zod response schema
- a consistent error model

---

## 12. Frontend requirements

The frontend should stay visually calm and operational.

### 12.1 UI layout

Recommended layout:

- simple header
- narrow left filter / layer panel
- large central map
- optional right-side details drawer
- clear provenance area
- export action

### 12.2 Required map interactions

The user shall be able to:

- toggle airspace classes on and off
- toggle OSM feature families on and off
- hover features for lightweight preview
- click features for full detail
- zoom to selected feature
- switch among preset scenes

### 12.3 Required detail panel behavior

Clicking an airspace feature should show:

- class
- designation
- lower altitude text
- upper altitude text
- FAA cycle or ingest date
- source name

Clicking an OSM feature should show:

- name if present
- feature family
- canonical category
- height information
- height source
- selected source tags
- retrieval time
- OSM source attribution

### 12.4 Layer styling requirements

#### Airspace layers
- separate fill and outline styling per airspace class
- selected feature highlight state
- readable legend

#### OSM layers
- symbols, lines, fills, or circles depending on feature family
- visually subordinate to primary airspace overlays by default
- clustering only if data density requires it
- optional 3D extrusion for features with explicit or inferred height

### 12.5 Height visualization requirement

If 3D extrusion is used, the UI must make it obvious whether the extrusion is based on:

- explicit height tag
- inferred height

A legend, badge, or detail-panel label is sufficient.

---

## 13. Demo-first requirements

These are specifically about making the POC impressive in front of a client.

### 13.1 Preset scene requirement

The UI shall include at least **three preset scenes** that show different combinations of airspace richness and OSM object density.

Suggested examples:

- **Major metro / Class B + dense surface context**
- **Regional airport / Class C-D + civic objects**
- **Sparse environment / comparison case**

### 13.2 Strong default requirement

The app should open on a preset view that immediately shows:

- visible controlled airspace geometry
- visible nearby objects of interest
- at least one feature with inspectable height data or clearly unknown height state

### 13.3 Provenance requirement

The UI shall visibly show:

- FAA cycle or airspace ingest date
- OSM retrieval date
- indication that the current view is backed by locally persisted data

### 13.4 Demo script requirement

The POC should support a crisp walkthrough like:

1. choose a preset point of interest
2. show Class B/C/D/E overlays
3. toggle on schools and hospitals within 13 miles
4. click a school or building and inspect height status
5. filter to explicit-height structures only
6. export the visible subset as GeoJSON or CSV

That sequence shows architecture, data fusion, and map polish in under a few minutes.

---

## 14. Export requirements

The system should allow export of the current filtered dataset from the local database.

### Required export formats

- CSV
- GeoJSON
- JSON

### Export rules

The export must respect active filters such as:

- point of interest
- radius
- selected airspace classes
- selected OSM feature families
- height-source mode
- height threshold
- viewport or current selection if applicable

### Required export provenance

Exports should include, where relevant:

- source name
- source cycle or retrievedAt
- OSM element type and ID
- height source
- raw or normalized category fields

---

## 15. Auth requirements

For the POC, auth should stay intentionally basic.

### Required auth scope

- email + password login
- logout
- protected app and API routes
- persistent session
- minimal roles such as `admin` and `viewer`

Permission checks should live in application code, not only in controllers or frontend code.

---

## 16. Testing requirements

The POC should use **Vitest** and include both domain-level and integration-level testing.

### Unit tests

- radius conversion and spatial helper logic
- OSM tag normalization rules
- height parsing and inference logic
- export shaping
- combined filter behavior

### Integration tests

- FAA import into PostgreSQL/PostGIS
- OSM ingestion into PostgreSQL/PostGIS
- spatial radius filtering
- feature-family filtering
- explicit vs inferred height filtering
- auth/session flow
- export path

### Optional end-to-end tests

If time allows, add a small Playwright or equivalent smoke test covering:

- preset load
- layer toggles
- click inspection
- export trigger

---

## 17. Safe shortcuts for the POC

The following simplifications are acceptable without breaking forward compatibility:

- single deployable service
- basic local auth only
- manual ingestion triggers
- prebuilt preset datasets
- curated OSM query templates instead of universal normalization of every tag family
- limited height inference rules
- no vector tiles in v1
- no background job system unless clearly needed

These shortcuts reduce surface area without breaking the architecture.

---

## 18. Things to avoid

Do not introduce choices that create migration work later.

Avoid:

- a different primary backend language
- a different primary web framework
- SQLite, MongoDB, Firestore, or Redis as the source of truth
- canonical geometry stored only as frontend GeoJSON
- business rules embedded in route handlers
- validation only in UI code
- permission checks only in frontend code
- runtime dependence on Overpass during the client demo
- presenting inferred height as measured height
- claiming “all objects” are equally normalized in v1 when only curated groups are productized

---

## 19. Recommended implementation sequence

### Phase 1: foundation
- bootstrap Fastify + TypeScript service
- add Zod validation
- provision PostgreSQL + PostGIS locally
- set up Drizzle migrations
- create auth tables and local login
- add Vitest harness

### Phase 2: airspace import
- ingest FAA class-airspace data
- persist source cycle and geometry
- expose airspace query endpoint

### Phase 3: OSM ingestion
- implement point + radius input contract
- build curated Overpass query templates
- persist raw and canonical OSM objects
- normalize height fields and height-source labels
- add indexes

### Phase 4: map API and frontend
- implement combined map endpoints
- add preset scenes
- build Mapbox airspace layers
- add OSM feature layers
- add detail drawer and provenance display
- add export action

### Phase 5: polish
- tune layer styling and ordering
- add optional 3D extrusions for selected structures
- improve filter UX
- refine presets and demo script
- add legal/attribution check for OSM usage and exports

---

## 20. Bottom-line recommendation

This POC should be built as a **TypeScript / Fastify / PostgreSQL / PostGIS / Drizzle / Zod** modular monolith that fuses:

- **FAA class-airspace overlays** from official NASR data, and
- **OSM objects of interest within 13 miles of a point of interest** from pre-ingested Overpass-based retrieval

into a single persisted geospatial system.

The key to making it impressive is not claiming more than it does.

The win is:

- official source ingestion
- local persistence
- real geospatial querying
- clean Mapbox rendering
- inspectable provenance
- honest treatment of object heights

That combination will do a much better job of showing technical depth than either an airspace-only overlay or a noisy generic OSM map.
