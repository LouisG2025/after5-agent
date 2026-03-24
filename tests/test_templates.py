import pytest
from app.templates import OUTREACH_TEMPLATES, FOLLOW_UP_TEMPLATE

def test_outreach_templates_format():
    name = "John"
    company = "ACME Corp"
    for template in OUTREACH_TEMPLATES:
        formatted = template.format(name=name, company_name=company)
        assert name in formatted
        assert company in formatted
        assert "After5" in formatted

def test_follow_up_template_format():
    name = "John"
    formatted = FOLLOW_UP_TEMPLATE.format(name=name)
    assert name in formatted
    assert "following up" in formatted
