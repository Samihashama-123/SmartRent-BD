
# SmartRent BD — English / Bangla translations

SUPPORTED_LANGUAGES = {"en", "bn"}
DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        "home": "Home",
        "find_housing": "Find Housing",
        "roommate_match": "Roommate Matching",
        "mess_manager": "Mess Manager",
        "maintenance": "Maintenance",
        "fair_rent": "Fair Rent Calculator",
        "agreement": "Rental Agreement",
        "admin": "Admin Dashboard",
        "student": "Student",
        "landlord": "Landlord",
        "login": "Sign In",
        "register": "Create Account",
        "logout": "Sign Out",
        "profile": "My Profile",
        "search": "Search",
        "details": "View Details",
        "monthly_rent": "Monthly Rent",
        "location": "Location",
        "budget": "Budget",
        "property_type": "Property Type",
        "gender_preference": "Gender Preference",
        "save": "Save",
        "submit": "Submit",
        "cancel": "Cancel",
        "loading": "Loading...",
        "scam_warning": "Never send advance payments before viewing a property.",
    },
    "bn": {
        "home": "হোম",
        "find_housing": "বাসা খুঁজুন",
        "roommate_match": "রুমমেট খুঁজুন",
        "mess_manager": "মেস ব্যবস্থাপনা",
        "maintenance": "রক্ষণাবেক্ষণ",
        "fair_rent": "ন্যায্য ভাড়া নির্ণয়",
        "agreement": "ভাড়ার চুক্তিপত্র",
        "admin": "প্রশাসনিক ড্যাশবোর্ড",
        "student": "শিক্ষার্থী",
        "landlord": "বাড়ির মালিক",
        "login": "প্রবেশ করুন",
        "register": "অ্যাকাউন্ট তৈরি করুন",
        "logout": "বের হয়ে যান",
        "profile": "আমার প্রোফাইল",
        "search": "অনুসন্ধান",
        "details": "বিস্তারিত দেখুন",
        "monthly_rent": "মাসিক ভাড়া",
        "location": "অবস্থান",
        "budget": "বাজেট",
        "property_type": "বাসার ধরন",
        "gender_preference": "লিঙ্গভিত্তিক পছন্দ",
        "save": "সংরক্ষণ করুন",
        "submit": "জমা দিন",
        "cancel": "বাতিল করুন",
        "loading": "লোড হচ্ছে...",
        "scam_warning": "বাসা দেখার আগে কখনো অগ্রিম টাকা পাঠাবেন না।",
    },
}


def get_language(value):
    if value in SUPPORTED_LANGUAGES:
        return value
    return DEFAULT_LANGUAGE


def translate(language, key):
    language = get_language(language)

    translations = TRANSLATIONS[language]

    if key not in translations:
        raise KeyError(
            f"Missing translation: {language}.{key}"
        )

    return translations[key]
