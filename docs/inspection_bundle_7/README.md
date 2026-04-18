# Inspection Bundle 7

This bundle is the current bounded inspection publication for the canonical
question pipeline on course `24491`.

Source runs:

- candidate run: `20260418T182853Z`
- ledger run: `20260418T182901Z`

Pipeline path:

`raw YAML -> normalized course -> candidate generation -> policy -> ledger -> inspection bundle`

Included files:

- `24491_forecasting-in-r.md`
- `inspection_report.md`
- `question_ledger_v6_report.md`
- `run_manifest.json`
- `entry_definition_fix_note.md`
- `final_deliverables/all_questions.jsonl`

Convention going forward:

- each inspection bundle should include `final_deliverables/`
- the authoritative final ledger export `all_questions.jsonl` should be copied there

Source run directories:

- `data/pipeline_runs/20260418T182853Z`
- `data/pipeline_runs/20260418T182901Z`
