import json
import subprocess
from pathlib import Path

CONFIG_PATH = "/app/config.json"
OUTPUT_PATH = "/app/output.txt"
SCRIPT_PATH = "/app/processor.py"

def get_expected():
    with open(CONFIG_PATH) as f:
        c = json.load(f)
    return c["workers"] * c["increments"]

def run_script():
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True, text=True
    )
    return result

def test_output_file_exists():
    assert Path(OUTPUT_PATH).exists(), "output.txt was not created"

def test_output_is_integer():
    content = Path(OUTPUT_PATH).read_text().strip()
    assert content.isdigit(), f"Output is not an integer: {content}"

def test_output_correct_default_config():
    content = Path(OUTPUT_PATH).read_text().strip()
    assert int(content) == get_expected(), f"Expected {get_expected()}, got {content}"

def test_output_correct_config_b():
    with open(CONFIG_PATH, "w") as f:
        json.dump({"workers": 5, "increments": 200}, f)
    run_script()
    content = Path(OUTPUT_PATH).read_text().strip()
    assert int(content) == 1000, f"Expected 1000, got {content}"

def test_output_correct_config_c():
    with open(CONFIG_PATH, "w") as f:
        json.dump({"workers": 20, "increments": 50}, f)
    run_script()
    content = Path(OUTPUT_PATH).read_text().strip()
    assert int(content) == 1000, f"Expected 1000, got {content}"

def test_deterministic():
    with open(CONFIG_PATH, "w") as f:
        json.dump({"workers": 10, "increments": 100}, f)
    results = set()
    for _ in range(3):
        run_script()
        results.add(Path(OUTPUT_PATH).read_text().strip())
    assert len(results) == 1, f"Non-deterministic output: {results}"

def test_no_traceback():
    result = run_script()
    assert "Traceback" not in result.stderr, f"Script has errors: {result.stderr}"
