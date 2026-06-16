from src.server.action_definitions import get_action_definition, list_action_definitions


def test_list_action_definitions_has_expected_tier1_actions() -> None:
    actions = list_action_definitions()
    names = {action["name"] for action in actions}

    assert "get_caller_identity" in names
    assert "list_s3_buckets" in names
    assert "get_s3_bucket_details" in names
    assert "get_monthly_cost_by_service" in names
    assert "list_ec2_instances" in names
    assert "list_rds_db_instances" in names
    assert "get_ses_basic_health" in names
    assert "list_trusted_advisor_checks" in names


def test_get_action_definition_for_s3_details() -> None:
    definition = get_action_definition("get_s3_bucket_details")

    assert definition is not None
    assert definition["name"] == "get_s3_bucket_details"
    assert "bucket_name" in definition["input_schema"]["properties"]
    assert definition["input_schema"]["required"] == ["bucket_name"]
