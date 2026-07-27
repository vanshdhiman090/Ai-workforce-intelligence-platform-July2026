def compute_missing_skills(market_skills, company_skills):
    return sorted(list(set(market_skills) - set(company_skills)))


def test_missing_skills_basic_case():
    market = ["Python", "SQL", "AWS", "Excel"]
    company = ["Python", "SQL"]
    result = compute_missing_skills(market, company)
    assert result == ["AWS", "Excel"]


def test_missing_skills_full_coverage():
    market = ["Python", "SQL"]
    company = ["Python", "SQL", "AWS"]
    result = compute_missing_skills(market, company)
    assert result == []


def test_missing_skills_empty_company():
    market = ["Python", "SQL"]
    company = []
    result = compute_missing_skills(market, company)
    assert result == ["Python", "SQL"]