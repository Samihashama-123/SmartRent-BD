def estimate_fair_rent(area: str, property_type: str, distance_km: float = 1.0, facilities: list = None):
    """
    Predicts realistic student market rent in Dhaka campus hubs
    based on comprehensive real-estate data heuristics.
    """
    facilities = facilities or []

    # Base rent per property type
    base_rates = {
        "Mess Seat": 3200,
        "Single Room": 7500,
        "Bachelor Flat": 19000,
        "Hostel Seat": 4500
    }

    base = base_rates.get(property_type, 3500)

    # Area multiplier index in Dhaka campus zones
    area_weights = {
        "Bashundhara R/A": 1.30,   # Near NSU, IUB, AIUB
        "Dhanmondi": 1.35,         # Near UIU, Daffodil, Dhaka College, State Univ
        "Farmgate": 1.15,          # Central coaching & college hub
        "Azimpur": 1.05,           # Close to DU, Home Economics
        "Katabon / Nilkhet": 1.10, # Walking distance to DU & BUET
        "Mohakhali / Banani": 1.40,# Near BRAC University
        "Mirpur": 0.90,            # BUP, MIST proximity
        "Uttara": 1.10,            # IUT commute / sector colleges
        "Lalbagh": 0.85,           # Old Dhaka
        "Chawkbazar": 0.85         # Old Dhaka
    }

    weight = 1.0
    for a_key, val in area_weights.items():
        if a_key.lower() in area.lower():
            weight = val
            break

    rent = base * weight

    # Proximity premium (closer to campus is in extreme demand)
    if distance_km <= 0.5:
        rent += (base * 0.12)
    elif distance_km <= 1.0:
        rent += (base * 0.05)
    elif distance_km > 3.0:
        rent -= (base * 0.08)

    # Facility additions
    breakdown = []
    facility_deltas = {
        "attached_bath": (1200 if property_type == "Single Room" else 400, "Attached Washroom"),
        "generator": (600 if property_type == "Single Room" else 250, "IPS / Generator Backup"),
        "meals": (3500, "Daily 2-3 Meals Included"),
        "wifi": (200, "High Speed Optical Fiber Wi-Fi"),
        "lift": (300, "Building Elevator / Lift"),
        "cctv": (150, "24/7 CCTV Security"),
        "balcony": (500 if property_type == "Single Room" else 200, "Attached Balcony / Veranda"),
        "refrigerator": (200, "Shared Refrigerator Access"),
        "water_247": (150, "Uninterrupted 24/7 Deep-Tube Water")
    }

    for fac, (addon, label) in facility_deltas.items():
        if fac in facilities:
            rent += addon
            breakdown.append({"feature": label, "value": addon})

    recommended = round(rent / 50) * 50
    min_rent = round((recommended * 0.92) / 50) * 50
    max_rent = round((recommended * 1.08) / 50) * 50

    return {
        "area": area,
        "property_type": property_type,
        "distance_km": distance_km,
        "recommended_rent": recommended,
        "range_min": min_rent,
        "range_max": max_rent,
        "breakdown": breakdown
    }

def analyze_rent_fairness(actual_rent: int, estimated_rent: int):
    diff = actual_rent - estimated_rent
    diff_percent = (diff / estimated_rent) * 100

    if diff_percent <= -12:
        return {
            "status": "Exceptional Value / Budget Friendly",
            "badge_color": "emerald",
            "message": f"৳{abs(diff):,} lower than estimated market average for this area!",
            "stars": 5
        }
    elif diff_percent <= 6:
        return {
            "status": "Fair Market Price",
            "badge_color": "teal",
            "message": "Priced accurately in line with standard student market rates.",
            "stars": 4
        }
    elif diff_percent <= 18:
        return {
            "status": "Slightly Premium",
            "badge_color": "amber",
            "message": f"৳{diff:,} above typical base rates (may include prime location or perks).",
            "stars": 3
        }
    else:
        return {
            "status": "High Premium / Expensive",
            "badge_color": "rose",
            "message": f"৳{diff:,} significantly above local student average. Verify luxury inclusions.",
            "stars": 2
        }
