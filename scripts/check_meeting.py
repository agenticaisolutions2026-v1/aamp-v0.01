from pathlib import Path

folders = [
    Path("backend"),
    Path("alembic/versions"),
]

keywords = [
    "meeting",
    "meeting_link",
    "meeting_date",
    "meeting_time",
    "duration",
    "reschedul",
    "cancel",
]

for folder in folders:
    print(f"\n{'=' * 70}")
    print(f"SEARCHING: {folder}")
    print("=" * 70)

    for file in folder.rglob("*"):
        if not file.is_file():
            continue

        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(keyword.lower() in line.lower() for keyword in keywords):
                print(f"{file}:{line_number}: {line.strip()}")