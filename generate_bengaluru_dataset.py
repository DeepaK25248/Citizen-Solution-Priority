"""
Generates data/bengaluru_complaints.csv - a labeled text dataset for
training the complaint classifier, scoped to Bengaluru.

Why generated rather than downloaded: BBMP's real, public grievance dataset
(github.com/Vonter/bbmp-citizen-grievances, ~7.5 lakh rows since 2020) is
structured — Category / Sub Category / Ward / Status — but does not include
the citizen's free-text complaint wording, which is what a text classifier
like the one in "NLP based Model for Classification of Complaints" needs to
learn from. This script builds free-text training sentences using BBMP's
own category taxonomy (see DATA.md in that repo: Electrical, Solid Waste,
Road Maintenance, Storm Water Drain, etc.) combined with real Bengaluru
ward/locality names, so the *labels* match how Bengaluru actually
categorizes grievances even though the *sentences* are templated rather
than scraped verbatim complaints.

Run directly to regenerate the CSV:
    python generate_bengaluru_dataset.py
"""

import csv
import random

random.seed(42)

WARDS = [
    "Koramangala", "Indiranagar", "Whitefield", "HSR Layout", "Jayanagar",
    "Malleswaram", "Rajajinagar", "BTM Layout", "Marathahalli", "Yelahanka",
    "Basavanagudi", "JP Nagar", "Hebbal", "Electronic City", "Banashankari",
    "RT Nagar", "Vijayanagar", "Sarjapur Road", "Bellandur", "KR Puram",
    "Domlur", "Frazer Town", "Shivajinagar", "Ulsoor", "Vidyaranyapura",
]

LOCATION_PHRASES = [
    "{n} Main Road, {ward}", "{n} Cross, {ward}", "the service road near {ward} bus stop",
    "the market area in {ward}", "the junction near {ward} metro station",
    "the lane behind {ward} bus depot", "the signal near {ward} circle",
    "the stretch between {ward} and the ring road", "the by-lane near {ward} park",
    "outside the {ward} government school", "near the {ward} lake",
]


def loc():
    phrase = random.choice(LOCATION_PHRASES)
    return phrase.format(n=random.choice(["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "9th", "12th", "16th", "27th", "80 Feet"]),
                          ward=random.choice(WARDS))


# Each category maps to BBMP's real grievance taxonomy (see DATA.md) with
# several free-text templates that reference a location.
TEMPLATES = {
    "Road Maintenance": [
        "There is a large pothole on {loc} that is damaging vehicles.",
        "The road at {loc} has completely caved in after the rain.",
        "Deep cracks have formed on {loc}, making it dangerous for two-wheelers.",
        "The asphalt on {loc} is crumbling and needs urgent repair.",
        "A pothole on {loc} caused an accident last week.",
        "The road surface near {loc} is uneven and full of gravel.",
        "Newly laid road at {loc} has already developed cracks.",
        "The footpath near {loc} is broken and unsafe for pedestrians.",
        "Multiple potholes have appeared on {loc} since the monsoon began.",
        "The road divider near {loc} is damaged and needs to be fixed.",
    ],
    "Storm Water Drain": [
        "The storm water drain near {loc} is overflowing onto the road.",
        "Heavy rain has flooded {loc} and traffic is stuck.",
        "The drain at {loc} is clogged with debris and not draining properly.",
        "Water is stagnating on {loc} for days after every rain.",
        "The rajakaluve near {loc} has overflowed into nearby houses.",
        "Waterlogging on {loc} makes it impassable during heavy rain.",
        "The stormwater drain cover near {loc} is broken, exposing an open channel.",
        "Rainwater from {loc} is entering ground floor shops.",
        "The culvert near {loc} is blocked causing water to back up onto the street.",
    ],
    "Solid Waste": [
        "Garbage has not been collected from {loc} for over a week.",
        "There is an illegal garbage dump forming near {loc}.",
        "Waste bins near {loc} are overflowing and attracting stray dogs.",
        "Construction debris has been dumped illegally at {loc}.",
        "The BBMP garbage truck has skipped {loc} for several days.",
        "Segregated waste is being mixed and left uncollected at {loc}.",
        "A foul smell from rotting garbage near {loc} is affecting residents.",
        "Plastic waste is scattered all over {loc} after the weekly market.",
        "Dead leaves and yard waste are piling up uncollected near {loc}.",
    ],
    "Street Light / Electrical": [
        "The street light at {loc} has not worked for over a month.",
        "There is exposed electrical wiring hanging near {loc}.",
        "Frequent power cuts are affecting {loc} every evening.",
        "An electric pole near {loc} is leaning dangerously.",
        "The transformer near {loc} is making a loud sparking noise.",
        "Streetlights along {loc} are completely dark, making it unsafe at night.",
        "A live wire is exposed on the ground near {loc} after the storm.",
        "The BESCOM junction box at {loc} is open and unguarded.",
        "Voltage fluctuations near {loc} have damaged household appliances.",
    ],
    "Water Supply": [
        "There has been no BWSSB water supply to {loc} for three days.",
        "A water pipeline near {loc} has burst and is flooding the street.",
        "Water pressure at {loc} is extremely low every morning.",
        "Contaminated water is coming through the taps near {loc}.",
        "The water tanker did not arrive at {loc} as scheduled.",
        "An underground pipe leak near {loc} is wasting a lot of water.",
        "Residents of {loc} have had irregular water supply for two weeks.",
    ],
    "Sewage / Sanitation": [
        "The sewage line near {loc} is overflowing onto the street.",
        "Public toilets near {loc} are extremely unhygienic and need cleaning.",
        "An open manhole near {loc} is a serious safety hazard.",
        "Sewage water is mixing with the drinking water line near {loc}.",
        "The underground drainage near {loc} has been leaking for weeks.",
        "Mosquito breeding is rampant due to stagnant sewage near {loc}.",
        "The community toilet block at {loc} has no working water connection.",
    ],
    "Stray Animals": [
        "A pack of stray dogs near {loc} has been chasing pedestrians.",
        "Stray cattle are blocking traffic regularly at {loc}.",
        "Residents near {loc} are worried about aggressive stray dogs at night.",
        "Stray dogs near {loc} need to be sterilized and vaccinated urgently.",
        "A stray dog bit a child near {loc} yesterday.",
        "Monkeys from the park near {loc} are entering homes and causing damage.",
    ],
    "Parks & Trees": [
        "A large tree branch near {loc} is at risk of falling on the road.",
        "The park at {loc} is poorly maintained with overgrown grass.",
        "Playground equipment in the park near {loc} is broken and unsafe.",
        "An uprooted tree near {loc} is still blocking the footpath after the storm.",
        "The park near {loc} has no functioning lights after sunset.",
        "Garden waste has not been cleared from the park at {loc}.",
    ],
    "Encroachment": [
        "A shop near {loc} has illegally encroached onto the footpath.",
        "Illegal construction is taking place near {loc} without approval.",
        "Vendors near {loc} have blocked the pedestrian path with their stalls.",
        "Parked vehicles are illegally occupying the footpath at {loc}.",
        "An unauthorized structure has come up on public land near {loc}.",
    ],
    "Others": [
        "I would like feedback on how to track my complaint status online.",
        "This is a general inquiry about BBMP office working hours.",
        "How do I update my registered mobile number in the grievance portal?",
        "I want to appreciate the quick response from the ward office near {loc}.",
        "Can you tell me which ward office covers {loc}?",
        "I have a suggestion for improving the online complaints portal.",
        "Requesting information about property tax payment near {loc}.",
    ],
}


def generate(rows_per_category: int = 170):
    rows = []
    for category, templates in TEMPLATES.items():
        combos = set()
        attempts = 0
        while len(combos) < rows_per_category and attempts < rows_per_category * 20:
            attempts += 1
            template = random.choice(templates)
            text = template.format(loc=loc()) if "{loc}" in template else template
            combos.add(text)
        for text in combos:
            rows.append((text, category))
    random.shuffle(rows)
    return rows


if __name__ == "__main__":
    rows = generate(rows_per_category=170)
    print(f"Generated {len(rows)} complaint rows across {len(TEMPLATES)} categories.")
    with open("data/bengaluru_complaints.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "category"])
        writer.writerows(rows)
    print("Saved to data/bengaluru_complaints.csv")
