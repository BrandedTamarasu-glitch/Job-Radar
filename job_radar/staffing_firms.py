"""Known staffing/consulting firms for response likelihood scoring."""

STAFFING_FIRMS = [
    "motion recruitment",
    "k-tek",
    "k-tek resourcing",
    "divihn",
    "divihn integration",
    "robert half",
    "randstad",
    "teksystems",
    "tek systems",
    "insight global",
    "accenture federal",
    "slalom",
    "amentum",
    "hays",
    "adecco",
    "manpower",
    "manpowergroup",
    "kelly services",
    "kforce",
    "staffing",
    "apex systems",
    "modis",
    "collabera",
    "infosys bpo",
    "cognizant",
    "wipro",
    "hcl",
    "tata consultancy",
    "acl digital",
    "griffin global",
    "cybercoders",
    "jobot",
    "dice staffing",
    "experis",
    "aerotek",
    "beacon hill",
    "judge group",
    "horizontal talent",
    "brooksource",
    "revature",
    "smoothstack",
]


def is_staffing_firm(company_name: str) -> bool:
    """Check if a company name matches a known staffing firm."""
    name_lower = company_name.lower().strip()
    for firm in STAFFING_FIRMS:
        if firm in name_lower or name_lower in firm:
            return True
    return False
