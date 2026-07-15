import json
from io import BytesIO

from app import app


def client_with_tmp_outputs(tmp_path):
    app.config.update(TESTING=True, OUTPUT_DIR=tmp_path)
    return app.test_client()


def test_home_page_shows_exact_three_source_type_choices(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Papers_Proposal" in html
    assert "Research_Meeting_Minutes" in html
    assert "Talk_Presentation_Slides" in html
    assert "Generate JSONL" in html


def test_txt_upload_generates_inline_preview_and_download_links(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.post(
        "/generate",
        data={
            "project_name": "WVTR",
            "source_type": "Research_Meeting_Minutes",
            "source_date": "2026-07-15",
            "file": (
                BytesIO(b"1. Add stronger evidence.\n2. Clarify the next experiment."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Generated 2 draft records" in html
    assert "verified_by_human" in html
    assert "Download JSONL" in html
    assert "Download pretty JSON" in html
    assert "Download preview MD" in html


def test_download_jsonl_returns_newline_delimited_json(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    generate_response = client.post(
        "/generate",
        data={
            "project_name": "Talk Demo",
            "source_type": "Talk_Presentation_Slides",
            "file": (BytesIO(b"1. Revise the opening slide title."), "talk.md"),
        },
        content_type="multipart/form-data",
    )
    assert generate_response.status_code == 200
    run_id = generate_response.headers["X-Run-Id"]

    download_response = client.get(f"/download/{run_id}/jsonl")
    assert download_response.status_code == 200
    assert download_response.headers["Content-Type"].startswith("application/jsonl")
    line = download_response.data.decode("utf-8").strip()
    payload = json.loads(line)
    assert payload["project_name"] == "Talk Demo"
    assert payload["source_type"] == "Talk_Presentation_Slides"


def test_generate_rejects_invalid_source_type(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.post(
        "/generate",
        data={
            "project_name": "WVTR",
            "source_type": "Unknown_Type",
            "file": (BytesIO(b"Example content"), "notes.txt"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"Choose one of the three source types" in response.data


def test_generate_rejects_unsupported_extension(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.post(
        "/generate",
        data={
            "project_name": "WVTR",
            "source_type": "Papers_Proposal",
            "file": (BytesIO(b"a,b,c"), "table.csv"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"Unsupported file type" in response.data


def test_generate_requires_project_name(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.post(
        "/generate",
        data={
            "project_name": "",
            "source_type": "Papers_Proposal",
            "file": (BytesIO(b"Example content"), "proposal.txt"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"Project name is required" in response.data

def test_home_page_shows_reference_prompt_library_panel(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Build Your PI Style Library" in html
    assert "Research Ideas / Meeting Minutes" in html
    assert "Talks / Presentations / Slides" in html
    assert "Papers / Proposals" in html
    assert "Generate PI-Style Prompts" in html


def test_generate_prompts_creates_three_txt_prompt_downloads(tmp_path):
    client = client_with_tmp_outputs(tmp_path)
    response = client.post(
        "/generate-prompts",
        data={
            "project_name": "WVTR",
            "research_files": (
                BytesIO(b"Clarify the next experiment and add a missing control."),
                "meeting.txt",
            ),
            "slide_files": (
                BytesIO(b"Remove duplicate panels and state the slide takeaway."),
                "slides.txt",
            ),
            "paper_files": (
                BytesIO(b"The claim is too broad for the current evidence."),
                "proposal.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "PI Style Prompts Ready" in html
    assert "meeting_research_pi_prompt.txt" in html
    assert "slides_talk_pi_prompt.txt" in html
    assert "paper_proposal_pi_prompt.txt" in html
    run_id = response.headers["X-Prompt-Run-Id"]

    download_response = client.get(f"/download/{run_id}/meeting_research_pi_prompt")
    assert download_response.status_code == 200
    assert download_response.headers["Content-Type"].startswith("text/plain")
    body = download_response.data.decode("utf-8")
    assert "MODE: meeting_research_pi" in body
    assert "Clarify the next experiment" in body

