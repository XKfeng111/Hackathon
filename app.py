from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from flask import Flask, Response, abort, render_template, request, send_file
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from raw_materials.chunker import chunk_text
from raw_materials.jsonl_builder import (
    SOURCE_TYPE_TO_MENTOR_MODE,
    build_records,
    default_mentor_mode,
    records_to_jsonl,
    records_to_preview_markdown,
    records_to_pretty_json,
    slugify,
)
from raw_materials.prompt_builder import (
    MODE_DEFINITIONS,
    PromptArtifact,
    build_combined_prompt_text,
    build_mode_prompt_artifacts,
)
from raw_materials.reader import SUPPORTED_EXTENSIONS, extract_text_from_upload, is_supported_filename


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["OUTPUT_DIR"] = Path(__file__).parent / "outputs"

DOWNLOAD_FILENAMES = {
    "jsonl": "records.jsonl",
    "json": "records_pretty.json",
    "md": "preview.md",
}

REFERENCE_UPLOAD_GROUPS = {
    "meeting_research_pi": {
        "field": "research_files",
        "label": "Research Ideas / Meeting Minutes",
        "description": "Meeting notes, research ideas, experiment plans, and lab discussion records.",
    },
    "slides_talk_pi": {
        "field": "slide_files",
        "label": "Talks / Presentations / Slides",
        "description": "Talk drafts, presentation slides, figure sets, and slide feedback.",
    },
    "paper_proposal_pi": {
        "field": "paper_files",
        "label": "Papers / Proposals",
        "description": "Manuscripts, proposals, paper drafts, reviewer comments, and cover letters.",
    },
}


def get_output_dir() -> Path:
    return Path(app.config["OUTPUT_DIR"])


def render_home(**context: Any):
    defaults = {
        "error": "",
        "records": [],
        "record_count": 0,
        "run_id": "",
        "download_urls": {},
        "prompt_artifacts": [],
        "prompt_run_id": "",
        "prompt_download_urls": {},
        "prompt_message": "",
        "reference_form": {"project_name": ""},
        "form": {
            "project_name": "",
            "source_type": "Research_Meeting_Minutes",
            "source_date": "",
            "mentor_mode": "",
        },
    }
    defaults.update(context)
    return render_template(
        "index.html",
        source_types=SOURCE_TYPE_TO_MENTOR_MODE,
        supported_extensions=", ".join(sorted(SUPPORTED_EXTENSIONS)),
        reference_upload_groups=REFERENCE_UPLOAD_GROUPS,
        mode_definitions=MODE_DEFINITIONS,
        **defaults,
    )


@app.get("/")
def home():
    return render_home()


@app.post("/generate-prompts")
def generate_prompts():
    reference_form = {"project_name": request.form.get("project_name", "").strip()}
    if not reference_form["project_name"]:
        return render_home(
            error="Project name is required to generate PI-style prompts.",
            reference_form=reference_form,
        ), 400

    try:
        grouped_chunks = build_grouped_reference_chunks()
    except ValueError as exc:
        return render_home(error=str(exc), reference_form=reference_form), 400

    if not any(grouped_chunks[mode] for mode in grouped_chunks):
        return render_home(
            error="Please upload at least one reference material file.",
            reference_form=reference_form,
        ), 400

    artifacts = build_mode_prompt_artifacts(grouped_chunks)
    run_id = save_prompt_outputs(artifacts, reference_form["project_name"])
    prompt_download_urls = {
        mode: f"/download/{run_id}/{mode}_prompt" for mode in MODE_DEFINITIONS
    }
    prompt_download_urls["all"] = f"/download/{run_id}/all_pi_style_prompts"

    response = Response(
        render_home(
            prompt_artifacts=[artifacts[mode] for mode in MODE_DEFINITIONS],
            prompt_run_id=run_id,
            prompt_download_urls=prompt_download_urls,
            prompt_message="PI Style Prompts Ready",
            reference_form=reference_form,
        )
    )
    response.headers["X-Prompt-Run-Id"] = run_id
    return response


def build_grouped_reference_chunks() -> dict[str, list[dict]]:
    grouped_chunks: dict[str, list[dict]] = {mode: [] for mode in MODE_DEFINITIONS}
    for mode, config in REFERENCE_UPLOAD_GROUPS.items():
        files = [file for file in request.files.getlist(config["field"]) if file and file.filename]
        for uploaded_file in files:
            filename = safe_uploaded_filename(uploaded_file)
            if not is_supported_filename(filename):
                raise ValueError(
                    f"Unsupported file type for {config['label']}: {filename}. "
                    f"Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
                )
            text = extract_text_from_upload(uploaded_file.read(), filename)
            chunks = chunk_text(text, mode)
            if not chunks:
                raise ValueError(f"No usable chunks were generated from {filename}.")
            grouped_chunks[mode].append({"source_file": filename, "chunks": chunks})
    return grouped_chunks


def safe_uploaded_filename(uploaded_file: FileStorage) -> str:
    original = uploaded_file.filename or "uploaded.txt"
    filename = secure_filename(original)
    return filename or Path(original).name


@app.post("/generate")
def generate():
    form = {
        "project_name": request.form.get("project_name", "").strip(),
        "source_type": request.form.get("source_type", "").strip(),
        "source_date": request.form.get("source_date", "").strip(),
        "mentor_mode": request.form.get("mentor_mode", "").strip(),
    }
    uploaded_file = request.files.get("file")

    if not form["project_name"]:
        return render_home(error="Project name is required.", form=form), 400

    if form["source_type"] not in SOURCE_TYPE_TO_MENTOR_MODE:
        return render_home(error="Choose one of the three source types.", form=form), 400

    if not form["mentor_mode"]:
        form["mentor_mode"] = default_mentor_mode(form["source_type"])

    if not uploaded_file or not uploaded_file.filename:
        return render_home(error="Please choose a raw material file.", form=form), 400

    filename = safe_uploaded_filename(uploaded_file)
    if not is_supported_filename(filename):
        return render_home(
            error=f"Unsupported file type. Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.",
            form=form,
        ), 400

    try:
        file_bytes = uploaded_file.read()
        text = extract_text_from_upload(file_bytes, filename)
        chunks = chunk_text(text, form["source_type"])
        if not chunks:
            raise ValueError("No usable chunks were generated from this file.")
        records = build_records(
            chunks=chunks,
            project_name=form["project_name"],
            source_type=form["source_type"],
            source_date=form["source_date"],
            source_file=filename,
            mentor_mode=form["mentor_mode"],
        )
    except ValueError as exc:
        return render_home(error=str(exc), form=form), 400

    run_id = save_outputs(records, form["project_name"], form["source_type"])
    response = Response(
        render_home(
            records=records,
            record_count=len(records),
            run_id=run_id,
            download_urls={
                "jsonl": f"/download/{run_id}/jsonl",
                "json": f"/download/{run_id}/json",
                "md": f"/download/{run_id}/md",
            },
            form=form,
        )
    )
    response.headers["X-Run-Id"] = run_id
    return response


def save_outputs(records: list[dict], project_name: str, source_type: str) -> str:
    run_id = f"{slugify(project_name, 4)}_{slugify(source_type, 4)}_{secrets.token_hex(4)}"
    run_dir = get_output_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / DOWNLOAD_FILENAMES["jsonl"]).write_text(records_to_jsonl(records), encoding="utf-8")
    (run_dir / DOWNLOAD_FILENAMES["json"]).write_text(records_to_pretty_json(records), encoding="utf-8")
    (run_dir / DOWNLOAD_FILENAMES["md"]).write_text(records_to_preview_markdown(records), encoding="utf-8")
    return run_id


def save_prompt_outputs(artifacts: dict[str, PromptArtifact], project_name: str) -> str:
    run_id = f"{slugify(project_name, 4)}_pi_prompts_{secrets.token_hex(4)}"
    run_dir = get_output_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    for artifact in artifacts.values():
        (run_dir / artifact.filename).write_text(artifact.content, encoding="utf-8")
    (run_dir / "all_pi_style_prompts.txt").write_text(
        build_combined_prompt_text(artifacts),
        encoding="utf-8",
    )
    return run_id


@app.get("/download/<run_id>/<kind>")
def download(run_id: str, kind: str):
    safe_run_id = secure_filename(run_id)
    if safe_run_id != run_id:
        abort(404)

    path = path_for_download(run_id, kind)
    if path is None or not path.exists():
        abort(404)

    mimetypes = {
        "jsonl": "application/jsonl; charset=utf-8",
        "json": "application/json; charset=utf-8",
        "md": "text/markdown; charset=utf-8",
    }
    mimetype = "text/plain; charset=utf-8" if path.suffix == ".txt" else mimetypes[kind]
    return send_file(
        path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=path.name,
    )


def path_for_download(run_id: str, kind: str) -> Path | None:
    run_dir = get_output_dir() / run_id
    if kind in DOWNLOAD_FILENAMES:
        return run_dir / DOWNLOAD_FILENAMES[kind]
    if kind == "all_pi_style_prompts":
        return run_dir / "all_pi_style_prompts.txt"
    if kind.endswith("_prompt"):
        candidate = run_dir / f"{kind}.txt"
        if candidate.name in {f"{mode}_prompt.txt" for mode in MODE_DEFINITIONS}:
            return candidate
    return None


@app.errorhandler(413)
def file_too_large(_error: Exception):
    return render_home(error="The file is too large. Maximum upload size is 20 MB."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
