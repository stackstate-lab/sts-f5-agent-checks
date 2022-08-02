# StackState F5 Big IP Agent Check

## Overview

A custom [StackState Agent Check](https://docs.stackstate.com/develop/developer-guides/agent_check/agent_checks) that
makes it possible to integrate [F5 Big IP](https://www.f5.com/products/big-ip-services/local-traffic-manager).

The integration uses the [StackState ETL framework](https://stackstate-lab.github.io/stackstate-etl/) 
to define templates to map F5 Rest Api entities to StackState Components, Relations, Events,
Metrics and Health Syncs

See [StackState ETL documentation](https://stackstate-lab.github.io/stackstate-etl/) for more information.

## Installation

From the StackState Agent 2 linux machine, run

```bash 
curl -L https://github.com/stackstate-lab/sts-f5-agent-checks/releases/download/v0.1.0/sts_f5-0.1.0.zip -o sts_f5.zip
tar -xvf sts_f5.zip
./install.sh
```

Setup `conf.yaml` on agent machine.

```bash 
cp /etc/stackstate-agent/conf.d/f5.d/conf.yaml.example /etc/stackstate-agent/conf.d/f5.d/conf.yaml
chown stackstate-agent:stackstate-agent /etc/stackstate-agent/conf.d/f5.d/conf.yaml
vi conf.yaml
```

Change the properties to match your environment.

```yaml

init_config:

instances:
  - instance_url: "f5"
    instance_type: f5
    collection_interval: 300
    f5:
      url: "http://host.docker.internal:3005"
      username: "admin"
      password: "nx2Tech081!"
    domain: "f5"
    layer: "Machines"
    etl:
      refs:
        - "module_dir://sts_f5_impl.templates"


```

Run the agent check to verify configured correctly.

```bash
sudo -u stackstate-agent stackstate-agent check f5 -l info
```

## ETL

APIs to syn data from, 

- [icontrol-rest-api-user-guide-15-1-0.pdf](https://cdn.f5.com/websites/devcentral.f5.com/downloads/icontrol-rest-api-user-guide-15-1-0.pdf)
  - Refer to page 24/25 for information on query parameters like $select, $filter, pagination
- [Common iControl REST API command examples](https://support.f5.com/csp/article/K13225405)


### DataSources


| Name                                                        | Module              | Cls                                                     | Description                  |
|-------------------------------------------------------------|---------------------|---------------------------------------------------------|------------------------------|
| [f5](./src/sts_f5/sts_f5_impl/templates/010_default.yaml)   | sts_f5_impl.client  | [F5Client](src/sts_f5/sts_f5_impl/client/f5_client.py)  | enables rest calls to F5 api |


### Template Mappings

| Name                                                                                                              | Type              | 4T        | f5 Api                                                                                 | Description                                    |
|-------------------------------------------------------------------------------------------------------------------|-------------------|-----------|----------------------------------------------------------------------------------------|------------------------------------------------|
| [f5_device_template](./src/sts_f5/sts_f5_impl/templates/020_f5_devices.yaml)                                      | f5-device         | Component | [mgmt/tm/cm/device](./tests/resources/responses/device.json)                           |                                                |
| [f5_device_group_template](./src/sts_f5/sts_f5_impl/templates/022_f5_device_groups.yaml)                          | f5-device-group   | Component | [mgmt/tm/cm/device-group](./tests/resources/responses/device_group.json)               |                                                |
| [f5-traffic-group](./src/sts_f5/sts_f5_impl/templates/024_f5_traffic_groups.yaml)                                 | f5-traffic-group  | Component | [mgmt/tm/cm/traffic-group](./tests/resources/responses/traffic_group.json)             |                                                |
| [f5_traffic_group_rel_template](./src/sts_f5/sts_f5_impl/templates/024_f5_traffic_groups.yaml)                    | f5-traffic-group  | Relation  | [mgmt/tm/cm/traffic-group/stats](./tests/resources/responses/traffic_group_stats.json) |                                                |
| [f5_self_ip_template](./src/sts_f5/sts_f5_impl/templates/026_f5_self_ips.yaml)                                    | f5-self-ip        | Component | [mgmt/tm/net/self](./tests/resources/responses/self.json)                              |                                                |
| [f5_host_template](./src/sts_f5/sts_f5_impl/templates/020_f5_nodes.yaml)                                          | f5-node           | Component | [mgmt/tm/ltm/node](./tests/resources/responses/node.json)                              |                                                |
| [f5_host_health_template](./src/sts_f5/sts_f5_impl/templates/020_f5_nodes.yaml)                                   | f5-node           | Health    | [mgmt/tm/ltm/node](./tests/resources/responses/node.json)                              |                                                |
| [f5_pool_template](./src/sts_f5/sts_f5_impl/templates/040_f5_pools.yaml)                                          | f5-pool           | Component | [mgmt/tm/ltm/pool](./tests/resources/responses/pool.json)                              |                                                |
| [f5_pool_status_template](./src/sts_f5/sts_f5_impl/templates/040_f5_pools.yaml)                                   | f5-pool           | Health    | [mgmt/tm/ltm/pool/stats](./tests/resources/responses/pool_stats.json)                  |                                                |
| [f5_pool_metrics_template](./src/sts_f5/sts_f5_impl/templates/040_f5_pools.yaml)                                  | f5-pool           | Metric    | [mgmt/tm/ltm/pool/stats](./tests/resources/responses/pool_stats.json)                  |                                                |
| [f5_virtual_server_template](./src/sts_f5/sts_f5_impl/templates/050_f5_virtual_servers.yaml)                      | f5-virtual-server | Component | [mgmt/tm/ltm/virtual](./tests/resources/responses/virtual.json)                        |                                                |
| [f5_virtual_server_address_template](./src/sts_f5/sts_f5_impl/templates/052_f5_virtual_server_addresses.yaml)     | f5-virtual-server | Relation  | [mgmt/tm/ltm/virtual-address](./tests/resources/responses/virtual_address.json)        |                                                |
| [f5_interface_template](./src/sts_f5/sts_f5_impl/templates/060_f5_interfaces.yaml)                                | f5-interface      | Component | [mgmt/tm/net/interface](./tests/resources/responses/interface.json)                    |                                                |
| [f5_interface_status_template](./src/sts_f5/sts_f5_impl/templates/060_f5_interfaces.yaml)                         | f5-interface      | Health    | [mgmt/tm/net/interface/stats](./tests/resources/responses/interface_stats.json)        |                                                |
| [f5_vlan_template](./src/sts_f5/sts_f5_impl/templates/060_f5_vlans.yaml)                                          | f5-vlan           | Component | [mgmt/tm/net/vlan](./tests/resources/responses/vlan.json)                              |                                                |
| [f5_virtual_server_irule_pools](./src/sts_f5/sts_f5_impl/templates/055_f5_virtual_server_irule_pools.yaml.example) | f5-pool           | Relation  | IRule and Data Groups                                                                  | Example of parsing iRule and using Data Group  |


## Development

StackState F5 Big IP Agent Check is developed in Python 3, and is transpiled to Python 2.7 during build.

---
### Prerequisites:

- Python v.3.7+. See [Python installation guide](https://docs.python-guide.org/starting/installation/)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Docker](https://www.docker.com/get-started)
- [Mockoon](https://mockoon.com/)
- [Custom Synchronization StackPack](https://docs.stackstate.com/stackpacks/integrations/customsync)
---

### Setup local code repository


The poetry install command creates a virtual environment and downloads the required dependencies.

Install the [stsdev](https://github.com/stackstate-lab/stslab-dev) tool into the virtual environment.

```bash 
python -m pip install https://github.com/stackstate-lab/stslab-dev/releases/download/v0.0.7/stslab_dev-0.0.7-py3-none-any.whl
```

Finalize the downloading of the StackState Agent dependencies using `stsdev`

```bash
stsdev update
```
### Prepare local `.env` file

The `.env` file is used by `stsdev` to prepare and run the StackState Agent Docker image. Remember to change the
StackState url and api key for your environment.

```bash

cat <<EOF > ./.env
STSDEV_IMAGE_EXT=tests/resources/docker/agent_dockerfile
STS_URL=https://xxx.stackstate.io/receiver/stsAgent
STS_API_KEY=xxx
STSDEV_ADDITIONAL_COMMANDS=/etc/stackstate-agent/share/install.sh
STSDEV_ADDITIONAL_COMMANDS_FG=true
EXCLUDE_LIBS=charset-normalizer,stackstate-etl,stackstate-etl-agent-check
EOF
```

### Preparing Mock Server

In Mockoon, open environment `tests/resources/mockoon/f5.json` and press start.


### Preparing Agent check conf.yaml

```
cp ./tests/resources/conf.d/f5.d/conf.yaml.example ./tests/resources/conf.d/f5.d/conf.yaml
```
Change the `url` property to point to Mockoon port for when the agent check runs in docker.
e.g `http://host.docker.internal:3005`

---

### Running in Intellij

Setup the module sdk to point to the virtual python environment created by Poetry.
Default on macos is `~/Library/Caches/pypoetry/virtualenvs`

Create a python test run config for `tests/test_f5_check.py`

You can now run the integration from the test.

---
### Running using `stsdev`

```bash

stsdev agent check f5 
```

### Running StackState Agent to send data to StackState

```bash

stsdev agent run
```

---

## Quick-Start for `stsdev`

`stsdev` is a tool to aid with the development StackState Agent integrations.

### Managing dependencies

[Poetry](https://python-poetry.org/) is used as the packaging and dependency management system.

Dependencies for your project can be managed through `poetry add` or `poetry add -D` for development dependency.

```console
$ poetry add PyYAML
```
### Code styling and linting

```console
$ stsdev code-style
```

### Build the project
To build the project,
```console
$ stsdev build --no-run-tests
```
This will automatically run code formatting, linting, tests and finally the build.

### Unit Testing
To run tests in the project,
```console
$ stsdev test
```
This will automatically run code formatting, linting, and tests.

### Dry-run a check

A check can be dry-run inside the StackState Agent by running

```console
$ stsdev agent check f5
```
Before running the command, remember to copy the example conf `tests/resources/conf.d/f5.d/conf.yaml.example` to
`tests/resources/conf.d/f5.d/conf.yaml`.


### Running checks in the Agent

Starts the StackState Agent in the foreground using the test configuration `tests/resources/conf.d`

```console
$ stsdev agent run
```

### Packaging checks

```console
$  stsdev package --no-run-tests
```
This will automatically run code formatting, linting, tests and finally the packaging.
A zip file is created in the `dist` directory.  Copy this to the host running the agent and unzip it.
Run the `install.sh`.

