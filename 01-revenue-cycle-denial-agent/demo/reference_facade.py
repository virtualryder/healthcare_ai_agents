"""
Reference system-of-record façade — a tiny, dependency-free HTTP service that answers the
connector methods Agent 01 uses, so the LIVE connector path (CONNECTOR_MODE=live) can be
exercised end-to-end with no real EHR/clearinghouse/payer and no API key.

The platform's LiveHttpConnector POSTs JSON kwargs to `{<KIND>_BASE_URL}/{method}` and expects
JSON back. Point every `*_BASE_URL` at this façade for a realistic, non-mock round-trip; swap the
URL for the customer's real FHIR/X12 gateway to go live — the agent code does not change. The
payloads mirror the deterministic fixtures (synthetic, non-PHI).
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# method -> handler(kwargs) -> payload   (synthetic, non-PHI; mirrors the fixtures)
ROUTES = {
    "get_claim": lambda a: {"claim_ref": a.get("claim_ref", "CLM-2026-55810"), "status": "Denied",
                            "payer": "BlueChoice PPO", "billed": 312.00, "allowed": 0.0,
                            "cpt": ["99214"], "icd10": ["E11.9", "I10"], "service_date": "2026-06-12",
                            "denial_codes": ["CO-197"], "account_ref": "ACCT-77120", "encounter_ref": "ENC-88231"},
    "get_account": lambda a: {"account_ref": a.get("account_ref", "ACCT-77120"), "balance": 248.00,
                              "financial_class": "Commercial", "plan": "BlueChoice PPO"},
    "validate_claim": lambda a: {"claim_ref": a.get("claim_ref"), "clean": False,
                                 "edits": [{"edit": "CO-197", "severity": "high",
                                            "description": "Precertification/authorization absent."}]},
    "check_claim_status": lambda a: {"claim_ref": a.get("claim_ref"), "x12": "277",
                                     "status": "Denied", "denial_codes": ["CO-197"]},
    "validate_codes": lambda a: {"cpt": a.get("cpt", []), "icd10": a.get("icd10", []),
                                 "ncci_edits": [], "mue_violations": [], "valid": True},
    "check_medical_necessity": lambda a: {"cpt": a.get("cpt", []), "icd10": a.get("icd10", []),
                                          "policy": "LCD-L34567", "supported": True,
                                          "source": "CMS LCD/NCD coverage database"},
    "get_clinical_docs": lambda a: {"encounter_ref": a.get("encounter_ref", "ENC-88231"),
                                    "documents": [{"doc_id": "DOC-1", "type": "Progress Note", "signed": True,
                                                   "snippet": "Diabetes follow-up; A1c reviewed."}],
                                    "missing_for_billing": []},
    "search_policy": lambda a: [{"doc_id": "PAYER-MED-197",
                                 "title": "Authorization Requirements — Office & Outpatient Services",
                                 "snippet": "CO-197 denials cite an absent precertification or authorization for the billed service.",
                                 "url": "https://payer.example.com/policy/auth-197", "effective": "2026-01-01"}],
    "submit_appeal": lambda a: {"appeal_ref": "APL-2026-1180", "claim_ref": a.get("claim_ref"),
                                "level": a.get("level", 1), "status": "Submitted", "decision_due": "2026-07-15"},
    "update_case": lambda a: {"case_ref": a.get("case_ref", "CASE-30021"),
                              "status": a.get("status", "Updated"), "note_added": True},
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def do_POST(self):
        method = self.path.rstrip("/").rsplit("/", 1)[-1]
        n = int(self.headers.get("Content-Length", 0))
        kwargs = json.loads(self.rfile.read(n) or b"{}")
        fn = ROUTES.get(method)
        body = fn(kwargs) if fn else {"error": f"unknown method {method!r}"}
        payload = json.dumps(body).encode()
        self.send_response(200 if fn else 404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)


def serve(host: str = "127.0.0.1", port: int = 0) -> HTTPServer:
    """Start the façade; returns the running server (use server.server_address for the port)."""
    httpd = HTTPServer((host, port), Handler)
    Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


if __name__ == "__main__":
    s = serve(port=8799)
    print(f"reference façade on http://{s.server_address[0]}:{s.server_address[1]} — Ctrl-C to stop")
    try:
        import time
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        s.shutdown()
