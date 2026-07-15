# Hackathon Integrated PI-Style Feedback Workflow Design

Date: 2026-07-15
Project name: Hackathon
Target repository: XKfeng111/Hackathon-Extract-raw-materials

## Goal

Turn this repository into the final integrated **Hackathon** project: a single web app where users first upload categorized reference raw materials to build a personalized PI-style prompt bank, then upload a target document and choose a feedback mode to receive strict PI-style critique.

The final project should absorb the useful ideas from three prototype projects:

- `Hackathon-Extract-raw-materials`: raw material extraction, chunking, JSONL generation, prompt-ready records.
- `Professional-Editor-Biomimicry-AI-Bot`: strict PI-style prompt behavior and AI bot response pattern.
- `Hackathon_1`: user-facing Flask upload/feedback UI pattern.

The final demo should run as one Flask app from this repository, not as three separate services.

## User Workflow

### Step 1: Build PI Reference Library

The user uploads reference raw materials into three categories:

1. Research ideas / Meeting minutes
2. Talks / Presentations / Slides
3. Papers / Proposals / Manuscripts

Each category can accept multiple files. Supported formats should include:

- `.pdf`
- `.docx`
- `.pptx`
- `.txt`
- `.md`

For each category, the system extracts text, chunks it into coherent units, creates draft JSONL records, and summarizes those records into one mode-specific prompt.

The output of Step 1 is a prompt bank with three modes:

- `meeting_research_pi`
- `slides_talk_pi`
- `paper_proposal_pi`

### Step 2: Get Feedback

The user uploads the target file they want reviewed. The target file can also be PDF, DOCX, PPTX, TXT, or MD.

The user then selects one of the three modes:

- Meeting / Research PI mode
- Talk / Slides PI mode
- Paper / Proposal PI mode

The system extracts text from the target file, composes a final prompt from the base PI persona, the selected mode prompt, and the target file content, then sends it to the configured model endpoint.

### Step 3: Display PI-Style Response

The response should use a direct PI/advisor style:

```text
PI: <one concise assessment sentence>

Technical corrections needed:
- ...
- ...
- ...

Implementation issues:
- ...
- ...
- ...

Critical questions:
- ...
```

## Page Structure

The existing local Flask app can be expanded into two major panels.

### Panel A: Reference Materials Setup

Suggested page copy:

```text
Step 1: Build PI Reference Library
Upload reference materials that teach the system what this PI cares about.
```

Three upload cards:

1. Research / Meeting Materials
   - Accept meeting minutes, research ideas, experiment plans, notes.
   - Button: `Upload references`
   - Button: `Generate JSONL + Prompt`

2. Talk / Slides Materials
   - Accept talk drafts, presentation slides, figure sets, slide feedback.
   - Button: `Upload references`
   - Button: `Generate JSONL + Prompt`

3. Paper / Proposal Materials
   - Accept manuscripts, paper drafts, proposal drafts, reviewer/PI comments.
   - Button: `Upload references`
   - Button: `Generate JSONL + Prompt`

Prompt bank status should show:

```text
Prompt Bank Status
✓ Meeting / Research mode ready
✓ Talk / Slides mode ready
✓ Paper / Proposal mode ready
```

If a mode has no uploaded reference materials yet, it should show `Default mode` and use a built-in fallback prompt.

### Panel B: Feedback Workspace

Suggested page copy:

```text
Step 2: Get PI-Style Feedback
Upload the document you want reviewed and choose which PI mode to apply.
```

Inputs:

- Target feedback file upload
- Mode selector
- Optional focus text box
- Generate button

Output:

- Filename
- Selected mode
- PI-style response
- Optional metadata such as extracted character count and prompt bank status

## Backend Architecture

Keep the final implementation inside this repository.

```text
raw_materials/
  reader.py          # Extract text from PDF/DOCX/PPTX/TXT/MD
  chunker.py         # Split text into coherent chunks
  jsonl_builder.py   # Build draft JSONL records from chunks
  prompt_builder.py  # Build mode-specific prompt bank entries

pi_feedback/
  prompts.py         # Base PI-style prompt and mode defaults
  composer.py        # Compose final prompt for model call

data/
  prompt_bank.json
  records/
    meeting_research.jsonl
    slides_talk.jsonl
    paper_proposal.jsonl
```

The repository already contains `raw_materials/reader.py`, `chunker.py`, and `jsonl_builder.py`; these should be extended instead of duplicated.

## Data Flow

### Reference Material Flow

```text
Reference upload
  -> DocumentReader
  -> extracted text
  -> Chunker
  -> JSONLBuilder
  -> data/records/<mode>.jsonl
  -> PromptBuilder
  -> data/prompt_bank.json
```

### Target Feedback Flow

```text
Target upload
  -> DocumentReader
  -> selected prompt from data/prompt_bank.json
  -> base PI-style prompt
  -> PIStylePromptComposer
  -> call_model()
  -> response shown in browser
```

## Prompt Bank Format

`data/prompt_bank.json` should contain one entry per mode.

Example:

```json
{
  "meeting_research_pi": {
    "label": "Meeting / Research PI",
    "source_type": "research_ideas_meeting_minutes",
    "status": "ready",
    "system_addon_prompt": "When reviewing research ideas or meeting minutes, focus on research logic, feasibility, next experiments, missing controls, and decision clarity.",
    "reference_patterns": [
      "Clarify the decision before adding more experiments.",
      "Do not claim mechanism without control data."
    ],
    "record_count": 12
  }
}
```

If no references exist for a mode, `status` can be `default`, and the app should use the built-in default mode prompt.

## JSONL Record Format

Each record should preserve the raw extracted context and draft structured PI signals.

Example:

```json
{
  "id": "meeting_research_001",
  "mode": "meeting_research_pi",
  "source_file": "meeting_minutes.pdf",
  "source_type": "research_ideas_meeting_minutes",
  "context": "Extracted chunk text...",
  "key_points": ["unclear next experiment", "missing control"],
  "pi_style_patterns": ["Define the next experiment before expanding the claim."],
  "action_items": ["Add a control comparison."],
  "metadata": {
    "verified_by_human": false,
    "confidence": "draft"
  }
}
```

These JSONL records are prompt-ready draft data. They are not treated as final verified fine-tuning data unless a human reviews them.

## Base PI-Style Prompt

The system should use a base persona inspired by the PI-style behavior from `Professional-Editor-Biomimicry-AI-Bot`:

```text
You are a strict PI-style reviewer. Give direct, concise, critical, and specific feedback.
Use short sentences and concrete edits. Prefer commands such as change, remove, add, move, show, clarify, and do not show.
Focus on clarity, evidence quality, plausibility, structure, technical consistency, and actionable next steps.
Do not sound generic or overly polite. Do not give broad encouragement before identifying the core problem.
```

Then append the selected mode prompt.

## Mode-Specific Prompt Defaults

### meeting_research_pi

Focus on:

- research question clarity
- hypothesis and logic
- next experiment
- missing controls
- feasibility
- whether a decision was actually made

### slides_talk_pi

Focus on:

- slide layout
- visual hierarchy
- title/takeaway alignment
- duplicate panels
- figure clarity
- storyline
- whether each slide supports one message

### paper_proposal_pi

Focus on:

- claim strength
- evidence quality
- novelty
- logic gaps
- overclaiming
- mechanism support
- citation or comparison needs

## Final Prompt Composition

The final prompt sent to the model should have this shape:

```text
<Base PI-style prompt>

<Selected mode prompt from prompt bank or default>

Reference patterns extracted from uploaded raw materials:
- ...
- ...

User requested focus:
<optional focus or "Provide comprehensive PI-style feedback.">

Target file name:
<filename>

Target file content:
<extracted target text>

Return the response in this structure:
PI: <one concise assessment sentence>

Technical corrections needed:
- <bullet>
- <bullet>
- <bullet>

Implementation issues:
- <bullet>
- <bullet>
- <bullet>

Critical questions:
- <bullet>
- <bullet>
```

## Error Handling

- Unsupported file type: show a clear allowed-formats message.
- Empty extracted text: tell the user the file could not be read and suggest uploading a text-based PDF or DOCX.
- Missing prompt bank: use default prompt for the selected mode and show a small warning.
- Model unavailable: preserve demo-mode behavior.
- Very long extracted text: truncate or summarize before calling the model, and show that truncation occurred.

## Testing Plan

Unit tests:

- reader extracts text from TXT, DOCX, PDF, and PPTX fixtures.
- chunker returns non-empty chunks for representative text.
- JSONL builder creates valid JSON lines with mode metadata.
- prompt builder creates all three prompt bank entries.
- composer includes base prompt, mode prompt, target content, and output format.

Route tests:

- reference upload creates JSONL and updates prompt bank.
- feedback upload works with selected mode.
- unsupported file types return a clear error.
- demo mode still returns a response when `MODEL_API_URL` is not configured.

## MVP Scope

In scope for first implementation:

- Single Flask app in this repository
- Reference upload for the three modes
- JSONL generation and prompt bank generation
- Target file upload
- Mode selection
- PI-style response generation through existing model bridge or demo response
- PDF/DOCX/PPTX/TXT/MD reading

Out of scope for first implementation:

- Real fine-tuning
- Multi-user authentication
- Database storage
- Cloud deployment
- Human verification UI for editing every JSONL record
- Running A/B/C as separate services

## Success Criteria

The demo is successful when a user can:

1. Open the Hackathon website.
2. Upload at least one reference material into each of the three categories.
3. Generate a prompt bank and JSONL files.
4. Upload a target file for feedback.
5. Select one of the three modes.
6. Receive a PI-style response that reflects the selected mode.
