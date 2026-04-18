# Prefect Pipeline Bundle

This bundle introduces a Prefect-oriented orchestration package at
`src/course_pipeline/prefect_pipeline/`.

Phase 1 scope:

- typed run config and run context
- stable run directory creation
- run manifest generation
- top-level Prefect flow skeleton
- developer script entry point

The domain logic remains in the existing V3, V4.1, and V6 modules and will be
wired in the next slice.
