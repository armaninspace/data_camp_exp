# Entry Definition Fix Note

This pass implements the protected beginner-definition rules for foundational
anchors.

## Policy changes validated here

- every foundational anchor emits a plain canonical beginner definition
- acronym anchors prefer `What is X?`
- acronym-expansion questions may still exist, but only as secondary items
- required entry definitions are protected from low-distinctiveness demotion
- strict mode fails if a foundational anchor lacks a visible canonical plain
  definition

## Verified on `24491`

Visible beginner definitions now exist for:

- `What is ARIMA?`
- `What is exponential smoothing?`
- `What is the Ljung-Box test?`
- `What is trend?`
- `What is seasonality?`

The companion question `What does ARIMA stand for?` still exists, but it no
longer replaces the plain beginner definition.
