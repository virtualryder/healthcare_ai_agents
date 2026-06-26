from governance.accessibility.wcag import check_html, check_plain_language

def test_missing_alt_flagged():
    rep = check_html('<p>Your plan <img src="card.png"></p>')
    assert not rep.passes

def test_plain_language_simple_passes():
    rep = check_plain_language("Your claim was denied. We will appeal it for you. You owe nothing now.")
    assert rep.passes

def test_dense_language_flagged():
    dense = ("Notwithstanding the aforementioned adjudication, the determination "
             "regarding reimbursement eligibility necessitates comprehensive substantiation "
             "of medical necessity pursuant to applicable coverage determinations.")
    rep = check_plain_language(dense)
    assert not rep.passes
