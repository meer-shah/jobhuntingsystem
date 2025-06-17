# utils.py
def clean_unicode(text: str) -> str:
    replacements = {
        '\\u2013': '-',
        '\\u2014': '-',
        '\\u2018': "'",
        '\\u2019': "'",
        '\\u201c': '"',
        '\\u201d': '"',
        '\\u2026': '...',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text