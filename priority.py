"""
Priority scoring for complaints.

Priority is derived from two signals, similar in spirit to how the source
papers separate "category" (what the problem is) from severity triage,
which neither paper automates but both flag as useful future work:

1. Category severity - some categories are inherently higher-risk
   (e.g. a damaged road or exposed live wire is more dangerous than a
   general inquiry).
2. Urgency keywords - words in the free-text description that signal
   immediate danger, injury, or vulnerable people affected.

This is intentionally simple and transparent (a rule-based score, not a
trained model) so authorities can see exactly why something was flagged
High and can always override it by hand.
"""

CATEGORY_BASE_SCORE = {
    "Storm Water Drain": 3,
    "Road Maintenance": 3,
    "Street Light / Electrical": 3,
    "Sewage / Sanitation": 2,
    "Water Supply": 2,
    "Stray Animals": 2,
    "Solid Waste": 1,
    "Parks & Trees": 1,
    "Encroachment": 1,
    "Others": 0,
}

URGENT_KEYWORDS = [
    "danger", "dangerous", "accident", "injur", "injury", "injured",
    "fire", "collapse", "collapsed", "electrocut", "spark", "sparking",
    "child", "children", "school", "hospital", "emergency", "urgent",
    "life-threatening", "death", "died", "drowned", "drowning", "bit", "bite",
    "exposed wire", "live wire", "gas leak", "explosion",
]


def score_priority(category: str, description: str) -> str:
    """Return 'High', 'Medium', or 'Low'."""
    score = CATEGORY_BASE_SCORE.get(category, 0)

    text = (description or "").lower()
    keyword_hits = sum(1 for kw in URGENT_KEYWORDS if kw in text)
    score += keyword_hits * 2

    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

# Community upvotes can escalate a complaint's priority tier - enough
# citizens flagging the same issue as important is itself a severity
# signal, on top of the category/keyword rule-based score above.
UPVOTES_TO_ESCALATE_LOW_TO_MEDIUM = 10
UPVOTES_TO_ESCALATE_MEDIUM_TO_HIGH = 20


def effective_priority(priority: str, upvotes: int, locked: bool = False) -> str:
    """The priority actually used for sorting/display everywhere in the
    app: the stored (auto-scored or authority-set) priority, bumped up a
    tier if citizen upvotes have crossed a threshold.

    If `locked` is True, upvote escalation is skipped entirely and the
    stored priority is returned as-is. An authority sets this by ticking
    "Lock priority" when they manually correct a priority from the
    dashboard - without it, a complaint sitting on a lot of old upvotes
    would immediately escalate itself right back up the moment an
    authority tried to lower it, silently undoing their correction.
    """
    if locked:
        return priority
    upvotes = upvotes or 0
    if priority == "Low" and upvotes >= UPVOTES_TO_ESCALATE_LOW_TO_MEDIUM:
        priority = "Medium"
    if priority == "Medium" and upvotes >= UPVOTES_TO_ESCALATE_MEDIUM_TO_HIGH:
        priority = "High"
    return priority
