def triangular_membership(value, low, peak, high):
    """
    Triangular fuzzy membership function.

    Returns a value between 0 and 1 indicating
    how strongly 'value' belongs to a fuzzy set.
    """

    if value <= low or value >= high:
        return 0.0

    if value == peak:
        return 1.0

    if value < peak:
        return (value - low) / (peak - low)

    return (high - value) / (high - peak)


def left_shoulder_membership(value, peak, high):
    """
    Fuzzy membership for a LOW condition.
    """

    if value <= peak:
        return 1.0

    if value >= high:
        return 0.0

    return (high - value) / (high - peak)


def right_shoulder_membership(value, low, peak):
    """
    Fuzzy membership for a HIGH condition.
    """

    if value <= low:
        return 0.0

    if value >= peak:
        return 1.0

    return (value - low) / (peak - low)


def fuzzy_priority(patient):
    """
    Calculate patient priority using fuzzy reasoning.

    Inputs:
        - severity
        - oxygen requirement
        - waiting time
        - SpO2 (optional, percent)
        - age (optional, years)

    Output:
        priority score in [0, 1]
    """

    severity = patient.severity

    # Waiting time is normalized to approximately [0, 1].
    waiting = min(patient.waiting_time / 20.0, 1.0)

    # --------------------------------------------------
    # FUZZIFICATION
    # --------------------------------------------------

    severity_low = left_shoulder_membership(
        severity,
        peak=0.30,
        high=0.50
    )

    severity_medium = triangular_membership(
        severity,
        low=0.30,
        peak=0.60,
        high=0.80
    )

    severity_high = right_shoulder_membership(
        severity,
        low=0.70,
        peak=0.90
    )

    waiting_low = left_shoulder_membership(
        waiting,
        peak=0.20,
        high=0.40
    )

    waiting_medium = triangular_membership(
        waiting,
        low=0.20,
        peak=0.50,
        high=0.80
    )

    waiting_high = right_shoulder_membership(
        waiting,
        low=0.60,
        peak=0.80
    )

    oxygen = 1.0 if patient.oxygen_required else 0.0

    # --------------------------------------------------
    # FUZZY RULES
    # --------------------------------------------------

    rules = []

    # Rule 1:
    # IF severity is HIGH THEN priority is VERY HIGH
    rules.append(
        (severity_high, 1.00)
    )

    # Rule 2:
    # IF severity is MEDIUM AND waiting is HIGH
    # THEN priority is HIGH
    rules.append(
        (min(severity_medium, waiting_high), 0.85)
    )

    # Rule 3:
    # IF severity is LOW AND waiting is HIGH
    # THEN priority is MEDIUM-HIGH
    rules.append(
        (min(severity_low, waiting_high), 0.70)
    )

    # Rule 4:
    # IF oxygen is required AND severity is MEDIUM
    # THEN priority is HIGH
    rules.append(
        (min(oxygen, severity_medium), 0.80)
    )

    # Rule 5:
    # IF severity is LOW AND waiting is LOW
    # THEN priority is LOW
    rules.append(
        (min(severity_low, waiting_low), 0.20)
    )

    # Rule 6:
    # IF severity is MEDIUM AND waiting is MEDIUM
    # THEN priority is MEDIUM
    rules.append(
        (min(severity_medium, waiting_medium), 0.60)
    )

    # Rule 7:
    # IF severity is HIGH AND waiting is HIGH
    # THEN priority is CRITICAL
    rules.append(
        (min(severity_high, waiting_high), 1.00)
    )

    # Optional clinical inputs. When age / SpO2 are not recorded for a patient
    # these rules are not added at all, so results are identical to the
    # three-input rule base.
    spo2 = getattr(patient, "spo2", None)
    if spo2 is not None:
        # Rule 8: IF SpO2 is LOW (hypoxemic) THEN priority is VERY HIGH
        rules.append(
            (left_shoulder_membership(spo2, peak=88.0, high=94.0), 0.95)
        )

    age = getattr(patient, "age", None)
    if age is not None:
        # Rule 9: IF age is HIGH AND severity is MEDIUM THEN priority is HIGH
        rules.append(
            (min(right_shoulder_membership(age, low=60.0, peak=80.0),
                 severity_medium), 0.80)
        )

    # --------------------------------------------------
    # DEFUZZIFICATION
    # --------------------------------------------------

    total_activation = sum(
        activation
        for activation, _ in rules
    )

    if total_activation == 0:
        # Safe fallback based on severity.
        return severity

    weighted_priority = sum(
        activation * output
        for activation, output in rules
    )

    priority = weighted_priority / total_activation

    return round(
        max(0.0, min(1.0, priority)),
        4
    )