# Raw Materials to JSONL Flask Demo Design

## Goal

Build a standalone, runnable Flask demo inside `Hackathon-Extract-raw-materials` that lets a user upload raw research materials, generate draft structured JSONL records, preview those records directly in the browser, and download the generated outputs for human review.

## Scope

### In scope

- A local Flask web app.
- Upload one raw material file per generation run.
- Supported input formats:
  - `.pdf`
  - `.docx`
  - `.txt`
  - `.md`
- Required metadata:
  - `project_name`
  - `source_type`
- Source type is selected from exactly three choices:
  - `Papers_Proposal`
  - `Research_Meeting_Minutes`
  - `Talk_Presentation_Slides`
- `mentor_mode` is auto-filled from `source_type`, with an advanced override field if needed.
- Optional `source_date`.
- Rule-based text extraction, chunking, and draft JSONL generation.
- Browser preview of generated records before download.
- Download links for:
  - `.jsonl`
  - pretty `.json`
  - preview `.md`
- Every generated record is marked as a draft requiring human review.

### Out of scope for first version

- No OpenAI/API-based extraction.
- No user accounts.
- No database.
- No multi-file batch upload.
- No editing records inside the browser before download.
- No deployment work beyond local run instructions.

## User Flow

1. User starts the app with `python app.py`.
2. User opens the local URL in a browser.
3. User uploads a raw material file.
4. User selects one of the three source types:
   - `Papers_Proposal`
   - `Research_Meeting_Minutes`
   - `Talk_Presentation_Slides`
5. User enters `project_name`.
6. Optional: user enters `source_date` or changes the advanced `mentor_mode`.
7. User clicks `Generate JSONL`.
8. Flask extracts text from the uploaded file.
9. The extractor chunks the text into draft feedback/training units.
10. The builder creates structured JSONL records.
11. The page renders an inline preview:
    - record count
    - record id
    - source file
    - main concern
    - action items
    - draft/human-review status
12. User downloads JSONL, pretty JSON, or preview Markdown.

## Architecture

```text
Flask app
  ├─ routes
  │   ├─ GET /                    -> upload form and preview page
  │   ├─ POST /generate           -> process upload and render preview
  │   └─ GET /download/<run>/<kind> -> download jsonl/json/md output
  ├─ raw_materials.reader         -> extract text from pdf/docx/txt/md
  ├─ raw_materials.chunker        -> split text into coherent chunks
  ├─ raw_materials.jsonl_builder  -> build structured draft records
  └─ outputs/                     -> generated files for download
```

## Components

### `app.py`

Responsibilities:

- Configure Flask.
- Validate upload size and extension.
- Validate `source_type`.
- Map selected `source_type` to default `mentor_mode`.
- Call extraction/chunking/building modules.
- Save generated files under `outputs/<run_id>/`.
- Render preview in `templates/index.html`.
- Serve generated downloads.

### `raw_materials/reader.py`

Responsibilities:

- Read file bytes.
- Extract plain text from supported formats.
- Normalize whitespace.
- Raise clear errors for unsupported or unreadable files.

Dependencies:

- `python-docx` for `.docx`.
- `pypdf` for `.pdf`.
- Python standard library for `.txt` and `.md`.

### `raw_materials/chunker.py`

Responsibilities:

- Split extracted text into draft record chunks.
- Prefer structured feedback boundaries when available:
  - `Feedback 1:`
  - numbered lists such as `1.`
  - headings
- Fall back to paragraph grouping with a maximum character budget.

### `raw_materials/jsonl_builder.py`

Responsibilities:

- Build one structured JSONL record per chunk.
- Create stable-ish readable IDs from project name, source type, file stem, and chunk index.
- Infer draft `main_concern` and `action_items` using lightweight rules.
- Mark records as unverified drafts.

## Data Model

Each JSONL line is one object:

```json
{
  "id": "project_source_file_001",
  "project_name": "Example Project",
  "source_type": "Research_Meeting_Minutes",
  "source_date": "2026-07-15",
  "source_file": "meeting_notes.pdf",
  "mentor_mode": "research_problem_feedback",
  "training_input": {
    "context": "Extracted raw material chunk...",
    "task": "Generate mentor-style feedback, critique questions, and concrete action items from this raw material."
  },
  "training_output": {
    "main_concern": "Draft concern inferred from this chunk...",
    "advisor_questions": [],
    "critique_points": [],
    "missing_or_weak_elements": [],
    "action_items": [],
    "ideal_response": "Draft mentor response..."
  },
  "tags": ["Research_Meeting_Minutes", "draft", "needs_review"],
  "persona_patterns": [],
  "metadata": {
    "source_section": "file.pdf / chunk 1",
    "needs_anonymization": true,
    "verified_by_human": false,
    "confidence": "draft"
  }
}
```

## Source Type Mapping

```text
Papers_Proposal          -> research_problem_feedback
Research_Meeting_Minutes -> research_problem_feedback
Talk_Presentation_Slides -> presentation_feedback
```

The UI shows these as three selectable cards or radio options. The underlying submitted value is exact and stable.

## Error Handling

- Missing file: show inline error.
- Unsupported extension: show inline error listing supported formats.
- Empty extracted text: show inline error explaining the file may be scanned or unreadable.
- Missing `project_name`: show inline error.
- Unknown `source_type`: show inline error and do not process.
- Too-large upload: return a friendly page error.

## Testing

Initial tests:

- Home page loads.
- Home page shows the three source type choices.
- TXT upload generates records.
- DOCX upload generates records.
- Unsupported file extension is rejected.
- Missing project name is rejected.
- Generated records have `verified_by_human: false`.
- JSONL download endpoint returns newline-delimited JSON.

## Human Review Principle

The system does not claim final training-data quality. It creates draft records only. The browser preview and generated Markdown preview are part of the human-review workflow, and every record explicitly carries draft metadata.
