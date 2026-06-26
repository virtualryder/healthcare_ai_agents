from governance.grounding import verify_grounding

def test_grounded_text_passes():
    state = {"sources": [{"snippet": "CO-197 cites an absent authorization.",
                          "url": "https://payer.example.com/policy/auth-197"}],
             "claim": {"cpt": ["99214"], "billed": 312.00}}
    text = "The billed CPT 99214 service for $312.00 was denied under CO-197."
    rep = verify_grounding(text, state)
    assert rep.grounded, rep.to_audit_dict()

def test_fabricated_amount_flagged():
    state = {"claim": {"cpt": ["99214"], "billed": 312.00}}
    text = "We are owed $9,999.00 for this claim."
    rep = verify_grounding(text, state)
    assert not rep.grounded and rep.ungrounded_numbers

def test_fabricated_entity_flagged():
    state = {"claim": {"payer": "BlueChoice PPO"}}
    text = "Per Imaginary Health Plan policy, reprocess the claim."
    rep = verify_grounding(text, state)
    assert "Imaginary Health Plan" in rep.ungrounded_entities
