import subprocess
import requests
import json
import os
import re

# --- Step 1: Keyword mapping ---
SECTOR_KEYWORDS = {
    # --- Healthcare ---
    "hospital": "Healthcare",
    "clinic": "Healthcare",
    "medical": "Healthcare",
    "pharma": "Healthcare",
    "laboratory": "Healthcare",
    "lab": "Healthcare",
    "dental": "Healthcare",
    "veterinary": "Healthcare",
    "vet": "Healthcare",
    "health": "Healthcare",
    "care center": "Healthcare",
    "rehab": "Healthcare",
    "therapy": "Healthcare",

    # --- Finance / Banking / Insurance ---
    "bank": "Finance",
    "finance": "Finance",
    "financial": "Finance",
    "credit": "Finance",
    "loan": "Finance",
    "mortgage": "Finance",
    "investment": "Finance",
    "asset": "Finance",
    "securities": "Finance",
    "insurance": "Finance",
    "reinsurance": "Finance",
    "broker": "Finance",
    "holding": "Finance",
    "fund": "Finance",
    "capital": "Finance",

    # --- Education ---
    "school": "Education",
    "university": "Education",
    "college": "Education",
    "academy": "Education",
    "institut": "Education",      # covers 'institute' / 'institution'
    "campus": "Education",
    "student": "Education",
    "education": "Education",
    "training": "Education",
    "kindergarten": "Education",
    "high school": "Education",

    # --- Government / Public Sector ---
    "government": "Government",
    "ministry": "Government",
    "department": "Government",
    "county": "Government",
    "city": "Government",
    "town": "Government",
    "village": "Government",
    "municip": "Government",
    "state": "Government",
    "federal": "Government",
    "provinc": "Government",
    "public": "Government",
    "gov": "Government",
    "authority": "Government",
    "agency": "Government",
    "embassy": "Government",
    "consulate": "Government",
    "court": "Government",
    "judicial": "Government",
    "parliament": "Government",

    # --- Legal / Law Firms ---
    "law": "Legal",
    "attorney": "Legal",
    "legal": "Legal",
    "solicitor": "Legal",
    "barrister": "Legal",
    "notary": "Legal",
    "court": "Legal",
    "llp": "Legal",
    "Lawyers": "Legal",

    # --- Manufacturing / Industrial / Engineering ---
    "manufactur": "Manufacturing",
    "factory": "Manufacturing",
    "industrial": "Manufacturing",
    "plant": "Manufacturing",
    "machinery": "Manufacturing",
    "engineering": "Manufacturing",
    "aerospace": "Manufacturing",
    "automotive": "Manufacturing",
    "construction": "Manufacturing",
    "metal": "Manufacturing",
    "plastics": "Manufacturing",
    "printing": "Manufacturing",
    "production": "Manufacturing",
    "fabrication": "Manufacturing",
    "equipment": "Manufacturing",

    # --- Energy / Utilities / Oil & Gas ---
    "energy": "Energy",
    "oil": "Energy",
    "gas": "Energy",
    "utility": "Energy",
    "electric": "Energy",
    "power": "Energy",
    "renewable": "Energy",
    "solar": "Energy",
    "wind": "Energy",
    "nuclear": "Energy",
    "pipeline": "Energy",
    "hydro": "Energy",
    "fuel": "Energy",

    # --- Technology / IT / Telecom ---
    " it ": "Technology",
    "(it services)": "Technology",
    " it company": "Technology",
    "tech": "Technology",
    "software": "Technology",
    "hardware": "Technology",
    "data": "Technology",
    "it ": "Technology",
    "information": "Technology",
    "cyber": "Technology",
    "systems": "Technology",
    "network": "Technology",
    "cloud": "Technology",
    "telecom": "Technology",
    "communications": "Technology",
    "ai ": "Technology",
    "ml ": "Technology",
    "automation": "Technology",
    "robotics": "Technology",
    "electronics": "Technology",

    # --- Transportation / Logistics / Automotive ---
    "logistic": "Transportation",
    "transport": "Transportation",
    "shipping": "Transportation",
    "freight": "Transportation",
    "courier": "Transportation",
    "trucking": "Transportation",
    "rail": "Transportation",
    "bus": "Transportation",
    "aero": "Transportation",
    "aviation": "Transportation",
    "airline": "Transportation",
    "airport": "Transportation",
    "maritime": "Transportation",
    "port": "Transportation",
    "delivery": "Transportation",
    "fleet": "Transportation",
    "truck": "Transportation",
    "transportation": "Transportation",

    # --- Retail / Consumer / E-commerce ---
    "retail": "Retail",
    "store": "Retail",
    "shop": "Retail",
    "supermarket": "Retail",
    "mall": "Retail",
    "market": "Retail",
    "boutique": "Retail",
    "ecommerce": "Retail",
    "wholesale": "Retail",
    "distributor": "Retail",
    "supplier": "Retail",
    "chain": "Retail",

    # --- Hospitality / Food / Travel ---
    "hospitality": "Hospitality",
    "hotel": "Hospitality",
    "resort": "Hospitality",
    "restaurant": "Hospitality",
    "cafe": "Hospitality",
    "bar": "Hospitality",
    "catering": "Hospitality",
    "travel": "Hospitality",
    "tourism": "Hospitality",
    "motel": "Hospitality",
    "casino": "Hospitality",
    "event": "Hospitality",


    # --- Real Estate / Construction ---
    "real estate": "Real Estate",
    "property": "Real Estate",
    "developer": "Real Estate",
    "construction": "Real Estate",
    "building": "Real Estate",
    "architect": "Real Estate",
    "design": "Real Estate",
    "housing": "Real Estate",
    "contractor": "Real Estate",

    # --- Agriculture / Food Production ---
    "farm": "Agriculture",
    "agri": "Agriculture",
    "crop": "Agriculture",
    "dairy": "Agriculture",
    "meat": "Agriculture",
    "fisher": "Agriculture",
    "seafood": "Agriculture",
    "food": "Agriculture",
    "grain": "Agriculture",
    "agro": "Agriculture",
    "brew": "Agriculture",
    "beverage": "Agriculture",

    # --- Media / Entertainment ---
    "media": "Media",
    "press": "Media",
    "news": "Media",
    "magazine": "Media",
    "tv": "Media",
    "television": "Media",
    "broadcast": "Media",
    "radio": "Media",
    "film": "Media",
    "movie": "Media",
    "music": "Media",
    "publisher": "Media",
    "publishing": "Media",

    # --- Nonprofit / NGO / Charity ---
    "ngo": "Nonprofit",
    "foundation": "Nonprofit",
    "charity": "Nonprofit",
    "association": "Nonprofit",
    "organization": "Nonprofit",
    "nonprofit": "Nonprofit",
    "church": "Nonprofit",
    "ministry": "Nonprofit",
    "religious": "Nonprofit",

    # --- Defense / Security ---
    "defense": "Defense",
    "military": "Defense",
    "army": "Defense",
    "navy": "Defense",
    "air force": "Defense",
    "security": "Defense",
    "aerospace": "Defense",
    "weapons": "Defense",
    "contractor": "Defense",

    # --- Miscellaneous / Catch-all ---
    "consulting": "Professional Services",
    "advisory": "Professional Services",
    "marketing": "Professional Services",
    "design": "Professional Services",
    "printing": "Professional Services",
    "cleaning": "Services",
    "maintenance": "Services",
    "repair": "Services",
    "waste": "Utilities",
    "water": "Utilities",
    "sanitation": "Utilities",
}


def guess_sector(name_or_desc):
    text = (name_or_desc or "").lower()
    sector_counts = {}

    for keyword, sector in SECTOR_KEYWORDS.items():
        pattern = r'(?<![a-zA-Z])' + \
            re.escape(keyword.lower()) + r'(?![a-zA-Z])'
        if re.search(pattern, text):
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

    if sector_counts:
        # Return the sector with the highest count
        return max(sector_counts, key=sector_counts.get)

    return "Unknown"


# --- Fetch latest ransomware victim data ---
res = requests.get('https://www.ransomlook.io/api/last')

if res.status_code == 200:
    data = res.json()

    # --- Add sector tagging to each record ---
    for post in data:
        name = post.get("post_title", "")
        desc = post.get("description", "")
        combined_text = f"{name} {desc}"
        post["sector"] = guess_sector(combined_text)

    # --- Write enriched output ---
    with open('output.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print(f"Wrote {len(data)} records with sector info → output.json")

else:
    print(f"Failed to fetch data. Status code: {res.status_code}")
