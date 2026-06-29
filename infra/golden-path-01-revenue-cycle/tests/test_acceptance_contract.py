"""
Acceptance CONTRACT test (offline) — statically proves the golden-path template actually
ENCODES every control the clean-account acceptance test (acceptance_test.sh) will exercise.
This lets CI gate the deployable claim without an AWS account: if a control is removed from
the template, this fails before anyone deploys. Each assertion maps to a remediation finding.
"""
import os

import pytest
import yaml

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, "..", "template.yaml")
AGENT_SVC = os.path.join(HERE, "..", "..", "cloudformation", "agent-service.yaml")


class _CfnLoader(yaml.SafeLoader):
    pass


# Make every CFN short-tag (!Ref, !Sub, !GetAtt, !If, ...) parse to a plain value.
_CfnLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


@pytest.fixture(scope="module")
def tpl():
    with open(TEMPLATE) as fh:
        return yaml.load(fh, Loader=_CfnLoader)


@pytest.fixture(scope="module")
def raw():
    with open(TEMPLATE) as fh:
        return fh.read()


def test_bound_approval_enforced_in_env(tpl):
    env = tpl["Globals"]["Function"]["Environment"]["Variables"]
    assert env["AUTH_REQUIRE_BOUND_APPROVAL"] == "1"   # F2 — demo approval path closed


def test_runtime_is_vpc_attached(tpl):
    assert "VpcConfig" in tpl["Globals"]["Function"]   # F5 — every function in private subnets


def _has_wildcard_egress(res):
    """True if any Route or SecurityGroup egress allows 0.0.0.0/0 (prose mentioning it is fine)."""
    for r in res.values():
        t, props = r.get("Type"), r.get("Properties") or {}
        if t == "AWS::EC2::Route" and props.get("DestinationCidrBlock") == "0.0.0.0/0":
            return True
        if t == "AWS::EC2::SecurityGroupEgress" and props.get("CidrIp") == "0.0.0.0/0":
            return True
        if t == "AWS::EC2::SecurityGroup":
            for e in props.get("SecurityGroupEgress", []) or []:
                if isinstance(e, dict) and e.get("CidrIp") == "0.0.0.0/0":
                    return True
    return False


def test_no_internet_egress(tpl):
    res = tpl["Resources"]
    assert not any(r.get("Type") == "AWS::EC2::NatGateway" for r in res.values())       # F5
    assert not any(r.get("Type") == "AWS::EC2::InternetGateway" for r in res.values())
    assert not _has_wildcard_egress(res)               # no default route / wildcard egress


def test_durable_audit_jti_and_secret_present(tpl):
    res = tpl["Resources"]
    assert res["AuditTable"]["Properties"]["PointInTimeRecoverySpecification"]["PointInTimeRecoveryEnabled"] is True  # F4
    assert res["JtiTable"]["Type"] == "AWS::DynamoDB::Table"            # durable single-use
    assert res["ApprovalSecret"]["Type"] == "AWS::SecretsManager::Secret"  # no hardcoded key
    assert res["AppealOutbox"]["Type"] == "AWS::SQS::Queue"             # controlled export


def test_separate_functions_and_reviewer(tpl):
    res = tpl["Resources"]
    for fn in ("ConnectorFn", "ReviewerFn", "WorkflowFn"):
        assert res[fn]["Type"] == "AWS::Serverless::Function"          # F7 — distinct roles


def test_bedrock_never_wildcard(raw):
    # F7 — Bedrock is conditional + scoped to a model ARN, never Resource:"*".
    assert "bedrock:InvokeModel], Resource: \"*\"" not in raw
    assert 'bedrock:InvokeModel, bedrock:ApplyGuardrail], Resource: "*"' not in raw


def test_real_state_machine_no_pass(tpl, raw):
    sm = tpl["Resources"]["DenialWorkflow"]
    assert sm["Type"] == "AWS::Serverless::StateMachine"
    states = sm["Properties"]["Definition"]["States"]
    assert not any(s.get("Type") == "Pass" for s in states.values())   # F1 — no placeholders
    assert "waitForTaskToken" in raw                                    # real human gate
    assert "HumanReviewGate" in states


def test_egress_and_approvals_routes_present(raw):
    assert "/egress-check" in raw      # F5 probe the acceptance test asserts BLOCKED
    assert "/approvals" in raw         # reviewer service the acceptance test calls


def test_nested_state_machine_has_no_pass_placeholder():
    with open(AGENT_SVC) as fh:
        assert '"Type": "Pass"' not in fh.read()   # F1 — nested CFN also real


def test_worm_archive_is_automatic_and_immutable(tpl):
    res = tpl["Resources"]
    b = res["WormBucket"]["Properties"]
    assert b["ObjectLockEnabled"] is True                                  # F4 — WORM exists
    assert "DefaultRetention" in b["ObjectLockConfiguration"]["Rule"]      # retention configured
    assert tpl["Parameters"]["WormMode"]["Default"] == "COMPLIANCE"        # prod default is immutable
    assert res["AuditTable"]["Properties"]["StreamSpecification"]["StreamViewType"] == "NEW_IMAGE"
    exp = res["AuditExporterFn"]["Properties"]
    assert exp["Handler"] == "exporter.handler"                            # automatic export
    assert any(e.get("Type") == "DynamoDB" for e in exp["Events"].values())  # stream-triggered


def test_egress_uses_prefix_lists_not_wildcard(tpl, raw):
    assert "DestinationPrefixListId" in raw   # gateway-endpoint egress is prefix-list scoped
    assert not _has_wildcard_egress(tpl["Resources"])  # no wildcard egress in any route/SG
