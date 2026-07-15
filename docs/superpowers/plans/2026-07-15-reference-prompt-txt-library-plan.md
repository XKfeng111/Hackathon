# Reference Prompt TXT Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Step 1 UI and backend flow that uploads three categories of reference materials, extracts text from PDF/DOCX/PPTX/TXT/MD, generates three mode-specific PI-style prompt TXT files, and exposes them for preview/download.

**Architecture:** Extend the existing Flask app in place. Reuse `raw_materials.reader` and `chunker`; add a focused `raw_materials.prompt_builder` for prompt synthesis and TXT serialization. Keep the existing JSONL generator route intact as the Step 2/legacy workflow.

**Tech Stack:** Flask, python-docx, pypdf, python-pptx, pytest.

---

## Files

- Modify: `requirements.txt` — add `python-pptx`.
- Modify: `raw_materials/reader.py` — support `.pptx` extraction.
- Create: `raw_materials/prompt_builder.py` — mode definitions, keyword/pattern extraction, prompt text generation.
- Modify: `app.py` — add `/generate-prompts` and prompt TXT downloads.
- Modify: `templates/index.html` — add Step 1 reference materials prompt-library panel above existing upload panel.
- Modify: `static/style.css` — style new panels/cards/downloads.
- Modify: `tests/test_reader_builder.py` — failing tests for PPTX and prompt builder.
- Modify: `tests/test_app.py` — failing route/UI tests.

## Task 1: PPTX reader support

- [ ] Write tests: `is_supported_filename("slides.pptx")` is true and a generated PPTX extracts slide text.
- [ ] Run tests and verify they fail because `.pptx` is unsupported.
- [ ] Add `python-pptx` to requirements and implement `extract_pptx()` in `raw_materials.reader`.
- [ ] Run targeted tests and verify they pass.

## Task 2: Prompt TXT builder

- [ ] Write tests for `build_mode_prompt_artifacts()` that pass sample categorized chunks and assert three `.txt` prompt artifacts are produced with mode names and PI-style language.
- [ ] Run tests and verify they fail because `prompt_builder` does not exist.
- [ ] Implement `raw_materials.prompt_builder` with deterministic keyword, key-sentence, reference-pattern, and prompt generation logic.
- [ ] Run targeted tests and verify they pass.

## Task 3: Flask route for Step 1

- [ ] Write route test posting `research_files`, `slide_files`, and `paper_files` to `/generate-prompts` and assert response includes ready prompt text and download links.
- [ ] Run tests and verify they fail because route does not exist.
- [ ] Implement route, save outputs under `outputs/<run_id>/prompts/`, and add TXT download support.
- [ ] Run targeted route tests and verify they pass.

## Task 4: UI integration

- [ ] Write home-page test asserting `Build Your PI Style Library`, three upload categories, and `Generate PI-Style Prompts` appear.
- [ ] Run test and verify it fails until template is updated.
- [ ] Update `templates/index.html` and `static/style.css` with Step 1 panel above existing Step 2 upload.
- [ ] Run app tests and verify they pass.

## Task 5: Full verification and commit

- [ ] Run the full pytest suite.
- [ ] Import Flask app and inspect routes.
- [ ] Commit changes with a descriptive message.
- [ ] Push to `origin/main` if requested/appropriate.
