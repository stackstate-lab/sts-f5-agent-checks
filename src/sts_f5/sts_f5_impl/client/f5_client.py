from logging import Logger
from typing import Any, Dict, List, Union

import pydash.strings
import requests
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict
from sts_f5_impl.model.instance import F5Spec
from urllib3.util import Retry

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

    def get(self, url, params):
        result = self._handle_failed_call(self._session.get(url, params=params)).json()
        return result

    def get_ltm_object(
        self, object_type: str, expand_subcollections: bool = False, params: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        url = self.get_ltm_type_url(object_type)
        return self._get_f5_object(url, expand_subcollections, params)

    def get_ltm_object_stats(
        self, object_type: str, params: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        :param object_type: str Any object in the LTM_OBJECTS list
        :param params: Dict[str, Any] Additional query paramaters
        :return: List[Dict[str, Any]] Returns the 'nestedstats' object with object name and partition
        """
        url = f"{self.get_ltm_type_url(object_type)}/stats"
        return self._get_object_stats(params, url)

    def get_net_object(
        self, object_type: str, expand_subcollections: bool = False, params: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        url = self.get_net_type_url(object_type)
        return self._get_f5_object(url, expand_subcollections, params)

    def get_net_object_stats(
        self, object_type: str, params: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        :param object_type: str Any object in the NET_OBJECTS list
        :param params: Dict[str, Any] Additional query paramaters
        :return: List[Dict[str, Any]] Returns the 'nestedstats' object with object name and partition
        """
        url = f"{self.get_net_type_url(object_type)}/stats"
        return self._get_object_stats(params, url)

    def get_ltm_type_url(self, object_type: str):
        if object_type not in LTM_OBJECTS:
            raise Exception(f'Object type "{object_type}" is unknown.  Valid types are {LTM_OBJECTS}')
        return f"{self.spec.url}mgmt/tm/ltm/{object_type}"

    def get_net_type_url(self, object_type: str):
        if object_type not in NET_OBJECTS:
            raise Exception(f'Object type "{object_type}" is unknown.  Valid types are {NET_OBJECTS}')
        return f"{self.spec.url}mgmt/tm/net/{object_type}"

    def _get_f5_object(self, url, expand_subcollections, params):
        if expand_subcollections:
            params = params if params is not None else {}
            params["expandSubcollections"] = "true"
        return self.get(url, params)

    def _get_object_stats(self, params, url):
        response = self.get(url, params)
        result = []
        for key, stats in response["entries"].items():
            nested_stats = stats["nestedStats"]
            name = key.split("/")[-2]
            if name.startswith("~"):
                parts = name[1:].split("~")
                nested_stats["partition"] = parts[0]
                name = parts[1]
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
        result = self._handle_failed_call(session.post(url, data=body)).json()
        session.headers["X-F5-Auth-Token"] = result["token"]["token"]

    @staticmethod
    def _handle_failed_call(response: requests.Response) -> requests.Response:
        if not response.ok:
            msg = f"Failed to call [{response.url}]. Status code {response.status_code}. {response.text}"
            raise Exception(msg)
        return response
