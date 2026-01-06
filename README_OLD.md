<div align="center">
  <img src="./Logo.png" alt="DynamicCBOM Logo" width="300" height="auto">
  
  # DynamicCBOM
  
  **Runtime Cryptography Bill of Materials Extraction using eBPF**
  
  [![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
  [![Linux](https://img.shields.io/badge/OS-Linux-orange)](https://www.linux.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![pdoc](https://img.shields.io/badge/docs-pdoc-green)](https://pdoc.dev/)

</div>

## 🎯 Overview

**DynamicCBOM** is an experimental software for extracting **Cryptography Bill of Materials (CBOM)** at runtime. It's lightweight, non-invasive, and designed for real-world tracing on Linux systems.

Using [bpftrace](https://bpftrace.org/) to dynamically trace cryptographic function calls, DynamicCBOM effectively intercepts **OpenSSL 3.x** library calls. Since many cryptography libraries in other languages are wrappers around OpenSSL (e.g., Python's `cryptography`, Node's `crypto`), tracing OpenSSL provides comprehensive coverage.

### Key Features

✨ **Non-invasive Runtime Tracing** - No code modification required  
🔍 **Comprehensive Coverage** - Tracks OpenSSL and wrapper libraries  
📊 **Standards Compliant** - CycloneDX 1.6 CBOM format  
🎨 **Publication-Quality Visualizations** - Comparison charts with metrics  
🔧 **Flexible Tracing Modes** - Attach to existing processes, system-wide, or run new targets  
⚡ **Fast & Lightweight** - eBPF-based with minimal overhead  

## 🚀 Quick Start

### Installation

```bash
# 1. Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone https://github.com/your-org/DynamicCBOM.git
cd DynamicCBOM

# 3. Install system dependencies
sudo apt install make

# 4. Build and install
uv build
uv pip install dist/dynamic_cbom-0.1.0-py3-none-any.whl

# 5. Install bpftrace
dynamic-cbom install-dependencies

# 6. Verify installation
dynamic-cbom --help
```

### First Command (30 seconds)

```bash
# Trace a Python cryptography program
dynamic-cbom run-python-test ./src/testPrograms/cryptography_symmetric.py \
  --script ./src/probes/symmetric.bt \
  --log-file ./trace.log

# Generate CBOM
dynamic-cbom parse-log ./trace.log \
  --output-path ./cbom.json

# Compare with ground truth
dynamic-cbom generate-chart ./cbom.json \
  ./src/tests/ground_truth/symmetric_cbom_gt.json \
  --output-path ./comparison.png
```

## 🔧 How It Works

DynamicCBOM leverages **eBPF (Extended Berkeley Packet Filter)** and **bpftrace** to trace cryptographic operations:

```
Your Program (using OpenSSL)
           ↓
    eBPF uprobes intercept
    cryptographic function calls
           ↓
    bpftrace captures events
           ↓
    Trace log (CSV format)
           ↓
    DynamicCBOM post-processor
           ↓
    CycloneDX CBOM JSON
    + Word cloud visualization
```

**Why eBPF?**
- Runs in kernel space (sandboxed)
- No kernel module loading required
- Minimal performance overhead
- No source code modification needed

## 📋 Available Commands

| Command | Purpose | Use Case |
|---------|---------|----------|
| `banner` | Display logo | Verify installation |
| `install-dependencies` | Setup bpftrace | First-time setup |
| `attach-pid` | Trace existing process | Monitor running app |
| `global-trace` | System-wide tracing | Find all crypto usage |
| `run-new-target` | Run program + trace | Test new executable |
| `run-python-test` | Trace Python program | Test Python crypto |
| `parse-log` | Log → CBOM conversion | Process bpftrace output |
| `generate-chart` | CBOM comparison | Visualize results |

**Example:**
```bash
# Trace by process ID
dynamic-cbom attach-pid 12345 --script ./src/probes/algorithms.bt

# System-wide tracing
dynamic-cbom global-trace --script ./src/probes/tls.bt

# Run and trace (note the --)
dynamic-cbom run-new-target -- ./myapp --config config.json
```

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICKSTART.md)** - 5-minute installation tutorial
- **[Installation Guide](docs/QUICKSTART.md#installation-steps)** - Detailed setup instructions

### Usage & Reference
- **[Command Reference](docs/COMMAND_REFERENCE.md)** - All 9 commands with examples
- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive usage guide
- **[API Documentation](docs/API_REFERENCE.md)** - Function and class reference

### Understanding the System
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and components
- **[Class Diagram](#class-diagram)** - Visual component structure

### Publishing & Distribution
- **[PyPI Guide](docs/PYPI_GUIDE.md)** - Publish to Python Package Index

## 📊 System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Linux (Ubuntu 20.04+, Debian 11+) |
| **Kernel** | 4.8+ (for eBPF support) |
| **Python** | 3.12 or later |
| **Privileges** | sudo access (for bpftrace) |
| **Disk** | ~500MB free |

**Note:** WSL2 and containers may have limited eBPF support.

## 🛠️ Prerequisites

- **bpftrace**: Installed automatically via `dynamic-cbom install-dependencies`
- **uv**: Python package manager ([install](https://docs.astral.sh/uv/))
- **make**: Build tool (`sudo apt install make`)
- **OpenSSL 3.x**: Usually pre-installed on modern Linux

## 📦 Installation Methods

### Method 1: Direct from Source (Recommended)
```bash
uv build
uv pip install dist/dynamic_cbom-0.1.0-py3-none-any.whl
```

### Method 2: Using pip
```bash
cd src
pip install -e .
```

### Method 3: Docker (Alternative)
```bash
docker build -t dynamic-cbom .
docker run --privileged -it dynamic-cbom bash
```

## 🎓 Usage Examples

### Example 1: Trace a Running Process

```bash
# Find process
PID=$(pgrep -f myapp)

# Attach tracing
dynamic-cbom attach-pid $PID \
  --script ./src/probes/algorithms.bt \
  --log-file ./myapp_trace.log

# Process results
dynamic-cbom parse-log ./myapp_trace.log \
  --output-path ./myapp_cbom.json --verbose
```

### Example 2: Compare CBOMs

```bash
# Generate comparison chart
dynamic-cbom generate-chart \
  ./dynamic_cbom.json \
  ./ground_truth_cbom.json \
  --ibm-cbom-path ./ibm_cbom.json \
  --output-path ./comparison.png
```

### Example 3: Test Suite

```bash
# Run multiple tests
for test in src/testPrograms/*.py; do
  dynamic-cbom run-python-test "$test" \
    --script ./src/probes/algorithms.bt \
    --log-file "$(basename $test .py).log"
  dynamic-cbom parse-log "$(basename $test .py).log" \
    --output-path "$(basename $test .py).json"
done
```

## 🏗️ Architecture

DynamicCBOM uses a modular architecture with clear separation of concerns:

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