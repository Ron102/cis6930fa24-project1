import pytest
import spacy
import en_core_web_md
from redactor import redact_content

nlp = en_core_web_md.load()

@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("job", "█" * 3)
    ],
)
def test_all(input_text, expected):
    redacted_content, stats_output = redact_content(input_text, nlp, labels, concepts=['occupation'])
    assert redacted_content == expected

labels = {
    "NORP": "Nationalities or Religious or Political Groups",
    "GPE": "Geopolitical Entities",
    "FAC": "Facilities",
    "ORG": "Organizations",
    "PERSON": "Persons",
    "LOC": "Locations",
    "PRODUCT": "Products",
    "EVENT": "Events",
    "WORK_OF_ART": "Art Works",
    "LAW": "Laws",
    "LANGUAGE": "Languages",
    "DATE": "Dates",
    "TIME": "Times",
    "PERCENT": "Percentages",
    "MONEY": "Monetary Values",
    "QUANTITY": "Quantities",
    "ORDINAL": "Ordinal Numbers",
    "CARDINAL": "Cardinal Numbers",
    "PHONE": "Phone Numbers",
    "EMAIL": "Email IDs",
}
