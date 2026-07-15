# Hackathon

A local Flask demo for building a PI-style feedback workflow from raw research materials, draft JSONL records, and mode-specific prompts.

The workflow is intentionally semi-automatic:

1. Upload a raw material file.
2. Choose one of three source types.
3. Generate draft JSONL records.
4. Preview the records directly in the browser.
5. Download JSONL / pretty JSON / Markdown preview.
6. Human-check the records before using them for training.

Every generated record is marked:

```json
{
  "verified_by_human": false,
  "confidence": "draft"
}
```

## Supported raw material files

- `.pdf`
- `.docx`
- `.txt`
- `.md`

## Source type choices

The web demo uses exactly three source types:

- `Papers_Proposal`
- `Research_Meeting_Minutes`
- `Talk_Presentation_Slides`

Default mentor-mode mapping:

```text
Papers_Proposal          -> research_problem_feedback
Research_Meeting_Minutes -> research_problem_feedback
Talk_Presentation_Slides -> presentation_feedback
```

## Run locally on Windows

From PowerShell:

```powershell
git clone https://github.com/XKfeng111/Hackathon-Extract-raw-materials.git
cd Hackathon-Extract-raw-materials

py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Then open:

```text
http://127.0.0.1:5000
```

If `py` is not available, install Python 3.11+ from <https://www.python.org/downloads/> and check **Add Python to PATH** during installation.

## How to use the demo

1. Open the local web app.
2. Choose a raw material file.
3. Enter `project_name`, for example `WVTR`.
4. Choose source type:
   - `Papers_Proposal`
   - `Research_Meeting_Minutes`
   - `Talk_Presentation_Slides`
5. Optionally enter `source_date`.
6. Leave `mentor_mode` blank unless you need an advanced override.
7. Click **Generate JSONL**.
8. Review the generated preview in the browser.
9. Download:
   - **Download JSONL**
   - **Download pretty JSON**
   - **Download preview MD**

Generated files are saved under:

```text
outputs/<run_id>/
```

The `outputs/` directory is ignored by git except for `outputs/.gitkeep`.

## Development

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Project structure

```text
app.py                         Flask web app and download routes
raw_materials/reader.py        Extract text from PDF/DOCX/TXT/MD
raw_materials/chunker.py       Split extracted text into draft chunks
raw_materials/jsonl_builder.py Build structured JSONL records
templates/index.html           Upload form and inline preview
static/style.css               Demo styling
tests/                         Unit and route tests
outputs/                       Generated local outputs
```

## Important note

This project does **not** produce final verified training data automatically.

It creates a clean draft that is easier for a human to review, edit, and approve.

## Contributors and acknowledgements

- Xianke Feng 鈥?project owner and dataset workflow design.
- ChatGPT 鈥?AI coding assistant for planning, implementation, testing, and documentation support.

Note: GitHub's automatic contributor list is generated from commit authors. This acknowledgement records ChatGPT's assistance in the project documentation.

