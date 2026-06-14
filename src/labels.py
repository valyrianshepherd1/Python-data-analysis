"""Readable labels and fixed category orders used by the Streamlit app."""

STATE_ABBREVIATIONS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

STATE_CODES = {
    1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas", 6: "California",
    8: "Colorado", 9: "Connecticut", 10: "Delaware", 11: "District of Columbia",
    12: "Florida", 13: "Georgia", 15: "Hawaii", 16: "Idaho", 17: "Illinois",
    18: "Indiana", 19: "Iowa", 20: "Kansas", 21: "Kentucky", 22: "Louisiana",
    23: "Maine", 24: "Maryland", 25: "Massachusetts", 26: "Michigan",
    27: "Minnesota", 28: "Mississippi", 29: "Missouri", 30: "Montana",
    31: "Nebraska", 32: "Nevada", 33: "New Hampshire", 34: "New Jersey",
    35: "New Mexico", 36: "New York", 37: "North Carolina", 38: "North Dakota",
    39: "Ohio", 40: "Oklahoma", 41: "Oregon", 42: "Pennsylvania",
    44: "Rhode Island", 45: "South Carolina", 46: "South Dakota", 47: "Tennessee",
    48: "Texas", 49: "Utah", 50: "Vermont", 51: "Virginia", 53: "Washington",
    54: "West Virginia", 55: "Wisconsin", 56: "Wyoming",
}

VOTE_LABELS = {
    1: "Kamala Harris",
    2: "Donald Trump",
    3: "Robert F. Kennedy Jr.",
    4: "Cornel West",
    5: "Jill Stein",
    6: "Other",
}

TURNOUT_LABELS = {0: "Did not vote", 1: "Voted"}

EDUCATION_LABELS = {
    1: "Less than high school",
    2: "High school",
    3: "Some college / no bachelor's",
    4: "Bachelor's degree",
    5: "Graduate degree",
}

RACE_LABELS = {
    1: "White, non-Hispanic",
    2: "Black, non-Hispanic",
    3: "Hispanic",
    4: "Asian or Native Hawaiian/other Pacific Islander, non-Hispanic",
    5: "Native American/Alaska Native or other race, non-Hispanic",
    6: "Multiple races, non-Hispanic",
}

SEX_LABELS = {1: "Male", 2: "Female"}

GENDER_LABELS = {1: "Man", 2: "Woman", 3: "Non-binary", 4: "Another gender"}

IDEOLOGY_LABELS = {
    1: "Extremely liberal",
    2: "Liberal",
    3: "Slightly liberal",
    4: "Moderate",
    5: "Slightly conservative",
    6: "Conservative",
    7: "Extremely conservative",
}

INCOME_LABELS = {
    1: "Under $5,000", 2: "$5,000-9,999", 3: "$10,000-12,499",
    4: "$12,500-14,999", 5: "$15,000-17,499", 6: "$17,500-19,999",
    7: "$20,000-22,499", 8: "$22,500-24,999", 9: "$25,000-27,499",
    10: "$27,500-29,999", 11: "$30,000-34,999", 12: "$35,000-39,999",
    13: "$40,000-44,999", 14: "$45,000-49,999", 15: "$50,000-54,999",
    16: "$55,000-59,999", 17: "$60,000-64,999", 18: "$65,000-69,999",
    19: "$70,000-74,999", 20: "$75,000-79,999", 21: "$80,000-89,999",
    22: "$90,000-99,999", 23: "$100,000-109,999", 24: "$110,000-124,999",
    25: "$125,000-149,999", 26: "$150,000-174,999", 27: "$175,000-249,999",
    28: "$250,000 or more",
}

PRE_CHOICE_PARTY_LABELS = {
    10: "Democratic candidate selected (vote)",
    11: "Republican candidate selected (vote)",
    12: "Other candidate selected (vote)",
    20: "Democratic candidate selected (intent)",
    21: "Republican candidate selected (intent)",
    22: "Other candidate selected (intent)",
    30: "Democratic candidate selected (preference)",
    31: "Republican candidate selected (preference)",
    32: "Other candidate selected (preference)",
}

MAJOR_CANDIDATE_ORDER = ["Kamala Harris", "Donald Trump"]
AGE_GROUP_ORDER = ["18-29", "30-44", "45-64", "65+"]
EDUCATION_GROUP_ORDER = ["No college degree", "Bachelor's degree", "Graduate degree"]
INCOME_GROUP_ORDER = [
    "Lower income categories",
    "Middle income categories",
    "Higher income categories",
]
IDEOLOGY_ORDER = list(IDEOLOGY_LABELS.values())
