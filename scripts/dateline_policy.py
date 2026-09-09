#!/usr/bin/env python3
"""The ONE rule both dateline gates apply, and the ONE tolerance they apply it with.

⚠️ WHY THIS EXISTS. jsonld_dateline_gate and visible_dateline_gate each held their own
`GRACE_DAYS = 30` and their own `days > GRACE_DAYS` comparison. Two copies of a RULE, not
of a value: one reads the JSON-LD `dateModified`, the other the visible byline, and both
answer the same question — how far may a declared date lag the body's last real change.

That is drift-shaped by construction. Tune one to 45 and a page passes the visible check
while failing the JSON-LD one, with both describing the same underlying fact. Giving the
second gate "the same tolerance" by editing its own copy is a THIRD copy and moves the
failure rather than removing it.

So the rule lives here once, as a PREDICATE rather than a number. A gate asks this module
whether a lag is stale; it does not hold an opinion about staleness itself.

(Adopted from Crisp's "Two copies of a RULE drift the same way two copies of a fact do",
ops UPGRADES 2026-09-08 — where a renderer's dead-band and a describer's unconditional
maths disagreed on ordinary footage.)
"""

#: How far a declared date may lag the body's last real change before it is a lie.
GRACE_DAYS = 30

#: Vacuity floor shared by both gates: they survey the same corpus, so a reach that is
#: adequate for one is adequate for the other. Two numbers here would drift too.
MIN_PAGES = 50


def lag_days(declared, body_changed) -> int:
    """Days the declared date lags the body's last change. Negative = declared is ahead."""
    return (body_changed - declared).days


def is_stale(declared, body_changed) -> bool:
    """The single staleness decision. Both gates call this; neither reimplements it."""
    return lag_days(declared, body_changed) > GRACE_DAYS
