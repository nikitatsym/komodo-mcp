"""Integration tests — an agent works with Komodo entirely through MCP tools.

The test simulates a realistic agent workflow:
1. Check connection → 2. CRUD servers →
3. Deployments lifecycle → 4. Stacks lifecycle →
5. Builds, repos, procedures, actions →
6. Variables, tags, alerters →
7. Users, groups, permissions →
8. Batch operations → 9. Docker cleanup → 10. Export TOML
"""

import pytest

from tests.conftest import KOMODO_URL


def _id(result: dict) -> str:
    """Extract id from Komodo API response (handles _id.$oid and id)."""
    if "id" in result:
        return result["id"]
    raw = result.get("_id", "")
    return raw.get("$oid", raw) if isinstance(raw, dict) else raw


@pytest.mark.usefixtures("configure_env")
class TestAgentWorkflow:
    """Sequential test simulating a full agent workflow."""

    # Shared state
    server_id = None
    deployment_id = None
    stack_id = None
    build_id = None
    repo_id = None
    procedure_id = None
    action_id = None
    tag_id = None
    alerter_id = None
    user_group_id = None
    service_user_id = None

    # ── 1. Connection & General ───────────────────────────────

    def test_01_version(self, agent):
        result = agent.call("get_version")
        assert "version" in result

    def test_02_core_info(self, agent):
        result = agent.call("get_core_info")
        assert "title" in result

    # ── 2. Servers ────────────────────────────────────────────

    def test_10_create_server(self, agent):
        import time
        result = agent.call("create_server",
            name="test-server",
            config={"address": "https://komodo-periphery:8120", "enabled": True},
        )
        assert result["name"] == "test-server"
        TestAgentWorkflow.server_id = _id(result)
        # Wait for periphery connection
        for _ in range(10):
            state = agent.call("get_server_state", server="test-server")
            if state.get("status") == "Ok":
                break
            time.sleep(2)

    def test_11_list_servers(self, agent):
        result = agent.call("list_servers")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_12_get_server(self, agent):
        result = agent.call("get_server", server="test-server")
        assert result["name"] == "test-server"

    def test_13_get_servers_summary(self, agent):
        result = agent.call("get_servers_summary")
        assert "total" in result

    def test_14_rename_server(self, agent):
        result = agent.call("rename_server",
            id=TestAgentWorkflow.server_id,
            name="test-server-renamed",
        )
        assert result.get("success", True)
        # Verify via get
        srv = agent.call("get_server", server="test-server-renamed")
        assert srv["name"] == "test-server-renamed"

    def test_15_rename_server_back(self, agent):
        agent.call("rename_server",
            id=TestAgentWorkflow.server_id,
            name="test-server",
        )

    # ── 3. Deployments ────────────────────────────────────────

    def test_20_create_deployment(self, agent):
        result = agent.call("create_deployment",
            name="test-deploy",
            config={
                "server_id": TestAgentWorkflow.server_id,
                "image": {"type": "Image", "params": {"image": "nginx:alpine"}},
            },
        )
        assert result["name"] == "test-deploy"
        TestAgentWorkflow.deployment_id = _id(result)

    def test_21_list_deployments(self, agent):
        result = agent.call("list_deployments")
        assert isinstance(result, list)

    def test_22_get_deployment(self, agent):
        result = agent.call("get_deployment", deployment="test-deploy")
        assert result["name"] == "test-deploy"

    def test_23_get_deployments_summary(self, agent):
        result = agent.call("get_deployments_summary")
        assert "total" in result

    def test_24_deploy(self, agent):
        result = agent.call("deploy", deployment="test-deploy")
        assert result is not None

    def test_25_get_deployment_log(self, agent):
        import time
        for _ in range(10):
            try:
                result = agent.call("get_deployment_log", deployment="test-deploy", tail=10)
                assert result is not None
                return
            except Exception:
                time.sleep(3)
        result = agent.call("get_deployment_log", deployment="test-deploy", tail=10)
        assert result is not None

    def test_26_stop_deployment(self, agent):
        agent.call("stop_deployment", deployment="test-deploy")

    def test_27_destroy_deployment(self, agent):
        agent.call("destroy_deployment", deployment="test-deploy")

    def test_28_delete_deployment(self, agent):
        import time
        for _ in range(5):
            try:
                agent.call("delete_deployment", id=TestAgentWorkflow.deployment_id)
                return
            except Exception:
                time.sleep(2)
        agent.call("delete_deployment", id=TestAgentWorkflow.deployment_id)

    # ── 4. Stacks ─────────────────────────────────────────────

    def test_30_create_stack(self, agent):
        result = agent.call("create_stack",
            name="test-stack",
            config={"server_id": TestAgentWorkflow.server_id},
        )
        assert result["name"] == "test-stack"
        TestAgentWorkflow.stack_id = _id(result)

    def test_31_list_stacks(self, agent):
        result = agent.call("list_stacks")
        assert isinstance(result, list)

    def test_32_get_stack(self, agent):
        result = agent.call("get_stack", stack="test-stack")
        assert result["name"] == "test-stack"

    def test_33_delete_stack(self, agent):
        agent.call("delete_stack", id=TestAgentWorkflow.stack_id)

    # ── 5. Builds, Repos, Procedures, Actions ─────────────────

    def test_40_create_build(self, agent):
        result = agent.call("create_build", name="test-build")
        assert result["name"] == "test-build"
        TestAgentWorkflow.build_id = _id(result)

    def test_41_delete_build(self, agent):
        agent.call("delete_build", id=TestAgentWorkflow.build_id)

    def test_42_create_repo(self, agent):
        result = agent.call("create_repo", name="test-repo")
        assert result["name"] == "test-repo"
        TestAgentWorkflow.repo_id = _id(result)

    def test_43_delete_repo(self, agent):
        agent.call("delete_repo", id=TestAgentWorkflow.repo_id)

    def test_44_create_procedure(self, agent):
        result = agent.call("create_procedure", name="test-procedure")
        assert result["name"] == "test-procedure"
        TestAgentWorkflow.procedure_id = _id(result)

    def test_45_delete_procedure(self, agent):
        agent.call("delete_procedure", id=TestAgentWorkflow.procedure_id)

    def test_46_create_action(self, agent):
        result = agent.call("create_action", name="test-action")
        assert result["name"] == "test-action"
        TestAgentWorkflow.action_id = _id(result)

    def test_47_delete_action(self, agent):
        agent.call("delete_action", id=TestAgentWorkflow.action_id)

    # ── 6. Variables, Tags, Alerters ──────────────────────────

    def test_50_create_variable(self, agent):
        result = agent.call("create_variable",
            name="TEST_VAR",
            value="hello",
            description="A test variable",
        )
        assert result["name"] == "TEST_VAR"

    def test_51_list_variables(self, agent):
        result = agent.call("list_variables")
        assert isinstance(result, list)

    def test_52_update_variable_value(self, agent):
        result = agent.call("update_variable_value", name="TEST_VAR", value="updated")
        assert result["value"] == "updated"

    def test_53_delete_variable(self, agent):
        agent.call("delete_variable", name="TEST_VAR")

    def test_54_create_tag(self, agent):
        result = agent.call("create_tag", name="test-tag")
        assert result["name"] == "test-tag"
        TestAgentWorkflow.tag_id = _id(result)

    def test_55_list_tags(self, agent):
        result = agent.call("list_tags")
        assert isinstance(result, list)

    def test_56_delete_tag(self, agent):
        agent.call("delete_tag", id=TestAgentWorkflow.tag_id)

    def test_57_create_alerter(self, agent):
        result = agent.call("create_alerter", name="test-alerter")
        assert result["name"] == "test-alerter"
        TestAgentWorkflow.alerter_id = _id(result)

    def test_58_delete_alerter(self, agent):
        agent.call("delete_alerter", id=TestAgentWorkflow.alerter_id)

    # ── 7. Users, Groups, Permissions ─────────────────────────

    def test_60_list_users(self, agent):
        result = agent.call("list_users")
        assert isinstance(result, list)

    def test_61_create_user_group(self, agent):
        result = agent.call("create_user_group", name="test-group")
        assert result["name"] == "test-group"
        TestAgentWorkflow.user_group_id = _id(result)

    def test_62_list_user_groups(self, agent):
        result = agent.call("list_user_groups")
        assert isinstance(result, list)

    def test_63_delete_user_group(self, agent):
        agent.call("delete_user_group", id=TestAgentWorkflow.user_group_id)

    def test_64_list_permissions(self, agent):
        result = agent.call("list_permissions")
        assert isinstance(result, list)

    # ── 8. Docker ─────────────────────────────────────────────

    def test_70_list_docker_containers(self, agent):
        result = agent.call("list_docker_containers", server="test-server")
        assert isinstance(result, list)

    def test_71_list_docker_images(self, agent):
        result = agent.call("list_docker_images", server="test-server")
        assert isinstance(result, list)

    def test_72_list_docker_networks(self, agent):
        result = agent.call("list_docker_networks", server="test-server")
        assert isinstance(result, list)

    def test_73_list_docker_volumes(self, agent):
        result = agent.call("list_docker_volumes", server="test-server")
        assert isinstance(result, list)

    # ── 9. Flattened params & validation ─────────────────────

    def test_80_query_filter_by_tag(self, agent):
        """Flattened ResourceQuery: tags filter works as top-level param."""
        tag = agent.call("create_tag", name="filter-test")
        tag_id = _id(tag)
        # Tag a server
        agent.call("komodo_write",
            operation="UpdateResourceMeta",
            params={"target_type": "Server", "target_id": TestAgentWorkflow.server_id, "tags": [tag_id]},
        )
        result = agent.call("list_servers", tags=["filter-test"])
        assert isinstance(result, list)
        assert any(s["name"] == "test-server" for s in result)
        # Cleanup
        agent.call("komodo_write",
            operation="UpdateResourceMeta",
            params={"target_type": "Server", "target_id": TestAgentWorkflow.server_id, "tags": []},
        )
        agent.call("delete_tag", id=tag_id)

    def test_81_query_filter_by_name(self, agent):
        """Flattened ResourceQuery: names filter."""
        result = agent.call("list_servers", names=["test-server"])
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["name"] == "test-server"

    def test_82_unknown_param_rejected(self, agent):
        """_coerce_call rejects unknown parameters."""
        with pytest.raises(ValueError, match="Unknown parameters"):
            agent.call("komodo_read",
                operation="ListStacks",
                params={"bogus_param": True},
            )

    def test_83_list_tags_by_name(self, agent):
        """MongoDocument override: ListTags with name filter."""
        tag = agent.call("create_tag", name="findme-tag")
        tag_id = _id(tag)
        result = agent.call("list_tags", name="findme-tag")
        assert isinstance(result, list)
        assert any(t["name"] == "findme-tag" for t in result)
        # Non-matching filter returns empty
        result = agent.call("list_tags", name="nonexistent-xyz")
        assert result == [] or isinstance(result, list) and len(result) == 0
        agent.call("delete_tag", id=tag_id)

    def test_84_create_tag_with_color(self, agent):
        """TagColor enum flattened to str."""
        tag = agent.call("create_tag", name="colored-tag", color="Red")
        assert tag["name"] == "colored-tag"
        assert tag.get("color") == "Red"
        agent.call("delete_tag", id=_id(tag))

    def test_85_target_flattened(self, agent):
        """ResourceTarget flattened to target_type + target_id."""
        result = agent.call("get_permission",
            target_type="Server",
            target_id=TestAgentWorkflow.server_id,
        )
        assert "level" in result

    def test_86_list_updates_filter(self, agent):
        """MongoDocument override: ListUpdates with success filter."""
        result = agent.call("list_updates", success=True)
        assert isinstance(result, dict)
        assert "updates" in result
        assert all(u.get("success") for u in result["updates"])

    def test_87_literal_validation(self, agent):
        """Literal type validation rejects invalid enum values."""
        with pytest.raises(ValueError, match="Invalid value"):
            agent.call("komodo_read",
                operation="ListStacks",
                params={"tag_behavior": "Garbage"},
            )
        with pytest.raises(ValueError, match="Invalid value"):
            agent.call("komodo_write",
                operation="CreateRepoWebhook",
                params={"repo": "x", "action": "BadAction"},
            )
        # Valid Literal values pass
        result = agent.call("list_stacks", tag_behavior="All")
        assert isinstance(result, list)

    def test_87b_deployment_specifics(self, agent):
        """Flattened ResourceQuery: DeploymentQuerySpecifics server_ids."""
        result = agent.call("list_deployments",
            server_ids=[TestAgentWorkflow.server_id],
        )
        assert isinstance(result, list)

    def test_89_multi_step_scenario(self, agent):
        """Multi-step: create tagged resources, filter, verify, clean up.

        1. Create two tags (prod, staging)
        2. Create two stacks, assign one tag each
        3. Filter stacks by tag — verify only matching returned
        4. Filter by name — verify exact match
        5. List alerts filtered by resolved=False
        6. List updates filtered by operation
        7. Check permissions on stack via flattened target
        8. Clean up everything
        """
        import time

        # 1. Tags
        prod = agent.call("create_tag", name="e2e-prod", color="Green")
        staging = agent.call("create_tag", name="e2e-staging", color="Orange")
        prod_id, staging_id = _id(prod), _id(staging)

        # 2. Stacks
        s1 = agent.call("create_stack", name="e2e-stack-prod",
            config={"server_id": TestAgentWorkflow.server_id})
        s2 = agent.call("create_stack", name="e2e-stack-staging",
            config={"server_id": TestAgentWorkflow.server_id})
        s1_id, s2_id = _id(s1), _id(s2)

        # Tag them
        agent.call("komodo_write", operation="UpdateResourceMeta",
            params={"target_type": "Stack", "target_id": s1_id, "tags": [prod_id]})
        agent.call("komodo_write", operation="UpdateResourceMeta",
            params={"target_type": "Stack", "target_id": s2_id, "tags": [staging_id]})

        # 3. Filter stacks by tag
        prod_stacks = agent.call("list_stacks", tags=["e2e-prod"])
        assert any(s["name"] == "e2e-stack-prod" for s in prod_stacks)
        assert not any(s["name"] == "e2e-stack-staging" for s in prod_stacks)

        staging_stacks = agent.call("list_stacks", tags=["e2e-staging"])
        assert any(s["name"] == "e2e-stack-staging" for s in staging_stacks)
        assert not any(s["name"] == "e2e-stack-prod" for s in staging_stacks)

        # Both tags with tag_behavior=Any
        both = agent.call("list_stacks", tags=["e2e-prod", "e2e-staging"], tag_behavior="Any")
        names = [s["name"] for s in both]
        assert "e2e-stack-prod" in names
        assert "e2e-stack-staging" in names

        # 4. Filter by name
        by_name = agent.call("list_stacks", names=["e2e-stack-prod"])
        assert len(by_name) == 1
        assert by_name[0]["name"] == "e2e-stack-prod"

        # 5. Alerts (there should be none unresolved, but the filter itself should work)
        alerts = agent.call("list_alerts", resolved=False)
        assert isinstance(alerts, dict)
        assert "alerts" in alerts

        # 6. Updates — filter by CreateStack operation
        updates = agent.call("list_updates", operation="CreateStack")
        assert isinstance(updates, dict)
        assert all(u["operation"] == "CreateStack" for u in updates["updates"])

        # 7. Permissions on stack via flattened target
        perm = agent.call("get_permission", target_type="Stack", target_id=s1_id)
        assert "level" in perm

        # 8. Cleanup
        agent.call("delete_stack", id=s1_id)
        agent.call("delete_stack", id=s2_id)
        agent.call("delete_tag", id=prod_id)
        agent.call("delete_tag", id=staging_id)

    # ── 10. Export ─────────────────────────────────────────────

    def test_88_export_all_to_toml(self, agent):
        result = agent.call("export_all_resources_to_toml", include_resources=True)
        assert isinstance(result, (str, dict))

    # ── 11. Cleanup ───────────────────────────────────────────

    def test_90_delete_server(self, agent):
        agent.call("delete_server", id=TestAgentWorkflow.server_id)

    def test_99_summary(self, agent):
        print(f"\nTotal MCP calls: {agent.total_calls}")
        print(f"Unique tools used: {len(agent.unique_tools_used)}")
