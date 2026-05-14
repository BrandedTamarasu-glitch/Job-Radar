from pathlib import Path

from job_radar.demo_report import demo_jobs, demo_profile, generate_demo_report


def test_demo_report_uses_realistic_sample_data():
    profile = demo_profile()
    jobs = demo_jobs()

    assert profile["target_titles"]
    assert profile["core_skills"]
    assert len(jobs) == 3
    assert {job.source for job in jobs} == {"Demo"}


def test_generate_demo_report_creates_html_and_markdown(tmp_path):
    result = generate_demo_report(output_dir=str(tmp_path), min_score=2.8)

    assert result["stats"]["total"] >= 1
    assert Path(result["html"]).exists()
    assert Path(result["markdown"]).exists()
