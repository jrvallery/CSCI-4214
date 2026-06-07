import re


DIN_CODES = tuple("ABCDEFGHIJKLMNO")
DIN_COLUMNS = (
    "250 or less",
    "251-270",
    "271-290",
    "291-310",
    "311-330",
    "330 or more",
)
DIN_TABLE = {
    "A": (0.75, 0.75, 0.0, 0.0, 0.0, 0.0),
    "B": (1.00, 1.00, 0.75, 0.0, 0.0, 0.0),
    "C": (1.50, 1.25, 1.00, 0.0, 0.0, 0.0),
    "D": (1.75, 1.50, 1.50, 1.25, 0.0, 0.0),
    "E": (2.25, 2.00, 1.75, 1.50, 1.50, 0.0),
    "F": (2.75, 2.50, 2.25, 2.00, 1.75, 1.75),
    "G": (3.50, 3.00, 2.75, 2.50, 2.25, 2.00),
    "H": (0.0, 3.50, 3.00, 3.00, 2.75, 2.50),
    "I": (0.0, 4.50, 4.00, 3.50, 3.50, 3.00),
    "J": (0.0, 5.50, 5.00, 4.50, 4.00, 3.50),
    "K": (0.0, 6.50, 6.00, 5.50, 5.00, 4.50),
    "L": (0.0, 7.50, 7.00, 6.50, 6.00, 5.50),
    "M": (0.0, 0.0, 8.50, 8.00, 7.00, 6.50),
    "N": (0.0, 0.0, 10.00, 9.50, 8.50, 8.00),
    "O": (0.0, 0.0, 11.50, 11.00, 10.00, 9.50),
}
WEIGHT_CODES = {
    (10, 13): "A",
    (14, 17): "B",
    (18, 21): "C",
    (22, 25): "D",
    (26, 30): "E",
    (31, 35): "F",
    (36, 41): "G",
    (42, 48): "H",
    (49, 57): "I",
    (58, 66): "J",
    (67, 78): "K",
    (79, 94): "L",
    (95, 995): "M",
    (996, 997): "N",
    (998, 999): "O",
}


def parse_weight(weight_input: str | int | float) -> float:
    if isinstance(weight_input, (int, float)):
        return float(weight_input)

    match = re.search(r"\d+\.?\d*", str(weight_input).lower())
    if match is None:
        raise ValueError("weight must include a numeric value")

    weight = float(match.group())
    text = str(weight_input).lower()
    if "lb" in text or "pound" in text:
        return weight * 0.453592
    return weight


def get_weight_code(weight_kg: float) -> str:
    for (low, high), code in WEIGHT_CODES.items():
        if low <= weight_kg <= high:
            return code
    raise ValueError("weight is outside the supported DIN chart range")


def get_boot_column(boot_sole_length_mm: int) -> str:
    if boot_sole_length_mm <= 250:
        return "250 or less"
    if boot_sole_length_mm <= 270:
        return "251-270"
    if boot_sole_length_mm <= 290:
        return "271-290"
    if boot_sole_length_mm <= 310:
        return "291-310"
    if boot_sole_length_mm <= 330:
        return "311-330"
    return "330 or more"


def adjust_code(code: str, age: int, skier_type: int) -> str:
    if skier_type not in {1, 2, 3}:
        raise ValueError("skier_type must be 1, 2, or 3")

    index = DIN_CODES.index(code)
    if age < 9 or age > 50:
        index -= 1

    if skier_type == 2:
        index += 1
    elif skier_type == 3:
        index += 2

    index = max(0, min(index, len(DIN_CODES) - 1))
    return DIN_CODES[index]


def calculate_din(
    weight: str | int | float,
    boot_sole_length_mm: int,
    age: int,
    skier_type: int,
) -> float:
    weight_kg = parse_weight(weight)
    code = get_weight_code(weight_kg)
    adjusted_code = adjust_code(code, age, skier_type)
    column = get_boot_column(boot_sole_length_mm)
    return DIN_TABLE[adjusted_code][DIN_COLUMNS.index(column)]


def get_din(weight: str | int | float, boot: int, age: int, skier_type: int) -> float:
    return calculate_din(
        weight=weight,
        boot_sole_length_mm=boot,
        age=age,
        skier_type=skier_type,
    )