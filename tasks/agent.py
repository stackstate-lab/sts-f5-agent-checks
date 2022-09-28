import subprocess
import os
from pathlib import Path
import toml

PROJECT_DIR = Path(__file__).parent.parent

TARGET_IMAGE = "stackstate-agent-2-dev:latest"
STS_API_KEY = os.getenv('STS_API_KEY')
STS_URL = os.getenv('STS_URL')

if STS_API_KEY is None or STS_URL is None:
    raise Exception(f"STS_API_KEY ({STS_API_KEY}) and STS_URL({STS_URL}) are required.")


AGENT_DOCKER_CMD = ["docker", "run", "--rm", "-it", "-v", f"{PROJECT_DIR}/build/agent:/etc/stackstate-agent",
                    "-e", f"STS_API_KEY={STS_API_KEY}",
                    "-e", f"STS_STS_URL={STS_URL}",
                    "-e", "DOCKER_STS_AGENT=false"]

if os.getenv('CURL_CA_BUNDLE'):
    AGENT_DOCKER_CMD.extend(["-e", f"CURL_CA_BUNDLE={os.getenv('CURL_CA_BUNDLE')}"]),

AGENT_DOCKER_CMD.append(TARGET_IMAGE)


def get_pyproject():
    return toml.load(Path.joinpath(PROJECT_DIR, "pyproject.toml"))


def perform_dist():
    pyproject = get_pyproject()
    commands = """
    rm -rf build/dist
    mkdir -p build/dist/checks.d build/dist/conf.d dist
    cp -r src/data/conf.d build/dist/
    cp -r src/ build/dist/checks.d
    rm -rf build/dist/checks.d/data
    find build/dist/checks.d -name "*.py" -exec rm -rf {} \;
    find build/dist/conf.d -name "conf.yaml" -exec rm -rf {} \;
    find build/dist -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null
    find build/dist -name ".DS_Store" -exec rm -rf {} \; 2>/dev/null
    py-backwards -i src -o build/dist/checks.d -t 2.7
    pdm export --prod  -o build/dist/requirements.txt
    cat <<EOF > build/dist/install.sh
    #!/bin/bash
    if test -f "./requirements.txt"; then
        echo "Installing requirement"
        sudo -u stackstate-agent /opt/stackstate-agent/embedded/bin/pip --no-cache-dir install -r ./requirements.txt
    fi
    echo "Copying config and checks to /etc/stackstate-agent"
    sudo -u stackstate-agent cp -r ./conf.d/* /etc/stackstate-agent/conf.d
    sudo -u stackstate-agent cp -r ./checks.d/* /etc/stackstate-agent/checks.d
    echo "Done".
    """
    subprocess.check_call(commands, shell=True, executable='/bin/bash', cwd=PROJECT_DIR)

    commands = """
    chmod +x build/dist/install.sh
    cd ./build/dist
    zip -r ../../dist/%s-agent-check-%s.zip *
    """ % (pyproject["project"]['name'], pyproject["project"]['version'])
    subprocess.check_call(commands, shell=True, executable='/bin/bash', cwd=PROJECT_DIR)

def prepare_agent_workspace():
    commands = """
    rm -rf build/agent
    mkdir -p build/agent/checks.d build/agent/conf.d build/agent/share
    cp -r src/data/conf.d build/agent/
    cp tests/resources/stackstate.yaml build/agent/
    cp -r tests/resources/share build/agent
    cp -r src/ build/agent/checks.d
    rm -rf build/agent/checks.d/data
    find build/agent/checks.d -name "*.py" -exec rm -rf {} \;
    py-backwards -i src -o build/agent/checks.d -t 2.7
    pdm export --prod  -o build/agent/requirements.txt
    """
    subprocess.check_call(commands, shell=True, executable='/bin/bash', cwd=PROJECT_DIR)

def clean_agent():
    _execute(["docker", "rmi", "--force", TARGET_IMAGE])

def build_agent():
    command = ["docker", "build", "-t", TARGET_IMAGE, "-f", "./tasks/dev-agent/Dockerfile", "."]
    return _execute(command)

def run_check(check_name):
    prepare_agent_workspace()
    command = []
    command.extend(AGENT_DOCKER_CMD)
    command.append("/opt/stackstate-agent/bin/run-dev-check.sh")
    command.append(check_name)
    print(" ".join(command))
    return _execute(command)

def run_agent():
    prepare_agent_workspace()
    # Check user changed template placeholders.
    if STS_API_KEY == "xxxx" or STS_URL == "https://stackstate.mycompany.com/receiver/stsAgent":
        raise Exception(f"Please update default STS_API_KEY ({STS_API_KEY}) and STS_URL({STS_URL}) in '.sts.env' file.")

    command = []
    command.extend(AGENT_DOCKER_CMD)
    command.append("/opt/stackstate-agent/bin/run-agent.sh")
    return _execute(command)


def _execute(command):
    def run_command():
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             universal_newlines=False)  # \r goes through

        nice_stdout = open(os.dup(p.stdout.fileno()), newline='')  # re-open to get \r recognized as new line
        for line in nice_stdout:
            yield line, p.poll()

        yield "", p.wait()

    for l, rc in run_command():
        print(l, end="", flush=True)
    return rc
