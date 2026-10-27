"""Small known-location aliases for searching stored listing areas.

Not a geocoder: map place lookups use user-initiated OpenStreetMap requests.
"""

# Search terms may be typed in Bengali even though landlord data is in English.
ALIASES = {
    "বগুড়া": "bogura", "বগুড়া": "bogura", "বগরা": "bogura", "bogra": "bogura",
    "মাটিডালি": "matidali", "মাটিডালী": "matidali",
    "সাতমাথা": "satmatha", "জলেশ্বরীতলা": "jaleshwaritola",
    "ঠনঠনিয়া": "thanthania", "গোকুল": "gokul",
    "ঢাকা": "dhaka", "ধানমন্ডি": "dhanmondi",
    "কাঁটাবন": "katabon", "কাটাবন": "katabon", "পলাশী": "palashi",
    "বসুন্ধরা": "bashundhara", "ফার্মগেট": "farmgate",
    "মেরুল বাড্ডা": "merul badda", "মহাখালী": "mohakhali",
    "রাজশাহী": "rajshahi",
}
BOGURA_NEIGHBORHOODS = ("matidali", "satmatha", "thanthania", "jaleshwaritola", "gokul", "shajahanpur", "bogura", "bogra")
DHAKA_NEIGHBORHOODS = ("katabon", "bashundhara", "mohakhali", "merul badda", "dhanmondi", "farmgate", "palashi", "kuril", "tejturi")

def search_terms(value):
    """Match known synonyms in existing fields; never invent pins or city data."""
    term = str(value or '').strip().lower()[:120]
    term = ALIASES.get(term,term)
    if term == "bogura":
        return BOGURA_NEIGHBORHOODS
    if term == "dhaka":
        return DHAKA_NEIGHBORHOODS
    return (term,) if term else ()
