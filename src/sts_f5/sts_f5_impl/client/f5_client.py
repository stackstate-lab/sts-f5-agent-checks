import re
from logging import Logger
from typing import Any, Dict, List, Optional, Tuple

import pydash.strings
import requests
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict
from stackstate_etl.model.factory import TopologyFactory
from stackstate_etl.model.stackstate import Component
from sts_f5_impl.model.instance import F5Spec
from urllib3.util import Retry

CM_OBJECTS = ["cert", "device", "device-group", "key", "traffic-group", "trust-domain"]

LTM_OBJECTS = [
    "auth",
    "cipher",
    "data-group",
    "dns",
    "global-settings",
    "html-rule",
    "message-routing",
    "monitor",
    "persistence",
    "profile",
    "tacdb",
    "default-node-monitor",
    "eviction-policy",
    "ifile",
    "nat",
    "node",
    "policy",
    "policy-strategy",
    "pool",
    "rule",
    "rule-profiler",
    "snat",
    "snat-translation",
    "snatpool",
    "traffic-class",
    "traffic-matching-criteria",
    "virtual",
    "virtual-address",
]

NET_OBJECTS = [
    "bwc",
    "cos",
    "fdb",
    "ipsec",
    "rate-shaping",
    "routing",
    "sfc",
    "tunnels",
    "address-list",
    "arp",
    "dag-globals",
    "dns-resolver",
    "interface",
    "lacp-globals",
    "lldp-globals",
    "multicast-globals",
    "ndp",
    "packet-filter",
    "packet-filter-trusted",
    "port-list",
    "port-mirror",
    "route",
    "route-domain",
    "router-advertisement",
    "self",
    "self-allow",
    "service-policy",
    "stp",
    "stp-globals",
    "timer-policy",
    "trunk",
    "vlan",
    "vlan-group",
    "wccp",
]


class F5Client(object):
    def __init__(self, spec: F5Spec, log: Logger):
        self.log = log
        self.spec = spec
        self.spec.url = pydash.strings.ensure_ends_with(spec.url, "/")
        self._session = self._init_session(spec)
        self._rules: Dict[str, str] = {}
        self._data_groups: Dict[str, Tuple[str, Dict[str, str]]] = {}

    @staticmethod
    def get_ip_from_destination(destination: str) -> str:
        # /Common/192.168.10.21:80
        if "/" in destination:
            destination = destination.rsplit("/", 1)[1]
        parts = destination.split(":")
        return parts[0]

    @staticmethod
    def get_name_from_self_link(link: str) -> str:
        parts = link.split("?")[0].split("/")
        name = parts[-1]
        if "~" in name:
            name = name.rsplit("~", 1)[-1]
        return name

    @staticmethod
    def get_full_name_from_self_link(link: str) -> str:
        parts = link.split("?")[0].split("/")
        name = parts[-1]
        return name.replace("~", "/")

    def get(self, url, params) -> Dict[str, Any]:
        result = self._handle_failed_call(self._session.get(url, params=params)).json()
        return result

    def get_pools_from_switch_statement_irule(self, rule_name: str) -> List[Dict[str, Optional[str]]]:
        return self._get_pools_from_switch_statement_irule(self.get_rule(rule_name))

    @staticmethod
    def _get_pools_from_switch_statement_irule(irule: str) -> List[Dict[str, Optional[str]]]:
        # strip out key words
        lines = []
        for line in irule.split("\n"):
            line = line.strip()
            if (
                line == ""
                or line.startswith("#")
                or line.startswith("if ")
                or line.startswith("switch ")
                or line.startswith("when ")
                or line.startswith("HTTP::uri")
                or line.startswith("[HTTP::uri")
                or line.startswith("HTTP::redirect")
                or line.startswith("persist")
                or line.startswith("set ")
                or line.startswith("set ")
            ):
                continue
            lines.append(line)

        one_line_block = re.compile('("/[A-Za-z0-9-*/_?]*".*{)(.*)}')
        one_line_default_block = re.compile('(default.*{)(.*)}')
        start_block = re.compile('"(/[A-Za-z0-9-*/_?]*)".*{')
        default_start_block = re.compile('default.*{')
        blocks = []
        still_too_parse_lines = []
        for line in lines:
            match = one_line_block.match(line)
            if match:
                blocks.append([match.group(1).strip(), match.group(2).strip(), "}"])
            else:
                match = one_line_default_block.match(line)
                if match:
                    blocks.append([match.group(1).strip(), match.group(2).strip(), "}"])
                else:
                    still_too_parse_lines.append(line)

        current_block: List[str] = []
        first_iteration = True
        while len(still_too_parse_lines) > 0:
            line = still_too_parse_lines.pop(0)
            if start_block.match(line) or default_start_block.match(line):
                first_iteration = False
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                if first_iteration:
                    if line == "}":
                        continue
                    else:
                        raise Exception(f"No start block found! Fist line was '{line}'")
            if line.strip() != "":
                current_block.append(line)
        pools: List[Dict[str, Optional[str]]] = []
        host_line = "HTTP::header replace Host "
        pool_line = "pool "
        for block in blocks:
            uri_pattern = None
            host = None
            pool = None
            for line in block:
                match = start_block.match(line)
                if match:
                    uri_pattern = match.group(1)
                elif line.startswith(host_line):
                    host = line[len(host_line) :]
                elif line.startswith(pool_line):
                    pool = line[len(pool_line) :]
            if pool:
                pools.append({"pool": pool, "host": host, "uri_pattern": uri_pattern})
        return pools

    def get_rule(self, rule_name: str) -> str:
        if len(self._rules) == 0:
            rules_object: Dict[str, Any] = self.get_ltm_object("rule")
            for item in rules_object["items"]:
                self._rules[item["name"]] = item["apiAnonymous"]
        return self._rules[rule_name]

    def get_data_group(self, dg_name: str) -> Tuple[str, Dict[str, str]]:
        if len(self._data_groups) == 0:
            url = self.get_ltm_type_url("data-group")
            data_groups_object = self._get_f5_object(f"{url}/internal", False, None)  # type: ignore
            for item in data_groups_object["items"]:
                records = {}
                for r in item.get("records", []):
                    records[r["name"]] = r["data"]
                self._data_groups[item["name"]] = (item["partition"], records)
        if dg_name not in self._data_groups:
            self.log.error(f"Datagroup name {dg_name} not found.")
            empty_dict: Tuple[str, Dict[str, str]] = ("Common", {})
            return empty_dict
        return self._data_groups[dg_name]

    def process_data_group_proxypass_details(
        self, dg_name: str, vs_uid: str, host_name: str, rule: str, vip: str, factory: TopologyFactory
    ):
        dg_tuple = self.get_data_group(dg_name)
        partition = dg_tuple[0]
        records = dg_tuple[1]
        for key, value in records.items():
            if key.startswith(host_name):
                value_parts = value.split(" ")
                if len(value_parts) != 2:
                    self.log.error(
                        "Expected 2 parts in value '%s' for key '%s' in data group '%s' " % (value, key, dg_name)
                    )
                    continue
                pool_name = value_parts[1]
                if not pool_name.startswith("/Common/"):
                    pool_name = pydash.strings.ensure_starts_with(pool_name, "/%s/" % partition)
                pool_name.replace("//", "/")
                pool_uid = "urn:f5:pool:/%s" % pool_name
                serverside_name = value_parts[0].split("/")[0]
                serverside_uid = factory.get_uid("host", "virtual:server", serverside_name)
                if not factory.component_exists(serverside_uid):
                    serverside_component = Component()
                    serverside_component.uid = serverside_uid
                    serverside_component.set_type("virtual-server")
                    serverside_component.set_name(serverside_name)
                    serverside_component.properties.layer = "Virtual Servers"
                    serverside_component.properties.domain = "F5"
                    factory.add_component(serverside_component)

                if not factory.component_exists(pool_uid):
                    self.log.error(
                        "Expected to find pool %s in rule %s for host %s for vip %s. Ignoring..."
                        % (pool_uid, rule, host_name, vip)
                    )
                else:
                    pool_component = factory.get_component(pool_uid)
                    pool_component.properties.add_label_kv("rule", rule)
                    # pool_component.properties.add_label_kv("clientside", key)
                    # pool_component.properties.add_label_kv("serverside", value_parts[0])
                    if not factory.relation_exists(pool_uid, serverside_uid):
                        factory.add_relation(pool_uid, serverside_uid)

                    if not factory.component_exists(vs_uid):
                        self.log.error(
                            "Expected to find virtual server %s in rule %s for host %s for vip %s. Ignoring..."
                            % (vs_uid, rule, host_name, vip)
                        )
                        return
                    vs_component = factory.get_component(vs_uid)
                    if not factory.relation_exists(vs_component.uid, pool_component.uid):
                        factory.add_relation(vs_component.uid, pool_uid)

    def get_ltm_object(
        self, object_type: str, expand_subcollections: bool = False, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        url = self.get_ltm_type_url(object_type)
        return self._get_f5_object(url, expand_subcollections, params)

    def get_ltm_object_stats(self, object_type: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        :param object_type: str Any object in the LTM_OBJECTS list
        :param params: Dict[str, Any] Additional query paramaters
        :return: List[Dict[str, Any]] Returns the 'nestedstats' object with object name and partition
        """
        url = f"{self.get_ltm_type_url(object_type)}/stats"
        return self._get_object_stats(params, url)

    def get_net_object(
        self, object_type: str, expand_subcollections: bool = False, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        url = self.get_net_type_url(object_type)
        return self._get_f5_object(url, expand_subcollections, params)

    def get_net_object_stats(self, object_type: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        :param object_type: str Any object in the NET_OBJECTS list
        :param params: Dict[str, Any] Additional query paramaters
        :return: List[Dict[str, Any]] Returns the 'nestedstats' object with object name and partition
        """
        url = f"{self.get_net_type_url(object_type)}/stats"
        return self._get_object_stats(params, url)

    def get_cm_object(
        self, object_type: str, expand_subcollections: bool = False, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        url = self.get_cm_type_url(object_type)
        return self._get_f5_object(url, expand_subcollections, params)

    def get_cm_object_stats(self, object_type: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        :param object_type: str Any object in the CM_OBJECTS list
        :param params: Dict[str, Any] Additional query paramaters
        :return: List[Dict[str, Any]] Returns the 'nestedstats' object with object name and partition
        """
        url = f"{self.get_cm_type_url(object_type)}/stats"
        return self._get_object_stats(params, url)

    def get_cm_type_url(self, object_type: str) -> str:
        if object_type not in CM_OBJECTS:
            raise Exception(f'Object type "{object_type}" is unknown.  Valid types are {CM_OBJECTS}')
        return f"{self.spec.url}mgmt/tm/cm/{object_type}"

    def get_ltm_type_url(self, object_type: str) -> str:
        if object_type not in LTM_OBJECTS:
            raise Exception(f'Object type "{object_type}" is unknown.  Valid types are {LTM_OBJECTS}')
        return f"{self.spec.url}mgmt/tm/ltm/{object_type}"

    def get_net_type_url(self, object_type: str) -> str:
        if object_type not in NET_OBJECTS:
            raise Exception(f'Object type "{object_type}" is unknown.  Valid types are {NET_OBJECTS}')
        return f"{self.spec.url}mgmt/tm/net/{object_type}"

    def _get_f5_object(self, url, expand_subcollections, params) -> Dict[str, Any]:
        if expand_subcollections:
            params = params if params is not None else {}
            params["expandSubcollections"] = "true"
        return self.get(url, params)

    def _get_object_stats(self, params, url) -> List[Dict[str, Any]]:
        response = self.get(url, params)
        result = []
        for key, stats in response["entries"].items():
            nested_stats = stats["nestedStats"]
            # https://localhost/mgmt/tm/cm/traffic-group/~Common~traffic-group-1:~Common~bigip1.local.net/stats
            name = key.split("/")[-2]
            if name.startswith("~"):
                parts = name[1:].split("~")
                nested_stats["partition"] = parts[0]
                name = parts[1].split(":")[0]
            nested_stats["name"] = name
            result.append(nested_stats)
        return result

    def _init_session(self, spec: F5Spec) -> requests.Session:
        retry = Retry(
            total=spec.max_request_retries,
            backoff_factor=spec.retry_backoff_seconds,
            status_forcelist=spec.retry_on_status,
        )
        session = requests.Session()
        session.verify = False
        session.headers = CaseInsensitiveDict(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "cache-control": "no-cache",
            }
        )
        session.mount(spec.url, HTTPAdapter(max_retries=retry))
        self._setup_session_token(session, spec)
        return session

    def _setup_session_token(self, session: requests.Session, spec: F5Spec):
        url = f"{spec.url}mgmt/shared/authn/login"
        body = {"username": spec.username, "password": spec.password, "loginProviderName": "tmos"}
        result = self._handle_failed_call(session.post(url, json=body)).json()
        session.headers["X-F5-Auth-Token"] = result["token"]["token"]

    @staticmethod
    def _handle_failed_call(response: requests.Response) -> requests.Response:
        if not response.ok:
            msg = f"Failed to call [{response.url}]. Status code {response.status_code}. {response.text}"
            raise Exception(msg)
        return response

    @staticmethod
    def _rreplace(s, old, new):
        li = s.rsplit(old, 1)
        return new.join(li)

    def break_point(self, arg: Any):
        self.log.info(arg)
