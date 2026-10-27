"""Localized presentation only. Never changes landlord-authored database content."""
import re

DEMO_TITLES = {
    'Bright 2-Seat Mess Room Near BUET & DU (Palashi Gate)': 'বুয়েট ও ঢাকা বিশ্ববিদ্যালয়ের কাছে উজ্জ্বল দুই-সিটের মেস রুম (পলাশী গেট)',
    'Premium AC Single Room with Balcony (Block C - 2 min to NSU)': 'নর্থ সাউথ বিশ্ববিদ্যালয়ের ২ মিনিট দূরে বারান্দাসহ প্রিমিয়াম এসি সিঙ্গেল রুম',
    'Safe Female Student Mess Seat (Facing BRACU New Campus)': 'ব্র্যাক বিশ্ববিদ্যালয়ের নতুন ক্যাম্পাসের সামনে ছাত্রীদের নিরাপদ মেস সিট',
    'Complete 3-Bed Bachelor Flat for University Group (Dhanmondi 9/A)': 'বিশ্ববিদ্যালয়ের শিক্ষার্থীদের জন্য তিন বেডরুমের সম্পূর্ণ ফ্ল্যাট (ধানমন্ডি ৯/এ)',
    'Affordable Single Room Sublet with Attached Bath (Tejgaon / Farmgate)': 'তেজগাঁও–ফার্মগেটে সংযুক্ত বাথরুমসহ সাশ্রয়ী সিঙ্গেল রুম সাবলেট',
    'Spacious student near campus': 'ক্যাম্পাসের কাছে শিক্ষার্থীদের প্রশস্ত কক্ষ',
}
DEMO_DESCRIPTIONS = {
    'Bright 2-Seat Mess Room Near BUET & DU (Palashi Gate)': 'বুয়েট ও ঢাকা বিশ্ববিদ্যালয়ের শিক্ষার্থীদের জন্য উপযুক্ত। শান্ত, পরিচ্ছন্ন চারতলার ব্যাচেলর ফ্ল্যাটে দুই বেডের বড় কক্ষ। পলাশী গেট ও কাঁটাবন মোড়ে হাঁটাপথে প্রায় ৫ মিনিট। ফিল্টার করা পানির ব্যবস্থা, ৫০ এমবিপিএস ফাইবার ওয়াই-ফাই, বিদ্যুৎ না থাকলে আইপিএস ব্যাকআপ এবং দিনে দুই বেলা রান্নার ব্যবস্থা রয়েছে।',
    'Premium AC Single Room with Balcony (Block C - 2 min to NSU)': 'বসুন্ধরা ব্লক সি-তে ব্যক্তিগত বারান্দা ও সংযুক্ত বাথরুমসহ সিঙ্গেল রুম। নর্থ সাউথ বিশ্ববিদ্যালয়ের ৮ নম্বর গেট ও আইইউবি থেকে প্রায় ২০০ মিটার দূরে। পড়ার টেবিল, চেয়ার, আলমারি ও বিছানা আছে। ফ্যান, বাতি ও ওয়াই-ফাইয়ের জন্য আইপিএস ব্যাকআপ এবং লিফট ও নিরাপত্তার ব্যবস্থা রয়েছে।',
    'Safe Female Student Mess Seat (Facing BRACU New Campus)': 'ব্র্যাক বিশ্ববিদ্যালয়ের মেরুল বাড্ডা ক্যাম্পাসের সামনে ছাত্রীদের জন্য মেস/হোস্টেল। বিজ্ঞাপনদাতার তথ্য অনুযায়ী নারী নিরাপত্তারক্ষী, সিসিটিভি ও প্রবেশ নিয়ন্ত্রণের ব্যবস্থা রয়েছে। দিনে তিন বেলা ঘরোয়া খাবার এবং পড়াশোনার জন্য শান্ত কক্ষ রয়েছে।',
    'Complete 3-Bed Bachelor Flat for University Group (Dhanmondi 9/A)': 'বিশ্ববিদ্যালয়ের পাঁচ থেকে ছয়জন শিক্ষার্থীর জন্য প্রস্তুত ১৪৫০ বর্গফুটের তিন বেডরুম ও তিন বাথরুমের ফ্ল্যাট। বড় ড্রয়িং–ডাইনিং, গ্যাসসংযোগসহ রান্নাঘর, কাপড় ধোয়ার জায়গা ও দুটি দক্ষিণমুখী বারান্দা আছে। বিজ্ঞাপন অনুযায়ী নিরাপত্তারক্ষী, সিসিটিভি, লিফট ও গাড়ি রাখার জায়গা রয়েছে।',
    'Affordable Single Room Sublet with Attached Bath (Tejgaon / Farmgate)': 'পরিবারের ফ্ল্যাটে আলাদা চাবিসহ সাশ্রয়ী সিঙ্গেল রুম সাবলেট। ফার্মগেট মেট্রো স্টেশন থেকে হাঁটাপথে প্রায় তিন মিনিট। ঢাকা বিশ্ববিদ্যালয়, ফার্মগেটের কলেজ ও তেজগাঁও এলাকায় যাতায়াত সহজ। ভর্তি পরীক্ষা ও চাকরির পরীক্ষার প্রস্তুতির জন্য শান্ত পরিবেশের কথা বিজ্ঞাপনে উল্লেখ রয়েছে।',
    'Spacious student near campus': 'বারান্দাসহ বড় কক্ষ।',
}

def listing_text(listing, field, language='en'):
    """Demo entries have verified human-authored UI translations. New landlord text stays original."""
    value = str(listing.get(field) or '') if isinstance(listing, dict) else ''
    if language != 'bn':
        return value
    title = str(listing.get('title') or '')
    if field == 'title':
        return listing.get('title_bn') or DEMO_TITLES.get(value, value)
    if field == 'description':
        return listing.get('description_bn') or DEMO_DESCRIPTIONS.get(title, value)
    return value


def has_listing_translation(listing, field, language='en'):
    if language != 'bn' or not isinstance(listing, dict):
        return True
    if field == 'title':
        return bool(listing.get('title_bn')) or str(listing.get('title') or '') in DEMO_TITLES
    if field == 'description':
        return bool(listing.get('description_bn')) or str(listing.get('title') or '') in DEMO_DESCRIPTIONS
    return False

ENUM = {
    'Mess Seat': 'মেস সিট', 'Single Room': 'সিঙ্গেল রুম',
    'Bachelor Flat': 'ব্যাচেলর ফ্ল্যাট', 'Hostel Seat': 'হোস্টেল সিট',
    'Shared Room': 'শেয়ার রুম', 'Apartment': 'ফ্ল্যাট',
    'Male Only': 'শুধু ছাত্র', 'Female Only': 'শুধু ছাত্রী',
    'Any': 'যেকোনো', 'Mixed': 'সবার জন্য', 'Any Gender':'যেকোনো লিঙ্গ',
    'night_owl':'রাত জাগা', 'early_bird':'সকালে ওঠা', 'flexible':'নমনীয়',
    'silent':'নীরবে পড়া', 'group':'দলবদ্ধ পড়া', 'moderate':'মাঝারি',
    'high':'উচ্চ', 'casual':'সাধারণ', 'non_smoker':'অধূমপায়ী',
    'tolerant':'সহনশীল', 'smoker':'ধূমপায়ী', 'mess_food':'মেসের খাবার',
    'self_cooking':'নিজে রান্না', 'daytime_only':'শুধু দিনের বেলা',
    'weekends_allowed':'সাপ্তাহিক ছুটিতে', 'strict_no_guests':'অতিথি নয়',
    'Exceptional Match':'অসাধারণ মিল', 'Strong Match':'খুব ভালো মিল',
    'Good Match':'ভালো মিল', 'Moderate Match':'মাঝারি মিল',
    'Low Compatibility':'কম মিল',
    'Katabon':'কাঁটাবন', 'Palashi':'পলাশী', 'Dhanmondi':'ধানমন্ডি',
    'Farmgate':'ফার্মগেট', 'Bashundhara R/A':'বসুন্ধরা আবাসিক এলাকা',
    'Mohakhali / Merul Badda':'মহাখালী / মেরুল বাড্ডা',
    'Matidali':'মাটিডালি', 'Kuril':'কুড়িল',
    'Merul Badda':'মেরুল বাড্ডা','Rampura':'রামপুরা','Banani':'বনানী',
    'Azimpur':'আজিমপুর','Lalbagh':'লালবাগ',
    'self_cook':'নিজে রান্না','no_guests':'বাইরের অতিথি নয়',
    'Bogura':'বগুড়া', 'Bogra':'বগুড়া', 'Rajshahi':'রাজশাহী',
}

EN_VALUES = {
    'night_owl':'Night owl', 'early_bird':'Early bird', 'flexible':'Flexible',
    'silent':'Silent study', 'group':'Group study', 'moderate':'Moderate',
    'high':'High', 'casual':'Casual', 'non_smoker':'Non-smoker',
    'tolerant':'Tolerant', 'smoker':'Smoker', 'mess_food':'Mess food',
    'self_cooking':'Self cooking', 'self_cook':'Self-cooked meals', 'no_guests':'No outside guests', 'daytime_only':'Daytime only',
    'weekends_allowed':'Weekends allowed', 'strict_no_guests':'No outside guests',
}

def enum_text(value, language='en'):
    if value is None:
        return ''
    text = str(value)
    if language != 'bn':
        return EN_VALUES.get(text, text)
    if text in ENUM:
        return ENUM[text]
    # Handle lists of known area names; don't translate arbitrary names.
    if ' / ' in text:
        return ' / '.join(ENUM.get(bit,bit) for bit in text.split(' / '))
    return text

# Matching reasons are created dynamically by app/matching.py.
# Translate patterns here rather than trying to replace DOM text nodes.
REASONS = [
    (r'Budget ranges overlap comfortably \(৳([\d,]+) - ৳([\d,]+)\)', r'বাজেটের সীমা মিলে যায় (৳\1 – ৳\2)'),
    (r'Budget ranges are close \(within ৳([\d,]+) margin\)', r'বাজেট প্রায় মিলে যায় (৳\1 পার্থক্য)'),
    (r'Budget discrepancy of ~৳([\d,]+)', r'বাজেটে প্রায় ৳\1 পার্থক্য আছে'),
    (r'Both prefer accommodations near (.+)', r'দুজনেই \1-এর কাছে থাকতে চান'),
    (r'Common target living area: (.+)', r'দুজনের পছন্দের এলাকা: \1'),
    (r'Synchronized sleep schedules: Both are (.+)', r'দুজনের ঘুমের সময় একই ধরনের (\1)'),
    (r'Adaptable sleeping schedules with low friction', 'ঘুমের সময় সহজে মানিয়ে নেওয়া সম্ভব'),
    (r'Conflicting sleep rhythms \(Early Bird vs Night Owl\)', 'ঘুমের অভ্যাসে পার্থক্য আছে'),
    (r'Identical mess hygiene expectations \((.+) cleanliness\)', r'পরিচ্ছন্নতার প্রত্যাশা একই (\1)'),
    (r'Compatible standards of room hygiene', 'পরিচ্ছন্নতার অভ্যাস কাছাকাছি'),
    (r'Noticeable difference in cleanliness expectations \(High vs Casual\)', 'পরিচ্ছন্নতার প্রত্যাশায় পার্থক্য আছে'),
    (r'Both strictly non-smokers \(Healthy Smoke-Free Environment\)', 'দুজনেই ধূমপান করেন না'),
    (r'Mutual smoking tolerance', 'ধূমপানের বিষয়ে দুজনের একই পছন্দ'),
    (r'Smoke-tolerant living agreement', 'ধূমপানের নিয়ম নিয়ে সমঝোতা সম্ভব'),
    (r'Smoking policy conflict: One is non-smoker, other is smoker', 'ধূমপানের অভ্যাসে অমিল রয়েছে'),
    (r'Matching study environment: (.+) habits', r'পড়াশোনার অভ্যাস মিলে যায় (\1)'),
    (r'Aligned guest hosting rules: (.+)', r'অতিথির বিষয়ে নিয়ম একই (\1)'),
]
SPECIAL = {'Night Owls':'রাত জাগা', 'Early Birds':'সকালে ওঠা', 'Flexible Sleepers':'নমনীয় ঘুমের সময়', 'High':'উচ্চ', 'Moderate':'মাঝারি', 'Casual':'সাধারণ', 'Silent':'নীরবে পড়া', 'Group':'দলবদ্ধ পড়া', 'Daytime only':'শুধু দিনের বেলা', 'Weekends allowed':'সপ্তাহান্তে'}

def match_reason(value, language='en'):
    text = str(value or '')
    if language != 'bn':
        return text
    for pattern, replacement in REASONS:
        if re.fullmatch(pattern, text, flags=re.IGNORECASE):
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            for en, bn in SPECIAL.items():
                text = text.replace('(' + en + ')', '(' + bn + ')')
            return text
    return text


DEMO_BIOS = {
    'Competitive programmer & AI enthusiast. Usually awake coding until 2:30 AM with headphones. Keeps room spotless.': 'প্রতিযোগিতামূলক প্রোগ্রামিং ও কৃত্রিম বুদ্ধিমত্তায় আগ্রহী। সাধারণত হেডফোন পরে রাত আড়াইটা পর্যন্ত কোডিং করেন। ঘর পরিচ্ছন্ন রাখতে পছন্দ করেন।',
    'Pharmacy student at BRACU. Clean, respectful of personal boundaries, prefers a focused academic atmosphere.': 'ব্র্যাক বিশ্ববিদ্যালয়ের ফার্মেসির শিক্ষার্থী। পরিষ্কার-পরিচ্ছন্ন থাকেন, ব্যক্তিগত সীমারেখাকে সম্মান করেন এবং পড়াশোনার জন্য শান্ত পরিবেশ পছন্দ করেন।',
    'BBA junior at NSU. Passionate about startups and gaming. Easygoing roommate who loves good food and chill weekends.': 'নর্থ সাউথ বিশ্ববিদ্যালয়ে বিবিএ পড়ছেন। স্টার্টআপ ও গেমিংয়ে আগ্রহী। বন্ধুবৎসল এবং ভালো খাবার ও আরামদায়ক সপ্তাহান্ত পছন্দ করেন।',
    'DU Economics research student. Enjoys reading, quiet mornings, and a disciplined mess study environment.': 'ঢাকা বিশ্ববিদ্যালয়ের অর্থনীতি বিষয়ের গবেষণার্থী। বই পড়া, শান্ত সকাল এবং নিয়ম মেনে পড়াশোনার পরিবেশ পছন্দ করেন।',
}

def profile_bio(value, language='en'):
    value = str(value or '')
    return DEMO_BIOS.get(value, value) if language == 'bn' else value

def has_bio_translation(value, language='en'):
    return language != 'bn' or str(value or '') in DEMO_BIOS
