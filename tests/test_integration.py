"""Integration tests — an agent works with Komodo entirely through MCP tools.

The test simulates a realistic agent workflow:
1. Check connection → 2. CRUD servers →
3. Deployments lifecycle → 4. Stacks lifecycle →
5. Builds, repos, procedures, actions →
6. Variables, tags, alerters →
7. Users, groups, permissions →
8. Batch operations → 9. Docker cleanup → 10. Export TOML
"""

import json

import pytest

from tests.conftest import KOMODO_URL


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
        result = agent.call("create_server",
            name="test-server",
            config=json.dumps({"address": "http://komodo-periphery:8120"}),
        )
        assert result["name"] == "test-server"
        TestAgentWorkflow.server_id = result["id"]

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
        assert result["name"] == "test-server-renamed"

    def test_15_rename_server_back(self, agent):
        agent.call("rename_server",
            id=TestAgentWorkflow.server_id,
            name="test-server",
        )

    # ── 3. Deployments ────────────────────────────────────────

    def test_20_create_deployment(self, agent):
        result = agent.call("create_deployment",
            name="test-deploy",
            config=json.dumps({
                "server_id": TestAgentWorkflow.server_id,
                "image": "nginx:alpine",
            }),
        )
        assert result["name"] == "test-deploy"
        TestAgentWorkflow.deployment_id = result["id"]

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
        result = agent.call("get_deployment_log", deployment="test-deploy", tail=10)
        assert result is not None

    def test_26_stop_deployment(self, agent):
        agent.call("stop_deployment", deployment="test-deploy")

    def test_27_destroy_deployment(self, agent):
        agent.call("destroy_deployment", deployment="test-deploy")

    def test_28_delete_deployment(self, agent):
        agent.call("delete_deployment", id=TestAgentWorkflow.deployment_id)

    # ── 4. Stacks ─────────────────────────────────────────────

    def test_30_create_stack(self, agent):
        compose = "services:\\n  web:\\n    image: nginx:alpine\\n    ports:\\n      - '8080:80'"
        result = agent.call("create_stack",
            name="test-stack",
            config=json.dumps({"server_id": TestAgentWorkflow.server_id}),
        )
        assert result["name"] == "test-stack"
        TestAgentWorkflow.stack_id = result["id"]

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
        TestAgentWorkflow.build_id = result["id"]

    def test_41_delete_build(self, agent):
        agent.call("delete_build", id=TestAgentWorkflow.build_id)

    def test_42_create_repo(self, agent):
        result = agent.call("create_repo", name="test-repo")
        assert result["name"] == "test-repo"
        TestAgentWorkflow.repo_id = result["id"]

    def test_43_delete_repo(self, agent):
        agent.call("delete_repo", id=TestAgentWorkflow.repo_id)

    def test_44_create_procedure(self, agent):
        result = agent.call("create_procedure", name="test-procedure")
        assert result["name"] == "test-procedure"
        TestAgentWorkflow.procedure_id = result["id"]

    def test_45_delete_procedure(self, agent):
        agent.call("delete_procedure", id=TestAgentWorkflow.procedure_id)

    def test_46_create_action(self, agent):
        result = agent.call("create_action", name="test-action")
        assert result["name"] == "test-action"
        TestAgentWorkflow.action_id = result["id"]

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
        TestAgentWorkflow.tag_id = result["id"]

    def test_55_list_tags(self, agent):
        result = agent.call("list_tags")
        assert isinstance(result, list)

    def test_56_delete_tag(self, agent):
        agent.call("delete_tag", id=TestAgentWorkflow.tag_id)

    def test_57_create_alerter(self, agent):
        result = agent.call("create_alerter", name="test-alerter")
        assert result["name"] == "test-alerter"
        TestAgentWorkflow.alerter_id = result["id"]

    def test_58_delete_alerter(self, agent):
        agent.call("delete_alerter", id=TestAgentWorkflow.alerter_id)

    # ── 7. Users, Groups, Permissions ─────────────────────────

    def test_60_list_users(self, agent):
        result = agent.call("list_users")
        assert isinstance(result, list)

    def test_61_create_user_group(self, agent):
        result = agent.call("create_user_group", name="test-group")
        assert result["name"] == "test-group"
        TestAgentWorkflow.user_group_id = result["id"]

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

    # ── 9. Export ─────────────────────────────────────────────

    def test_80_export_all_to_toml(self, agent):
        result = agent.call("export_all_resources_to_toml")
        assert "toml" in result

    # ── 10. Cleanup ───────────────────────────────────────────

    def test_90_delete_server(self, agent):
        agent.call("delete_server", id=TestAgentWorkflow.server_id)

    def test_99_summary(self, agent):
        print(f"\nTotal MCP calls: {agent.total_calls}")
        print(f"Unique tools used: {len(agent.unique_tools_used)}")
