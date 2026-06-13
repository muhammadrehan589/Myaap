"""Compliance Service — Dataset-driven compliance checking.

Uses RAG matches against the Capability Library to determine PASS/FAIL.
Identifies compliance gaps: missing certifications and experience areas.
"""

from services.dataset_service import get_capability_records

COMPLIANCE_THRESHOLD = 0.75


def check_compliance(requirements: list[str], rag_matches: list[dict]) -> dict:
    """Evaluate compliance based on RAG similarity scores against the Capability Library.

    PASS if the best RAG match score >= threshold, otherwise FAIL.
    Identifies missing certifications and experience gaps from the dataset.
    """
    results = []
    for req, match in zip(requirements, rag_matches):
        status = "PASS" if match["score"] >= COMPLIANCE_THRESHOLD else "FAIL"
        results.append({
            "requirement": req,
            "status": status,
            "evidence": match["evidence"],
            "record_id": match.get("record_id", ""),
        })

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)
    score = round((passed / total) * 100, 1) if total > 0 else 0

    # Identify gaps from dataset
    capabilities = get_capability_records()
    all_domains = set(r["domain"] for r in capabilities if r["domain"])
    matched_domains = set()
    for m in rag_matches:
        if m.get("record_id"):
            for cap in capabilities:
                if cap["cap_id"] == m["record_id"]:
                    matched_domains.add(cap["domain"])

    missing_domains = sorted(all_domains - matched_domains)

    # Identify failed requirements as compliance gaps
    compliance_gaps = [
        {"requirement": r["requirement"], "reason": "No sufficient capability match found"}
        for r in results if r["status"] == "FAIL"
    ]

    # Collect certifications from matched records
    matched_certs = set()
    for m in rag_matches:
        if m.get("record_id"):
            for cap in capabilities:
                if cap["cap_id"] == m["record_id"] and cap["certification"] != "N/A":
                    matched_certs.add(cap["certification"])

    all_certs = set(r["certification"] for r in capabilities
                    if r["certification"] and r["certification"] != "N/A")
    missing_certs = sorted(all_certs - matched_certs)

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": score,
        "results": results,
        "missing_certifications": missing_certs,
        "compliance_gaps": compliance_gaps,
    }
