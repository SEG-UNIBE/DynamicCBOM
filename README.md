![](./logo_compressed.png)

## Introduction

**Dynamic CBOM** is an experimental software for testing the feasibility of extracting **Cryptography Bill of Materials  (CBOM)** at runtime. It's lightweight, non-invasive, and designed for real-world tracing on Linux systems.

It essentially uses [bpftrace](https://bpftrace.org/) to dynamically trace the callings of cryptographic functions inside a program. To our current knowledge, it can effectively intercept all the callings for **OpenSSL** and other cryptography libraries implemented in C. Note that quite a lot cryptography libraries in other languages are just wrappers of OpenSSL, such as **Python Cryptography**. Hence, by tracing only OpenSSL, we are able to trace the usage of other cryptography libraries. 



## How does it work?

**bpftrace** is based on a concept [eBPF](https://ebpf.io/what-is-ebpf/). eBPF is a revolutionary technology with origins in the Linux kernel that can run sandboxed programs in a privileged context such as the operating system kernel. It is used to safely and efficiently extend the capabilities of the kernel without requiring to change kernel source code or load kernel modules. From the figure below, we can see that eBPF can also do Tracing task in user space, tracing some user space function calls. 

What eBPF does to intercept function calls is to **plant breakpoints** on a user space function in a binary or shared library.

bpftrace is a high-level tracing language for Linux and provides a quick and easy way for people to write observability-based eBPF programs, especially those unfamiliar with the complexities of eBPF.

![](https://ebpf.io/static/e293240ecccb9d506587571007c36739/f2674/overview.png)

## Prerequisite

- for simplicity, our implementation mainly focus on interception of OpenSSL 3.4 which is by default available in Ubuntu 25. 
- The repository is based on [uv](https://docs.astral.sh/uv/) which is a Python package and project manager. It needs to be installed firstly.

## Install

After cloning this repository, you can run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt install make
uv build
uv pip install dist/dynamic_cbom-0.1.0-py3-none-any.whl
```

Then you should able to run dynamic-cbom command:

```bash
dynamic-cbom --help
```

## Class Diagram

```mermaid
classDiagram
direction TB

%% ==== Core CLI ====
class ClientCLI {
  <<module>>
  +install_dependencies()
  +uninstall_dependencies()
  +attach_by_pid(pids, script, log_file?)
  +global_trace(script, log_file?)
  +run_new_target(command, script, log_file?)
  +run_python_test(test_program, script, log_file?)
}

%% ==== Option handlers (one per mode) ====
class AttachByPID {
  +run(pids: List~int~, script: str, log_file: str?)
}
class GlobalTrace {
  +run(script: str, log_file: str?)
}
class RunNewTarget {
  +run(command: str, script: str, log_file: str?)
}
class RunPythonTest {
  +run(test_program: str, script: str, log_file: str?)
}

%% ==== Execution wrapper around bpftrace ====
class BpftraceWrapper {
  +__init__(bpftrace_binary: str)
  +start(script: str, log_file: str, extra_args: List~str~)
}

class BpftraceError {
  <<exception>>
}

%% ==== Config & Utilities ====
class Config {
  <<config>>
  +settings: Dynaconf
  -- defaults from settings.toml --
  -default_bpftrace_binary_path: str
  -default_bpftrace_script_path: str
  -default_log_path: str
  -bpftrace_download_url: str
}

class DependencyInstaller {
  <<singleton>>
  +check()
  +install_bpftrace()
  +install_bpftrace_scripts()
  +uninstall_bpftrace()
  +uninstall_bpftrace_scripts()
  +install()
  +uninstall()
}

class SingletonMeta {
  <<metaclass>>
  +__call__(...)
}

class PostParser {
  +parse_log(path: str): ParsedResult
}

%% ==== Relationships ====
ClientCLI --> AttachByPID      : uses
ClientCLI --> GlobalTrace      : uses
ClientCLI --> RunNewTarget     : uses
ClientCLI --> RunPythonTest    : uses
ClientCLI --> DependencyInstaller : installs/removes deps
ClientCLI --> PostParser       : optional post-processing

AttachByPID --> BpftraceWrapper   : delegates start()
GlobalTrace --> BpftraceWrapper   : delegates start()
RunNewTarget --> BpftraceWrapper  : delegates start()
RunPythonTest --> BpftraceWrapper : delegates start()

AttachByPID ..> Config        : reads defaults
GlobalTrace ..> Config        : reads defaults
RunNewTarget ..> Config       : reads defaults
RunPythonTest ..> Config      : reads defaults
BpftraceWrapper ..> Config    : reads defaults
DependencyInstaller ..> Config: reads defaults

RuntimeError <|-- BpftraceError  : inherits
DependencyInstaller ..> SingletonMeta : metaclass

```



## Workflow

```mermaid
flowchart TD
  A[Start] --> D[Run CLI dynamic-cbom COMMAND]
  D --> E{Dependencies available}

  E -- No --> F[Install dependencies]
  F --> G{Install succeeded}
  G -- No --> X1[Abort install error]
  G -- Yes --> H[Proceed]
  E -- Yes --> H[Proceed]

  H --> M{Choose tracing mode}
  M --> P1[attach-by-pid]
  M --> P2[global-trace]
  M --> P3[run-new-target]
  M --> P4[run-python-test]

  P1 --> I1[Provide PIDs and optional script and log]
  P2 --> I2[Provide optional script and log]
  P3 --> I3[Provide command and optional script and log]
  P4 --> I4[Provide test py and optional script and log]

  I1 --> W[Start bpftrace]
  I2 --> W
  I3 --> W
  I4 --> W

  W --> CMD[Spawn sudo bpftrace with args and script]
  CMD --> LOG[Stream to log file]

  LOG --> PARSE{Parse results}
  PARSE -- Yes --> PP[PostParser creates summary]
  PARSE -- No --> END[Done]
  PP --> OUT[Done with log and summary]

  %% Common errors
  I1 -- script not found --> X2[Error invalid script path]
  I4 -- test py not found --> X3[Error invalid test path]
  CMD -- permission error --> X4[Error check sudo or binary path]

```

```mermaid
---
config:
  layout: dagre
  look: neo
  theme: redux
---
flowchart TB
    S(["Start"]) --> DEP{"Dependencies ready?"}
    DEP -- No --> INST["Dependency Manager"]
    INST -- success --> MODE["Mode Router"]
    INST -- fail --> ERR["Abort"]
    DEP -- Yes --> MODE
    MODE -- invalid input --> ERR
    MODE --> RUN["Bpftrace Runner"]
    RUN -- permission or binary error --> ERR
    RUN --> POST["Log Parser"]
    POST --> DONE(["End"])

    %% Styles (matching the provided template vibe)
    style S stroke:#000000,fill:#E1F0D4
    style DEP stroke:#000000,fill:#F2F7D2
    style INST stroke:#000000,fill:#C3EFE0
    style MODE stroke:#000000,fill:#A3E9CC
    style RUN stroke:#000000,fill:#D4EFF0
    style POST stroke:#000000,fill:#DBCDF8
    style ERR stroke:#000000,fill:#E9A3B2
    style DONE stroke:#000000,fill:#BEF6AC

```


```mermaid
---
config:
  layout: dagre
  look: neo
  theme: redux
---
flowchart TD
 subgraph Install_deps["Install dependencies"]
        Install_bpftrace["Install bpftrace"]
        Build_bpftrace_script["Build bpftrace script"]
  end
    Install_deps --> G{"Install succeeded"}
    G -- No --> X1["Abort"]
    G -- Yes --> H["Mode Router"]
    style Install_bpftrace stroke:#000000,fill:#C3EFE0
    style Build_bpftrace_script stroke:#000000,fill:#D4EFF0
    style Install_deps stroke:#000000,fill:#F6ACD8
    style G stroke:#000000,fill:#F2F7D2
    style X1 stroke:#000000,fill:#E9A3B2
    style H stroke:#000000,fill:#A3E9CC


```


```mermaid
---
config:
  layout: elk
  look: neo
  theme: redux
---
flowchart TD
    M{"Choose tracing mode"} --> P1["attach-by-pid"] & P2["global-trace"] & P3["run-new-target"] & P4["run-python-test"]
    P1 --> I1["Provide PIDs and optional script and log"]
    P2 --> I2["Provide optional script and log"]
    P3 --> I3["Provide command and optional script and log"]
    P4 --> I4["Provide test py and optional script and log"]
    I1 --> W["Bpftrace Runner"] & ERR["Abort"]
    I2 --> W & ERR
    I3 --> W & ERR
    I4 --> W & ERR

    %% Pretty styles (matching your template palette)
    style M stroke:#000000,fill:#F2F7D2
    style P1 stroke:#000000,fill:#C3EFE0
    style P2 stroke:#000000,fill:#A3E9CC
    style P3 stroke:#000000,fill:#BEF6AC
    style P4 stroke:#000000,fill:#E1F0D4

    style I1 stroke:#000000,fill:#FFFAAF
    style I2 stroke:#000000,fill:#FFFAAF
    style I3 stroke:#000000,fill:#FFFAAF
    style I4 stroke:#000000,fill:#FFFAAF

    style W stroke:#000000,fill:#D4EFF0
    style ERR stroke:#000000,fill:#E9A3B2



```


```mermaid
---
config:
  layout: dagre
  look: neo
  theme: redux
---
flowchart TD
    W["Build bpftrace command"] --> CMD["Spawn sudo bpftrace with args and script"]
    CMD --> LOG["Stream to log file"]
    CMD -- permission error --> X4["Abort"]

    %% Pretty styles (palette consistent with earlier charts)
    %% Note: same names keep same colors — "Abort" stays pink.
    style W stroke:#000000,fill:#D4EFF0
    style CMD stroke:#000000,fill:#C3EFE0
    style LOG stroke:#000000,fill:#DBCDF8
    style X4 stroke:#000000,fill:#E9A3B2


```


```mermaid

flowchart TD

  PARSE[Use Pandas to parse log file]
  DEDUP[Deduplicate entries]
  AGGR[Aggregate entries by process, function etc.]
  EXTRA[Filter out entries which reveal cryptographic properties]
  OUT[Concat and output]

  PARSE --> DEDUP
  DEDUP --> AGGR
  DEDUP --> EXTRA
  AGGR --> OUT
  EXTRA --> OUT

  %% Pretty styles (consistent palette; same names keep same colors across charts)
  style PARSE stroke:#000000,fill:#DBCDF8
  style DEDUP stroke:#000000,fill:#A3E9CC
  style AGGR stroke:#000000,fill:#E1F0D4
  style EXTRA stroke:#000000,fill:#F6ACD8
  style OUT stroke:#000000,fill:#BEF6AC

```