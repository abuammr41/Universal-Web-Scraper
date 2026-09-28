import re


def clean_extracted_data(data):
    if isinstance(data, list):
        return [clean_extracted_data(item) for item in data]

    if not isinstance(data, dict):
        return data

    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            value = re.sub(r"[ \t]+", " ", value)
            value = re.sub(r"\n\s*\n", "\n\n", value).strip()
        cleaned[key] = value

    return cleaned
