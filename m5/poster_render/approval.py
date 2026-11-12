"""Final export gate. Drafts never create approval records."""
from creative_core.validation import require
from creative_core import fingerprint
from .scene import render_identity


def check_export(doc, policy, engine, receipt=None, draft=True):
    identity = render_identity(doc, policy, engine)
    if not draft:
        require(bool(doc["approvals"]), "final export requires document approval")
        require(all(a["fingerprint"] == fingerprint(doc) for a in doc["approvals"]),
                "final export refuses stale approval")
        require(isinstance(receipt, dict) and set(receipt) == {"identity", "reviewer"}
                and receipt["identity"] == identity and isinstance(receipt["reviewer"], str)
                and receipt["reviewer"].strip(), "final export requires exact render-profile approval")
    return {"render_identity": identity, "approved": not draft, "draft": draft}
