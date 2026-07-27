import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clean_data import extract_skills


def test_extract_skills_finds_known_skill():
    description = "We are looking for a Python developer with SQL experience."
    result = extract_skills(description)
    assert "Python" in result
    assert "SQL" in result


def test_extract_skills_avoids_false_positive():
    description = "This candidate has excellent communication skills."
    result = extract_skills(description)
    assert "Excel" not in result


def test_extract_skills_handles_missing_description():
    result = extract_skills(None)
    assert result == []