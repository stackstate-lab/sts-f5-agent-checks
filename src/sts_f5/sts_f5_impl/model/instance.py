from typing import List

from schematics import Model
from schematics.types import IntType, ListType, ModelType, StringType, URLType
from stackstate_etl.model.instance import InstanceInfo as EtlInstanceInfo


class F5Spec(Model):
    url: str = URLType(required=True)
    username: str = StringType(required=True)
    password: str = StringType(required=True)
    max_request_retries: int = IntType(default=3)  # In case of a connection failure try 2 more times
    retry_backoff_seconds: int = IntType(default=2)  # wait 1 second before retrying in case of an error
    retry_on_status: List[int] = ListType(IntType, default=[408, 429, 500, 502, 503, 504])


class InstanceInfo(EtlInstanceInfo):
    instance_url: str = StringType(required=True)
    instance_type: str = StringType(default="f5check")
    collection_interval: int = IntType(default=120)
    f5: F5Spec = ModelType(F5Spec, required=True)
