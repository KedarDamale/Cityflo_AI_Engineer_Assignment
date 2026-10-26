"""Student lookup rules; independent of MCP and persistence infrastructure."""

from rapidfuzz import fuzz, process


data = {
    "kedar": 96.20,
    "kanchan": 89.60,
    "pravin": 60.00,
    "ananya": 98.40,
    "rohit": 85.50,
    "sneha": 91.20,
    "amit": 72.80,
    "priya": 94.00,
    "rahul": 55.40,
    "neha": 88.15,
    "vikram": 79.60,
    "pooja": 92.80,
    "siddharth": 68.40,
    "tanvi": 83.10,
    "aditya": 95.50,
    "meera": 76.20,
    "yash": 63.90,
    "divya": 87.30,
    "arjun": 81.00,
    "shruti": 90.50
}


def lookup_marks(name: str) -> dict:
    normalized_name = " ".join(name.split()).casefold()
    if not normalized_name:
        raise ValueError("Provide a non-empty student name.")

    if normalized_name in data:
        return {
            "status": "found",
            "student_name": normalized_name,
            "standard": 10,
            "marks": data[normalized_name],
            "marks_unit": "unspecified",
        }

    # A low cutoff offers spelling candidates, never an automatic identity match.
    # Avoid weak fuzzy suggestions for one- or two-character queries.
    matches = (
        process.extract(
            normalized_name, sorted(data), scorer=fuzz.WRatio, score_cutoff=60, limit=3
        )
        if len(normalized_name) >= 3
        else []
    )
    suggestions = [
        {"student_name": candidate, "spelling_similarity": round(score, 2)}
        for candidate, score, _ in matches
    ]
    return {
        "status": "confirmation_required" if suggestions else "not_found",
        "requested_name": name,
        "suggestions": suggestions,
        "next_step": (
            "Ask the user which suggested student they mean before looking up marks."
            if suggestions
            else "Ask the user to check the student's name; no matching record was found."
        ),
    }
