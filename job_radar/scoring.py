"""Weighted scoring engine for job-candidate fit."""

import logging
import re

from .profile_manager import DEFAULT_SCORING_WEIGHTS
from .staffing_firms import is_staffing_firm

log = logging.getLogger(__name__)


def score_job(job, profile: dict) -> dict:
    """Score a job result against a candidate profile.

    Returns a dict with overall score (1.0-5.0) and component breakdowns.
    """
    # Check dealbreakers first — hard disqualification
    dealbreaker_hit = _check_dealbreakers(job, profile)
    if dealbreaker_hit:
        return {
            "overall": 0.0,
            "components": {},
            "recommendation": "Dealbreaker",
            "dealbreaker": dealbreaker_hit,
        }

    scores = {}

    # 1. Stack/skill match (25%)
    scores["skill_match"] = _score_skill_match(job, profile)

    # 2. Title relevance (15%)
    scores["title_relevance"] = _score_title_relevance(job, profile)

    # 3. Seniority alignment (15%)
    scores["seniority"] = _score_seniority(job, profile)

    # 4. Location/arrangement fit (15%)
    scores["location"] = _score_location(job, profile)

    # 5. Domain relevance (10%)
    scores["domain"] = _score_domain(job, profile)

    # 6. Response likelihood (20%)
    scores["response"] = _score_response_likelihood(job)

    # Get weights from profile with fallback to defaults (defense-in-depth)
    weights = profile.get("scoring_weights", DEFAULT_SCORING_WEIGHTS)

    # Weighted total using configurable weights
    overall = (
        scores["skill_match"]["score"] * weights.get("skill_match", 0.25)
        + scores["title_relevance"]["score"] * weights.get("title_relevance", 0.15)
        + scores["seniority"]["score"] * weights.get("seniority", 0.15)
        + scores["location"]["score"] * weights.get("location", 0.15)
        + scores["domain"]["score"] * weights.get("domain", 0.10)
        + scores["response"]["score"] * weights.get("response_likelihood", 0.20)
    )

    # Staffing firm preference (post-scoring adjustment, NOT a weight component)
    staffing_pref = profile.get("staffing_preference", "neutral")
    if is_staffing_firm(job.company):
        if staffing_pref == "boost":
            overall = min(5.0, overall + 0.5)
            scores["staffing_note"] = "Staffing firm (boosted +0.5)"
        elif staffing_pref == "penalize":
            overall = max(1.0, overall - 1.0)
            scores["staffing_note"] = "Staffing firm (penalized -1.0)"
        # "neutral" = no adjustment, staffing firm treated same as direct employer

    # Compensation adjustment — penalize if below floor
    comp_penalty, comp_note = _check_comp_floor(job, profile)
    if comp_penalty:
        overall = max(1.0, overall - comp_penalty)
        scores["comp_note"] = comp_note

    # Parse confidence adjustment — demote low-confidence parses
    if hasattr(job, "parse_confidence") and job.parse_confidence == "low":
        overall = max(1.0, overall - 0.3)
        scores["parse_note"] = "Low parse confidence (freeform listing)"

    return {
        "overall": round(overall, 1),
        "components": scores,
        "recommendation": _recommendation(overall),
    }


def _recommendation(score: float) -> str:
    if score >= 4.0:
        return "Strong Recommend"
    elif score >= 3.5:
        return "Recommend"
    elif score >= 2.8:
        return "Worth Reviewing"
    elif score >= 2.0:
        return "Weak Match"
    else:
        return "Poor Match"


# ---------------------------------------------------------------------------
# Dealbreaker and compensation checks
# ---------------------------------------------------------------------------

def _check_dealbreakers(job, profile: dict) -> str | None:
    """Check if a job triggers any dealbreakers from the profile.

    Returns the dealbreaker reason string if hit, or None.
    """
    dealbreakers = profile.get("dealbreakers", [])
    if not dealbreakers:
        return None

    searchable = (job.title + " " + job.description + " " + job.company).lower()
    for db in dealbreakers:
        if db.lower() in searchable:
            return db

    return None


def _parse_salary_number(text: str) -> float | None:
    """Try to extract a numeric salary value from text.

    Returns annual equivalent in dollars, or None.
    """
    if not text or text == "Not listed":
        return None

    text = text.replace(",", "").strip()

    # Match patterns like "$120000", "$120k", "$60/hr"
    # Require at least one digit to avoid matching bare '.' or '$.'
    match = re.search(r'\$?(\d[\d.]*)\s*(?:k|K)', text)
    if match:
        return float(match.group(1)) * 1000

    match = re.search(r'\$?(\d[\d.]*)\s*/?\s*(?:hr|hour)', text)
    if match:
        return float(match.group(1)) * 2080  # hourly to annual

    match = re.search(r'\$?(\d[\d.]*)', text)
    if match:
        val = float(match.group(1))
        if val < 500:
            return val * 2080  # likely hourly
        elif val < 1000:
            return val * 1000  # likely in thousands
        return val

    return None


def _check_comp_floor(job, profile: dict) -> tuple[float, str]:
    """Check if job salary is below the candidate's compensation floor.

    Returns (penalty_amount, note_string). penalty is 0.0 if no issue.
    """
    comp_floor = profile.get("comp_floor")
    if not comp_floor:
        return 0.0, ""

    salary_val = _parse_salary_number(job.salary)
    if salary_val is None:
        return 0.0, ""

    if salary_val < comp_floor:
        gap_pct = round((comp_floor - salary_val) / comp_floor * 100)
        note = f"Below comp floor: ${salary_val:,.0f} vs ${comp_floor:,.0f} floor ({gap_pct}% gap)"
        # Bigger penalty for larger gaps
        if gap_pct > 30:
            return 1.5, note
        elif gap_pct > 15:
            return 1.0, note
        else:
            return 0.5, note

    return 0.0, ""


# ---------------------------------------------------------------------------
# Skill matching with word boundaries
# ---------------------------------------------------------------------------

_NORM_RE = re.compile(r'[\.\-\s]+')


def _normalize_skill(s: str) -> str:
    """Strip separator punctuation (dots, hyphens, spaces), lowercase.

    Preserves meaningful punctuation: # in C#, + in C++.

    Examples:
        "Node.js"   -> "nodejs"
        "node js"   -> "nodejs"
        ".NET"      -> "net"
        "C#"        -> "c#"
        "C++"       -> "c++"
    """
    return _NORM_RE.sub('', s.lower())


# Alternate forms / abbreviations for common skills
_SKILL_VARIANTS = {
    "business analysis": ["business analyst", "ba ", "ba/", "business analysis"],
    "requirements elicitation": ["requirements", "elicitation", "requirement gathering"],
    "uat": ["uat", "user acceptance testing", "user acceptance"],
    "agile": ["agile", "agile methodology"],
    "scrum": ["scrum", "scrum master", "scrum team"],
    ".net": [".net", "dotnet", "dot net"],
    "c#": ["c#", "csharp", "c sharp"],
    "node.js": ["node.js", "nodejs", "node js"],
    "react": ["react", "reactjs", "react.js"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "typescript": ["typescript", "ts "],
    "rpa": ["rpa", "robotic process automation"],
    "uipath": ["uipath", "ui path"],
    "sap": ["sap"],
    "procure-to-pay": ["procure-to-pay", "procure to pay", "p2p"],
    "vertex tax engine": ["vertex tax engine", "vertex tax", "vertex"],
    "stakeholder engagement": ["stakeholder engagement", "stakeholder management", "stakeholder"],
    "backlog management": ["backlog management", "backlog grooming", "backlog refinement", "backlog"],
    "process automation": ["process automation", "automation"],
    "blue prism": ["blue prism", "blueprism"],
    "erp": ["erp"],
    "safe": ["safe ", "safe/", "scaled agile"],
    "jira": ["jira"],
    "python": ["python", "python3", "py3"],
    "go": ["go", "golang"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angular.js", "angularjs"],
    "kubernetes": ["kubernetes", "k8s"],
    "k8s": ["k8s", "kubernetes"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "docker": ["docker", "containerization"],
    "terraform": ["terraform", "tf"],
    "sql": ["sql", "structured query language"],
    "nosql": ["nosql", "no-sql"],
    "rest": ["rest", "restful", "rest api", "restful api"],
    "graphql": ["graphql", "graph ql"],
    "ci/cd": ["ci/cd", "ci cd", "cicd", "continuous integration", "continuous deployment"],
}

_SKILL_VARIANTS_NORMALIZED: dict[str, list[str]] = {
    _normalize_skill(k): v for k, v in _SKILL_VARIANTS.items()
}

# Skills that need word-boundary matching to avoid false positives.
# Short or common words that could match unrelated text.
_BOUNDARY_SKILLS = {"go", "r", "c", "ai", "ml", "qa", "pm", "ci", "cd", "ts", "js"}


_WORD_ONLY_RE = re.compile(r'^\w+$')


def _build_skill_pattern(skill: str) -> re.Pattern:
    """Build a regex pattern for a skill, using word boundaries for short/ambiguous terms.

    Word boundaries are applied only when the skill is short (<=2 chars) AND
    consists entirely of word characters. Skills containing non-word characters
    like # (C#) or + (C++) are unambiguous and don't need boundary protection.
    """
    escaped = re.escape(skill.lower())
    needs_boundary = (
        skill.lower() in _BOUNDARY_SKILLS
        or (len(skill) <= 2 and bool(_WORD_ONLY_RE.match(skill)))
    )
    if needs_boundary:
        return re.compile(rf'\b{escaped}\b', re.IGNORECASE)
    return re.compile(re.escape(skill.lower()), re.IGNORECASE)


def _skill_in_text(skill: str, text: str) -> bool:
    """Check if a skill (or any of its variants) appears in text using word-boundary matching."""
    # Direct match with boundary awareness
    pattern = _build_skill_pattern(skill)
    if pattern.search(text):
        return True

    # Check known variants (normalized key lookup)
    variants = _SKILL_VARIANTS_NORMALIZED.get(_normalize_skill(skill), [])
    for v in variants:
        v_pattern = _build_skill_pattern(v)
        if v_pattern.search(text):
            return True

    return False


# ---------------------------------------------------------------------------
# Component scorers
# ---------------------------------------------------------------------------

def _score_skill_match(job, profile: dict) -> dict:
    """Score based on how many core skills appear in the job description/title."""
    core_skills = profile.get("core_skills", [])
    secondary_skills = profile.get("secondary_skills", [])
    searchable = (job.title + " " + job.description + " " + job.company).lower()

    matched_core = [s for s in core_skills if _skill_in_text(s, searchable)]
    matched_secondary = [s for s in secondary_skills if _skill_in_text(s, searchable)]

    if not core_skills:
        ratio = 0.0
    else:
        # Core matches count fully, secondary count at 50%
        ratio = (len(matched_core) + len(matched_secondary) * 0.5) / len(core_skills)

    # Map ratio to 1.0-5.0 scale
    score = min(5.0, max(1.0, 1.0 + ratio * 4.0))

    return {
        "score": round(score, 1),
        "matched_core": matched_core,
        "matched_secondary": matched_secondary,
        "ratio": f"{len(matched_core)}/{len(core_skills)} core",
    }


def _score_title_relevance(job, profile: dict) -> dict:
    """Score how well the job title matches the candidate's target titles."""
    target_titles = [t.lower() for t in profile.get("target_titles", [])]
    job_title = job.title.lower()

    if not target_titles:
        return {"score": 3.0, "reason": "No target titles set"}

    # Exact match (after lowering)
    if job_title in target_titles:
        return {"score": 5.0, "reason": f"Exact title match: {job.title}"}

    # Check if any target title is contained in the job title or vice versa
    for tt in target_titles:
        if tt in job_title or job_title in tt:
            return {"score": 4.5, "reason": f"Close title match: '{job.title}' ~ '{tt}'"}

    # Word overlap scoring — how many significant words from target titles appear
    target_words = set()
    for tt in target_titles:
        target_words.update(w for w in tt.split() if len(w) >= 3)

    job_words = set(w for w in job_title.split() if len(w) >= 3)

    if not target_words:
        return {"score": 3.0, "reason": "No significant title words to match"}

    overlap = target_words & job_words
    ratio = len(overlap) / len(target_words) if target_words else 0

    if ratio >= 0.6:
        score = 4.0
        reason = f"Good title overlap: {', '.join(overlap)}"
    elif ratio >= 0.3:
        score = 3.0
        reason = f"Partial title overlap: {', '.join(overlap)}"
    elif overlap:
        score = 2.0
        reason = f"Weak title overlap: {', '.join(overlap)}"
    else:
        score = 1.5
        reason = f"No title match (job: '{job.title}')"

    return {"score": round(score, 1), "reason": reason}


def _score_seniority(job, profile: dict) -> dict:
    """Score seniority alignment based on title keywords and years."""
    level = profile.get("level", "mid")
    years = profile.get("years_experience", 0)
    title_lower = job.title.lower()
    desc_lower = job.description.lower()
    combined = title_lower + " " + desc_lower

    # Detect job level from title
    job_level = "unknown"
    if any(w in title_lower for w in ["junior", "jr.", "jr ", "entry"]):
        job_level = "junior"
    elif any(w in title_lower for w in ["senior", "sr.", "sr ", "lead", "staff", "principal"]):
        job_level = "senior"
    elif any(w in title_lower for w in ["mid", "ii", "level 2"]):
        job_level = "mid"

    # Parse years requirement from description
    years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)', combined)
    required_years = int(years_match.group(1)) if years_match else None

    # Score logic
    score = 3.0  # default neutral

    # Level alignment
    level_map = {"junior": 1, "mid": 2, "senior": 3, "principal": 4}
    candidate_level_num = level_map.get(level, 2)
    job_level_num = level_map.get(job_level, 2)
    level_diff = abs(candidate_level_num - job_level_num)

    if job_level == "unknown":
        score = 3.5  # can't tell, slight benefit of doubt
    elif level_diff == 0:
        score = 5.0
    elif level_diff == 1:
        score = 3.5
    else:
        score = 1.5

    # Years adjustment
    if required_years is not None:
        if years >= required_years:
            score = min(5.0, score + 0.5)
        elif years >= required_years - 1:
            pass  # close enough
        else:
            score = max(1.0, score - 1.0)

    reason = f"Candidate: {level} ({years}yr)"
    if job_level != "unknown":
        reason += f" | Job: {job_level}"
    if required_years is not None:
        reason += f" (requires {required_years}+ yr)"

    return {"score": round(score, 1), "reason": reason}


def _score_location(job, profile: dict) -> dict:
    """Score location and work arrangement fit."""
    candidate_arrangements = [a.lower() for a in profile.get("arrangement", [])]
    candidate_location = profile.get("location", "").lower()
    target_market = profile.get("target_market", "").lower()

    job_arrangement = job.arrangement.lower()
    job_location = job.location.lower()

    # If arrangement is unknown, check description for hints
    if job_arrangement == "unknown":
        desc_lower = job.description.lower()
        all_text = f"{job_location} {desc_lower}"
        if "hybrid" in all_text:
            job_arrangement = "hybrid"
        elif "remote" in all_text:
            job_arrangement = "remote"
        elif "on-site" in all_text or "onsite" in all_text:
            job_arrangement = "onsite"

    score = 3.0
    reasons = []

    # Arrangement match
    if job_arrangement == "remote" and "remote" in candidate_arrangements:
        score = 5.0
        reasons.append("Remote match")
    elif job_arrangement == "hybrid" and "hybrid" in candidate_arrangements:
        if _locations_match(job_location, candidate_location, target_market):
            score = 5.0
            reasons.append("Hybrid in target area")
        else:
            score = 2.5
            reasons.append("Hybrid but wrong location")
    elif job_arrangement == "onsite":
        if _locations_match(job_location, candidate_location, target_market):
            if "onsite" in candidate_arrangements:
                score = 4.0
                reasons.append("Onsite in target area")
            else:
                score = 2.0
                reasons.append("Onsite only, candidate prefers remote/hybrid")
        else:
            score = 1.0
            reasons.append("Onsite in wrong location")
    elif job_arrangement == "unknown":
        if "remote" in job_location:
            score = 4.5
            reasons.append("Likely remote based on location text")
        else:
            score = 3.0
            reasons.append("Arrangement unclear")

    return {"score": round(score, 1), "reason": ", ".join(reasons) if reasons else "N/A"}


def _locations_match(job_loc: str, candidate_loc: str, target_market: str) -> bool:
    """Check if job location matches candidate location or target market."""
    for loc in [candidate_loc, target_market]:
        parts = [p.strip().lower() for p in loc.replace(",", " ").split() if len(p) > 1]
        for part in parts:
            if part in job_loc:
                return True
    return False


def _score_domain(job, profile: dict) -> dict:
    """Score domain/industry relevance."""
    domains = profile.get("domain_expertise", [])
    searchable = (job.title + " " + job.description + " " + job.company).lower()

    matched = [d for d in domains if d.lower() in searchable]

    if not domains:
        return {"score": 3.0, "matched": [], "reason": "No domain preferences set"}

    if matched:
        ratio = len(matched) / len(domains)
        score = min(5.0, 3.0 + ratio * 2.0)
        return {"score": round(score, 1), "matched": matched, "reason": f"Matched: {', '.join(matched)}"}

    return {"score": 3.0, "matched": [], "reason": "No domain overlap detected"}


def _score_response_likelihood(job) -> dict:
    """Score how likely the candidate is to get a response."""
    score = 3.0
    reasons = []

    # Direct email apply
    if job.apply_info and ("mailto:" in job.apply_info or "@" in job.apply_info):
        score = min(5.0, score + 1.0)
        reasons.append("Direct email apply")

    # HN Hiring source (small teams, human review)
    if job.source == "HN Hiring":
        score = min(5.0, score + 0.5)
        reasons.append("HN Hiring (small team, direct)")

    # RemoteOK tends to be smaller companies
    if job.source == "RemoteOK":
        score = min(5.0, score + 0.3)
        reasons.append("RemoteOK listing")

    # Company size indicators in description
    desc_lower = job.description.lower()
    if any(w in desc_lower for w in ["small team", "startup", "early stage", "founding", "pre-seed", "seed"]):
        score = min(5.0, score + 0.5)
        reasons.append("Small team/startup")

    if any(w in desc_lower for w in ["fortune 500", "enterprise", "large organization"]):
        score = max(1.0, score - 0.5)
        reasons.append("Large enterprise (lower response rate)")

    score = min(5.0, max(1.0, score))
    likelihood = "High" if score >= 4.0 else "Medium" if score >= 2.5 else "Low"

    return {
        "score": round(score, 1),
        "likelihood": likelihood,
        "reason": "; ".join(reasons) if reasons else "Standard application process",
    }
