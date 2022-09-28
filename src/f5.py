from six import PY3
from stackstate_checks.base import (
    AgentCheck,
    ConfigurationError,
    HealthStream,
    HealthStreamUrn,
    TopologyInstance,
)
from stackstate_etl_check_processor import AgentProcessor

from sts_f5_impl.model.instance import InstanceInfo


class F5Check(AgentCheck):
    INSTANCE_SCHEMA = InstanceInfo

    def __init__(self, name, init_config, agentConfig, instances=None):
        super().__init__(name, init_config, agentConfig, instances)

    def get_instance_key(self, instance):
        if "instance_url" not in instance:
            raise ConfigurationError("Missing instance_url in topology instance configuration.")

        if PY3:
            instance_type = instance.instance_type
            instance_url = instance.instance_url
        else:
            instance_type = instance.instance_type.encode("utf-8")
            instance_url = instance.instance_url.encode("utf-8")
        return TopologyInstance(instance_type, instance_url)

    def check(self, instance):
        AgentProcessor(instance, self).process()

    def get_health_stream(self, instance):
        return HealthStream(HealthStreamUrn(instance.instance_type, "f5_health"), expiry_seconds=0)
