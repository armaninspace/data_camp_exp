You are updating an existing Python pipeline that generates question-inspection artifacts for courses.

Goal:
Build code that creates an inspection bundle automatically from a single run, with strict validation so the bundle is internally consistent and scoped correctly.

What the bundle builder must do:
1. Take a run identifier and optional explicit course_id list as input.
2. Collect only artifacts produced by that run.
3. Build a clean inspection bundle directory with:
   - run_manifest.json
   - validation_report.json
   - inspection_report.md
   - question_ledger_v6_report.md
   - per-course markdown pages
   - final deliverables copied into a subdirectory
4. Fail hard if the bundle is inconsistent.

Core problem to solve:
The current artifacts can drift out of sync:
- manifest may declare one course set
- inspection report may include extra courses
- final JSONL may not match report counts
- unrelated artifacts can leak into the bundle

Your job is to make bundle creation deterministic, scoped, and self-validating.

Required behavior:

A. Bundle inputs
Support a command like:
build-inspection-bundle --run-id <RUN_ID> [--course-id <ID> ...] [--strict]

If course_ids are not provided:
- derive them from the run manifest or run outputs

If course_ids are provided:
- treat them as the authoritative scope
- fail if rendered artifacts include any other course

B. Bundle output structure
Create something like:

inspection_bundle_<RUN_ID>/
  run_manifest.json
  validation_report.json
  inspection_report.md
  question_ledger_v6_report.md
  courses/
    <course_id>_<slug>.md
  final_deliverables/
    all_questions.jsonl
    visible_curated.jsonl
    cache_servable.jsonl
    aliases.jsonl
    anchors_summary.json

If a file does not exist for a run, record that explicitly in validation_report.json.
Do not silently omit expected files.

C. Validation rules
Implement strict validation before finalizing the bundle.

At minimum validate:
1. Scope consistency
   - every per-course page belongs to the declared course set
   - no extra courses appear in the report
   - no extra courses appear in copied deliverables if the bundle is supposed to be scoped

2. Count consistency
   - report totals match the underlying JSONL
   - per-course counts match filtered ledger rows
   - visible curated counts match visible rows
   - cache_servable counts match cache rows
   - hidden counts match non-visible validated rows

3. Run consistency
   - copied artifacts belong to the requested run
   - manifest run id matches bundle run id
   - if artifacts include provenance/run metadata, verify it

4. Coverage consistency
   - if a course has a FAIL or WARN coverage state, surface it clearly in validation_report.json and inspection_report.md
   - strict mode should fail on blocking coverage issues if those are defined as blocking by project rules

5. Required file presence
   - if the bundle expects question_ledger_v6_report.md or all_questions.jsonl and they are missing, fail
   - do not fabricate placeholders for required core artifacts

D. Anchor sanitation checks
Add a validation pass for suspicious anchors and low-quality extracted topics.

Flag anchors that look like:
- website names / domains
- raw URL fragments
- generic overview placeholders
- mechanically inferred junk like "overview-segment-1"
- obviously non-pedagogical headings

Do not automatically delete them unless there is already an existing sanitation layer.
But:
- include them in validation_report.json
- surface them in inspection_report.md under "Suspicious anchors"
- support a strict mode failure threshold if too many occur

E. Rendering requirements
Per-course markdown pages should include:
- visible curated Q/A pairs if available
- hidden but correct questions with reasons
- coverage warnings
- policy summary
- scraped/normalized course description section if available

Top-level inspection_report.md should include:
- run id
- pipeline variant
- declared course scope
- actual rendered course scope
- validation summary
- suspicious anchor summary
- coverage failure summary
- per-course quick stats

F. Implementation guidance
Please implement this as additive code, not a repo rewrite.

Suggested modules:
- bundle_builder.py
- bundle_validate.py
- bundle_render.py
- bundle_schemas.py

Suggested data models:
- BundleManifest
- BundleValidationReport
- CourseBundleSummary
- SuspiciousAnchorRecord
- CountMismatchRecord

G. CLI
Add a CLI entrypoint such as:
build-inspection-bundle

Example:
build-inspection-bundle --run-id 20260418T212725Z --course-id 7630 --course-id 7631 --course-id 24370 --course-id 24372 --strict

H. Important design rules
- The bundle builder is not allowed to guess silently
- The bundle builder must fail loudly on scope drift
- The bundle builder must preserve inspection-oriented redundancy
- The bundle builder must be deterministic and reproducible
- The bundle builder must not depend on manual file copying

I. Acceptance criteria
1. Given a run id and 4 course ids, the bundle contains only those 4 courses.
2. If the report tries to include extra courses, the build fails.
3. If counts in inspection_report.md do not match all_questions.jsonl, the build fails.
4. validation_report.json explains exactly what passed, failed, and why.
5. Suspicious anchors are surfaced explicitly.
6. The final bundle is self-contained and human-reviewable.

J. Nice-to-have
- add a dry-run mode
- emit machine-readable mismatch diagnostics
- support both full-run bundles and scoped sub-bundles from a larger run
- add tests for scope drift, missing files, and count mismatches

Please implement the feature end-to-end, including:
- code
- CLI wiring
- validation logic
- markdown rendering
- tests
- a short README or docstring showing how to run it
