import json

from typing import List, Dict, Any

from sts_f5_impl.model.instance import InstanceInfo
from sts_f5_impl.client import F5Client
from f5 import F5Check

from stackstate_checks.stubs import topology, health, aggregator
import yaml
import logging
import requests_mock

logging.basicConfig()
logger = logging.getLogger("stackstate_checks.base.checks.base.f5check")
logger.setLevel(logging.INFO)


@requests_mock.Mocker(kw="m")
def test_check(m: requests_mock.Mocker = None):
    topology.reset()
    instance_dict = setup_test_instance()
    instance = InstanceInfo(instance_dict)
    instance.validate()
    check = F5Check("f5", {}, {}, instances=[instance_dict])
    check._init_health_api()

    _setup_request_mocks(instance, m)

    check.check(instance)
    stream = {"urn": "urn:health:f5:f5_health", "sub_stream": ""}
    health_snapshot = health._snapshots[json.dumps(stream)]
    health_check_states = health_snapshot["check_states"]
    metric_names = aggregator.metric_names
    snapshot = topology.get_snapshot("")
    components = snapshot["components"]
    relations = snapshot["relations"]
    assert len(components) == 12, "Number of Components does not match"
    assert len(relations) == 5, "Number of Relations does not match"
    assert len(health_check_states) == 6, "Number of Health does not match"
    assert len(metric_names) == 0, "Number of Metrics does not match"

    # host_uid = "urn:host:/karbon-stackstate-c9a026-k8s-master-0"
    # k8s_cluster_uid = "urn:cluster:/kubernetes:stackstate"
    # k8s_cluster_uid = "urn:cluster:/kubernetes:stackstate"
    # host_component = assert_component(components, host_uid)
    # assert_component(components, k8s_cluster_uid)
    # assert_relation(relations, k8s_cluster_uid, host_uid)
    #
    # assert host_component["data"]["custom_properties"]["ipv4_address"] == "10.55.90.119"


def _setup_request_mocks(instance, m):
    def response(file_name):
        file_name = file_name.replace("-", "_")
        with open(f"tests/resources/responses/{file_name}.json") as f:
            return json.load(f)

    m.register_uri("POST", f"{instance.f5.url}/mgmt/shared/authn/login", json=response("authn_login"))
    f5 = F5Client(instance.f5, logger)

    def register(method, object_type, path="ltm"):
        if path == "net":
            url = f5.get_net_type_url(object_type)
        elif path == "cm":
            url = f5.get_cm_type_url(object_type)
        else:
            url = f5.get_ltm_type_url(object_type)
        m.register_uri(method, url, json=response(object_type))
        m.register_uri(method, f"{url}/stats", json=response(f"{object_type}_stats"))

    m.register_uri("GET", f"{instance.f5.url}/mgmt/tm/ltm/data-group/internal", json=response("data_group_internal"))

    endpoints = [
        ("GET", "interface", "net"),
        ("GET", "node"),
        ("GET", "pool"),
        ("GET", "snat"),
        ("GET", "snatpool"),
        ("GET", "rule"),
        ("GET", "self", "net"),
        ("GET", "virtual"),
        ("GET", "virtual-address"),
        ("GET", "vlan", "net"),
        ("GET", "device", "cm"),
        ("GET", "device-group", "cm"),
        ("GET", "traffic-group", "cm"),
    ]

    for endpoint in endpoints:
        register(*endpoint)


def setup_test_instance() -> Dict[str, Any]:
    with open("tests/resources/conf.d/f5.d/conf.yaml.example") as f:
        config = yaml.load(f)
        instance_dict = config["instances"][0]
    return instance_dict


def assert_component(components: List[dict], cid: str) -> Dict[str, Any]:
    component = next(iter(filter(lambda item: (item["id"] == cid), components)), None)
    assert component is not None, f"Expected to find component {cid}"
    return component


def assert_relation(relations: List[dict], sid: str, tid: str) -> Dict[str, Any]:
    relation = next(
        iter(
            filter(
                # fmt: off
                lambda item: item["source_id"] == sid and item["target_id"] == tid,
                # fmt: on
                relations,
            )
        ),
        None,
    )
    assert relation is not None, f"Expected to find relation {sid}->{tid}"
    return relation
