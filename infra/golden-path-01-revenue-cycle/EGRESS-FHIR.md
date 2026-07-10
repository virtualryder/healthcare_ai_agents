# Locked egress for the real FHIR connector (HAPI FHIR R4)

*How HPP answers the CISO question "what stops the agent from calling arbitrary
endpoints?" for its one real external data source. The denial agent grounds its
appeal reasoning on **real** clinical documents read from the public **HAPI FHIR R4**
test server — reached through the governed MCP gateway and **only** through a
locked-down egress path.*

## The control

`egress-fhir.yaml` provisions an **AWS Network Firewall** whose stateful policy is
**default-deny** and allow-lists exactly one FQDN:

```
ALLOW  TLS_SNI / HTTP_HOST  ->  hapi.fhir.org
DROP   everything else       (aws:drop_established + aws:alert_established)
```

Every denied egress attempt is logged (ALERT) to `/hpp-01/<env>/egress-firewall`, so
the allow-list is not just asserted — a reviewer can see the drops. This is the
`UnexpectedEgressBlocked` signal wired in `infra/cloudformation/security-alarms.yaml`.

## Why this connector is safe to run

- **Read-only.** The connector implements only FHIR **reads** (`get_patient_summary`,
  `get_encounter`, `get_clinical_docs`). Any write (`draft_note`, `submit_claim`,
  `submit_appeal`, …) raises — writes target the customer's **validated** EHR /
  clearinghouse and stay **human-gated**. See `platform_core/hpp_agent_platform/connectors/fhir.py`.
- **Synthetic / de-identified.** The public HAPI test server holds only test data, so
  the connector needs **no BAA**. PHI masking still runs downstream on returned text —
  the control is exercised, not assumed (`test_fhir_connector.py`).
- **Governed.** Reads flow through the MCP gateway: deny-by-default authorization
  (agent grant ∩ user entitlement), a scoped per-call token, and an append-only masked
  audit record. Proven by `01-revenue-cycle-denial-agent/tests/test_fhir_connector.py`.

## Enabling the real connector

```bash
# Offline / CI (default): fixtures, no network.
pytest 01-revenue-cycle-denial-agent/tests/test_fhir_connector.py -q

# Opt-in live smoke against the real server:
RUN_LIVE_FHIR=1 pytest 01-revenue-cycle-denial-agent/tests/test_fhir_connector.py -q

# Point an agent run at the real source:
CONNECTOR_MODE=live EHR_SOURCE=hapifhir  # -> HapiFhirEhrConnector
# Customer variant (HealthLake / payer FHIR under a BAA): set EHR_BASE_URL + EHR_API_KEY
# and change AllowedFqdn in egress-fhir.yaml to that endpoint. Same control, same code.
```

## Wiring the firewall

Deploy `egress-fhir.yaml` into the golden-path-01 VPC, put the firewall endpoint in a
dedicated firewall subnet (one per AZ), and route the connector subnet's `0.0.0.0/0`
through the firewall endpoint, then to NAT/IGW. The connector can now reach
`hapi.fhir.org` and nothing else; every other destination is dropped and alerted.

> The regulated path is identical: swap `AllowedFqdn` (and `EHR_BASE_URL`) to the
> customer's HealthLake / payer FHIR endpoint under a BAA. The allow-list of one FQDN
> is the pattern — the data source behind it is a configuration choice.
