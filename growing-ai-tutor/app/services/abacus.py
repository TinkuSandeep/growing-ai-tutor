PLACE_NAMES = ["Thousands", "Hundreds", "Tens", "Ones"]


def represent(number: int) -> dict:
    digits = [int(x) for x in f"{number:04d}"]
    columns = []
    for place, digit in zip(PLACE_NAMES, digits):
        columns.append({"place": place, "digit": digit, "active_beads": digit, "total_beads": 9})
    return {"number": number, "columns": columns}


def teaching_steps(number: int) -> list[str]:
    rep = represent(number)
    steps = []
    for col in rep["columns"]:
        if col["digit"]:
            steps.append(f"Move {col['digit']} bead(s) in the {col['place'].lower()} column.")
    return steps or ["Keep all beads at zero."]
