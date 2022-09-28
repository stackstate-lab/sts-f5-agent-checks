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
curl -L https://github.com/stackstate-lab/sts-f5-agent-checks/releases/download/v0.1.1/f5-agent-check-0.1.1.zip -o sts_f5.zip
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


| Name                                               | Module              | Cls                                                     | Description                  |
|----------------------------------------------------|---------------------|---------------------------------------------------------|------------------------------|
| [f5](./src/sts_f5_impl/templates/010_default.yaml) | sts_f5_impl.client  | [F5Client](./src/sts_f5_impl/client/f5_client.py)  | enables rest calls to F5 api |


### Template Mappings

| Name                                                                                                              | Type              | 4T        | f5 Api                                                                                 | Description                                    |
|-------------------------------------------------------------------------------------------------------------------|-------------------|-----------|----------------------------------------------------------------------------------------|------------------------------------------------|
| [f5_device_template](./src/sts_f5_impl/templates/020_f5_devices.yaml)                                      | f5-device         | Component | [mgmt/tm/cm/device](./tests/resources/responses/device.json)                           |                                                |
| [f5_device_group_template](./src/sts_f5_impl/templates/022_f5_device_groups.yaml)                          | f5-device-group   | Component | [mgmt/tm/cm/device-group](./tests/resources/responses/device_group.json)               |                                                |
| [f5-traffic-group](./src/sts_f5_impl/templates/024_f5_traffic_groups.yaml)                                 | f5-traffic-group  | Component | [mgmt/tm/cm/traffic-group](./tests/resources/responses/traffic_group.json)             |                                                |
| [f5_traffic_group_rel_template](./src/sts_f5_impl/templates/024_f5_traffic_groups.yaml)                    | f5-traffic-group  | Relation  | [mgmt/tm/cm/traffic-group/stats](./tests/resources/responses/traffic_group_stats.json) |                                                |
| [f5_self_ip_template](./src/sts_f5_impl/templates/026_f5_self_ips.yaml)                                    | f5-self-ip        | Component | [mgmt/tm/net/self](./tests/resources/responses/self.json)                              |                                                |
| [f5_host_template](./src/sts_f5_impl/templates/020_f5_nodes.yaml)                                          | f5-node           | Component | [mgmt/tm/ltm/node](./tests/resources/responses/node.json)                              |                                                |
| [f5_host_health_template](./src/sts_f5_impl/templates/020_f5_nodes.yaml)                                   | f5-node           | Health    | [mgmt/tm/ltm/node](./tests/resources/responses/node.json)                              |                                                |
| [f5_pool_template](./src/sts_f5_impl/templates/040_f5_pools.yaml)                                          | f5-pool           | Component | [mgmt/tm/ltm/pool](./tests/resources/responses/pool.json)                              |                                                |
| [f5_pool_status_template](./src/sts_f5_impl/templates/040_f5_pools.yaml)                                   | f5-pool           | Health    | [mgmt/tm/ltm/pool/stats](./tests/resources/responses/pool_stats.json)                  |                                                |
| [f5_pool_metrics_template](./src/sts_f5_impl/templates/040_f5_pools.yaml)                                  | f5-pool           | Metric    | [mgmt/tm/ltm/pool/stats](./tests/resources/responses/pool_stats.json)                  |                                                |
| [f5_virtual_server_template](./src/sts_f5_impl/templates/050_f5_virtual_servers.yaml)                      | f5-virtual-server | Component | [mgmt/tm/ltm/virtual](./tests/resources/responses/virtual.json)                        |                                                |
| [f5_virtual_server_address_template](./src/sts_f5_impl/templates/052_f5_virtual_server_addresses.yaml)     | f5-virtual-server | Relation  | [mgmt/tm/ltm/virtual-address](./tests/resources/responses/virtual_address.json)        |                                                |
| [f5_interface_template](./src/sts_f5_impl/templates/060_f5_interfaces.yaml)                                | f5-interface      | Component | [mgmt/tm/net/interface](./tests/resources/responses/interface.json)                    |                                                |
| [f5_interface_status_template](./src/sts_f5_impl/templates/060_f5_interfaces.yaml)                         | f5-interface      | Health    | [mgmt/tm/net/interface/stats](./tests/resources/responses/interface_stats.json)        |                                                |
| [f5_vlan_template](./src/sts_f5_impl/templates/060_f5_vlans.yaml)                                          | f5-vlan           | Component | [mgmt/tm/net/vlan](./tests/resources/responses/vlan.json)                              |                                                |
| [f5_virtual_server_irule_pools](./src/sts_f5_impl/templates/055_f5_virtual_server_irule_pools.yaml.example) | f5-pool           | Relation  | IRule and Data Groups                                                                  | Example of parsing iRule and using Data Group  |


## Development

This project is generated using [Yeoman](https://yeoman.io/) and the [StackState Generator](https://github.com/stackstate-lab/generator-stackstate-lab)

StackState F5 Big IP Agent Check is developed in Python 3, and is transpiled to Python 2.7 for deployment to the StackState Agent v2 environment.

---
### Prerequisites:

- Python v.3.9.x See [Python installation guide](https://docs.python-guide.org/starting/installation/)
- [PDM](https://pdm.fming.dev/latest/#recommended-installation-method)
- [Docker](https://www.docker.com/get-started)
- [Mockoon](https://mockoon.com/)
---


### Setup local code repository

```bash 
git clone git@github.com:stackstate-lab/sts-f5-agent-checks.git
cd sts-f5-agent-checks
pdm install 
```
The `pdm install` command sets up all the projects required dependencies using [PEP 582](https://peps.python.org/pep-0582/) instead of virtual environments.

### Prepare local _.sts.env_ file

The `.sts.env` file is used to run the StackState Agent container. Remember to change the StackState url and api key for your environment.

```bash

cat <<EOF > ./.sts.env
STS_URL=https://xxx.stackstate.io/receiver/stsAgent
STS_API_KEY=xxx
EOF
```


### Preparing Mock Server

In Mockoon, open environment `tests/resources/mockoon/f5.json` and press start.


### Preparing Agent check conf.yaml

```
cp ./src/data/conf.d/f5.d/conf.yaml.example ./src/data/conf.d/f5.d/conf.yaml
```

Change the `url` property to point to Mockoon port for when the agent check runs in docker.
e.g `http://host.docker.internal:3005`

---
### Code styling and linting


- [Black](https://black.readthedocs.io/en/stable/) for formatting
- [isort](https://pycqa.github.io/isort/) to sort imports
- [Flakehell](https://flakehell.readthedocs.io/) for linting
- [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking

```bash
pdm format
```

### Running unit tests

```bash
pdm test
```

### Build

The build will transpile the custom agent check to Python 2.7 and creates and install shell script packaged into
the `dist/f_5-agent-check-0.1.0.zip`

```bash
pdm build
```

### Building a StackState Agent container

You have the ability to customize the StackState Agent using the [Dockerfile](./tasks/dev-agent/Dockerfile).

For installing os packages or other tools at runtime, you could define an `install.sh` file in the `tests/resources/share/` directory that is run every time the container is started.

```bash
pdm cleanAgent
pdm buildAgent
```

### Running your custom agent check

A check can be dry-run inside the StackState Agent container by running:

```bash
pdm check
```

### Starting the StackState Agent to send data to StackState server

Starts the StackState Agent in the foreground using the configuration `src/data/conf.d/` directory.

```bash
pdm serve
```
---
