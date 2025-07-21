import re

def extract_entities(text):
    dates = re.findall(r'\b(?:\d{1,2}[\-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,-]*\d{2,4}', text, flags=re.I)
    dollars = re.findall(r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?', text)
    percentages = re.findall(r'\d+(?:\.\d+)?\s?%', text)
    return {
        "dates": list(set(dates)),
        "dollar_amounts": list(set(dollars)),
        "percentages": list(set(percentages))
    }
