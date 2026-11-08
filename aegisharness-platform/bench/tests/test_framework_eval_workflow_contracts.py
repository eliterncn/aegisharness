"""Current AegisHarness workflow contracts freeze explicit actions and reject retired commands."""
import pytest

from bench.workflow_contracts import WorkflowContractError, resolve_workflow_contract


def _closure() -> dict[str, object]:
    return {
        "schema_version": "framework-eval-aegisharness-closure.v1",
        "max_stage_rework_cycles": 3,
        "stage_findings_prompt": "repair the failed native stage",
        "transitions": [],
    }

def resolve(commands):
    return resolve_workflow_contract(commands, profile_name="UNIFIED_EVALUATION", side="BASE", source_commit="a"*40, workflow_closure=_closure())

def test_workflow_chain_freezes_exact_commands_and_archive():
    commands=["/aegis:init", "/aegis:propose demo request.md", "/aegis:apply demo", "/aegis:archive demo"]
    result=resolve(commands)
    assert [s["command"] for s in result["steps"]] == commands
    assert "variant" not in result
    assert result["terminal"]["evidence_contract"] == "AEGISHARNESS_ARCHIVE"
    assert "REVIEW" not in result["goal_control"]["actions"]

def test_loop_is_terminal_and_keeps_exact_invocation():
    result=resolve(["/aegis:propose demo request.md --loop"])
    assert result["steps"][0]["artifact_contract"] == "AEGISHARNESS_ARCHIVE"
    assert result["steps"][0]["command"].endswith("--loop")


def test_literal_requirement_flags_do_not_turn_propose_into_archive():
    result = resolve(["/aegis:propose demo -- --loop --example", "/aegis:archive demo"])
    assert result["steps"][0]["artifact_contract"] == "AEGISHARNESS_PROPOSE"


def test_workspace_init_and_independent_unit_test_command_keep_feature_identity():
    result = resolve([
        "/aegis:init --workspace --repos ../service-a ../service-b",
        "/aegis:propose demo implement a requirement",
        "/aegis:ut --packages sample.service --concurrency 2",
        "/aegis:apply demo",
        "/aegis:archive demo --no-commit",
    ])
    assert result["feature"] == "demo"
    assert result["steps"][2]["artifact_contract"] == "UT"

@pytest.mark.parametrize("commands", [
 ["/aegis:review demo", "/aegis:archive demo"],
 ["/aegis:propose demo --workflow", "/aegis:archive demo"],
 ["/aegis:propose demo --loop", "/aegis:archive demo"],
 ["/aegis:apply one", "/aegis:archive two"],
 ["/aegis:apply demo"],
 ["/aegis:archive demo && echo bad"],
 ["/aegis:init --removed", "/aegis:archive demo"],
 ["/aegis:init --repos ../service", "/aegis:archive demo"],
 ["/aegis:propose demo --loop=false"],
 ["/aegis:archive demo --commit --no-commit"],
])
def test_invalid_or_retired_chains_are_rejected(commands):
    with pytest.raises(WorkflowContractError):
        resolve(commands)
