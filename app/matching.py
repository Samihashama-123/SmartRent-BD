def calculate_compatibility(p1, p2):
    """
    Calculates compatibility score (0-100%) and generates structured explanation
    between two roommate profiles.
    p1 and p2 are dictionaries or sqlite3.Row containing profile and user info.
    """
    score = 0
    max_score = 100
    reasons = []
    cautions = []

    # 1. Budget Overlap (25 points)
    b1_min = p1.get('budget_min', 0)
    b1_max = p1.get('budget_max', 100000)
    b2_min = p2.get('budget_min', 0)
    b2_max = p2.get('budget_max', 100000)

    overlap_min = max(b1_min, b2_min)
    overlap_max = min(b1_max, b2_max)

    if overlap_min <= overlap_max:
        score += 25
        reasons.append(f"Budget ranges overlap comfortably (৳{overlap_min:,} - ৳{overlap_max:,})")
    else:
        diff = overlap_min - overlap_max
        if diff <= 1500:
            score += 15
            reasons.append(f"Budget ranges are close (within ৳{diff:,} margin)")
        else:
            score += 5
            cautions.append(f"Budget discrepancy of ~৳{diff:,}")

    # 2. Campus & Area Match (20 points)
    univ1 = (p1.get('preferred_university') or '').lower().strip()
    univ2 = (p2.get('preferred_university') or '').lower().strip()
    area1 = (p1.get('preferred_area') or '').lower().strip()
    area2 = (p2.get('preferred_area') or '').lower().strip()

    if univ1 and univ2 and (univ1 in univ2 or univ2 in univ1):
        score += 12
        reasons.append(f"Both prefer accommodations near {p1.get('preferred_university')}")
    elif univ1 and univ2:
        score += 4

    if area1 and area2 and (area1 in area2 or area2 in area1):
        score += 8
        reasons.append(f"Common target living area: {p1.get('preferred_area')}")
    else:
        score += 3

    # 3. Sleep Rhythm (15 points)
    sleep1 = p1.get('sleep_schedule', 'flexible')
    sleep2 = p2.get('sleep_schedule', 'flexible')

    if sleep1 == sleep2:
        score += 15
        label = "Night Owls" if sleep1 == 'night_owl' else ("Early Birds" if sleep1 == 'early_bird' else "Flexible Sleepers")
        reasons.append(f"Synchronized sleep schedules: Both are {label}")
    elif 'flexible' in (sleep1, sleep2):
        score += 10
        reasons.append("Adaptable sleeping schedules with low friction")
    else:
        score += 3
        cautions.append("Conflicting sleep rhythms (Early Bird vs Night Owl)")

    # 4. Cleanliness Habits (15 points)
    clean1 = p1.get('cleanliness', 'moderate')
    clean2 = p2.get('cleanliness', 'moderate')

    if clean1 == clean2:
        score += 15
        reasons.append(f"Identical mess hygiene expectations ({clean1.capitalize()} cleanliness)")
    elif (clean1 == 'moderate' and clean2 in ('high', 'casual')) or (clean2 == 'moderate' and clean1 in ('high', 'casual')):
        score += 10
        reasons.append("Compatible standards of room hygiene")
    else:
        score += 4
        cautions.append("Noticeable difference in cleanliness expectations (High vs Casual)")

    # 5. Smoking Habits (15 points - critical deal breaker)
    smk1 = p1.get('smoking', 'non_smoker')
    smk2 = p2.get('smoking', 'non_smoker')

    if smk1 == 'non_smoker' and smk2 == 'non_smoker':
        score += 15
        reasons.append("Both strictly non-smokers (Healthy Smoke-Free Environment)")
    elif smk1 == 'smoker' and smk2 == 'smoker':
        score += 15
        reasons.append("Mutual smoking tolerance")
    elif 'tolerant' in (smk1, smk2):
        score += 10
        reasons.append("Smoke-tolerant living agreement")
    else:
        score = max(0, score - 10)
        cautions.append("Smoking policy conflict: One is non-smoker, other is smoker")

    # 6. Study & Guests (10 points)
    study1 = p1.get('study_habit', 'flexible')
    study2 = p2.get('study_habit', 'flexible')
    guest1 = p1.get('guest_policy', 'daytime_only')
    guest2 = p2.get('guest_policy', 'daytime_only')

    if study1 == study2:
        score += 5
        reasons.append(f"Matching study environment: {study1.capitalize()} habits")
    else:
        score += 3

    if guest1 == guest2:
        score += 5
        reasons.append(f"Aligned guest hosting rules: {guest1.replace('_', ' ').capitalize()}")
    else:
        score += 2

    # Cap at 100
    final_score = min(max_score, max(15, score))

    if final_score >= 88:
        level = "Exceptional Match"
        badge_color = "emerald"
    elif final_score >= 75:
        level = "Strong Match"
        badge_color = "teal"
    elif final_score >= 60:
        level = "Good Match"
        badge_color = "blue"
    elif final_score >= 45:
        level = "Moderate Match"
        badge_color = "amber"
    else:
        level = "Low Compatibility"
        badge_color = "rose"

    return {
        "score": final_score,
        "level": level,
        "badge_color": badge_color,
        "reasons": reasons,
        "cautions": cautions
    }
