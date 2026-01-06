"""Log post-processing module for generating CycloneDX Bill of Materials.

This module provides functionality to parse bpftrace logs, extract cryptographic
operations, and generate CycloneDX Bill of Materials (CBOM) documents based on
configurable rules.
"""

from __future__ import annotations

import datetime
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import rule_engine
import yaml
from wordcloud import WordCloud

from interface.config import settings


@dataclass
class CompiledRule:
    """A compiled rule-engine rule with associated CBOM metadata.

    Attributes:
        id: Unique identifier for the rule.
        priority: Numeric priority (higher values take precedence).
        rule: Compiled rule-engine Rule object.
        primitive: Cryptographic primitive type (e.g., 'symmetric', 'asymmetric').
        crypto_functions: List of cryptographic function names.
        extra: Additional metadata dictionary.
    """

    id: str
    priority: int
    rule: rule_engine.Rule
    primitive: str
    crypto_functions: List[str]
    extra: Dict[str, Any]


class LogPostProcessor:
    """Post-processes bpftrace logs and generates CycloneDX CBOM documents.

    Loads cryptographic rules from a YAML configuration, parses bpftrace logs
    into a structured format, applies matching rules, and produces standardized
    CBOM output in JSON format.

    Attributes:
        yaml_path: Path to the YAML rules file.
        verbose: Enable verbose logging output.
    """

    def __init__(self, yaml_path: str = settings.default_rules_path, verbose: bool = False) -> None:
        """Initialize the log post-processor.

        Args:
            yaml_path: Path to the YAML rules configuration file.
            verbose: If True, print detailed processing information.
        """
        self.yaml_path = yaml_path
        self.verbose = verbose
        self.defaults: Dict[str, Any] = {}
        self._rules: List[CompiledRule] = []
        self._context = rule_engine.Context(default_value=None)
        self._load_rules()

    def print_pandas_intermediate_results(self, log_file: str) -> None:
        """Print intermediate pandas aggregation results for debugging.

        Args:
            log_file: Path to the bpftrace log file.
        """
        df = self._load_and_summarize_log(log_file)
        df_aggregated = df.sort_values(by=["proc", "func", "timestamp"])
        df_aggregated = df_aggregated.groupby(["proc", "func"], as_index=False).agg(
            {
                "timestamp": ["min", "max", "count"],
                "op": lambda ops: list(ops.unique()),
                "pid": lambda pids: list(pids.unique()),
            }
        )
        df_aggregated.columns = ["_".join(col).strip("_") for col in df_aggregated.columns.values]

    def generate_wordCloud(self, log_file: str, output_path: str) -> None:
        """Generate a word cloud visualization from crypto function names.

        Creates a word cloud image based on the frequency of cryptographic
        functions found in the log file. Each function is weighted by its
        occurrence count.

        Args:
            log_file: Path to the bpftrace log file.
            output_path: Path where the word cloud image will be saved.
        """
        df = self._load_and_summarize_log(log_file)
        text = ""
        for record in df.itertuples():
            for _ in range(record.count):
                text += " " + record.op

        if self.verbose:
            print("Generating word cloud...")
            print(text)

        wordcloud = WordCloud(
            width=800, height=400, background_color="white", regexp=r"\S+"
        ).generate(text)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(output_path)
        if self.verbose:
            print(f"Word cloud saved to {output_path}")

    def _load_and_summarize_log(self, log_file: str) -> pd.DataFrame:
        """Load and parse bpftrace log file into a structured DataFrame.

        Performs extensive parsing and normalization:
        1. Read CSV with pipe separators
        2. Trim whitespace from string columns
        3. Convert timestamp and PID to appropriate types
        4. Extract function names from uprobe events
        5. Normalize operation names (uppercase)
        6. Filter and merge EVP function calls
        7. Map pointer relationships for EVP context objects
        8. Clean and normalize extra metadata fields
        9. Aggregate identical records with counts
        10. Map OpenSSL function names to generic operations

        Args:
            log_file: Path to the bpftrace log file.

        Returns:
            Processed DataFrame with columns: op, func, extra, count.
        """
        # 1) Read using regex separator
        df = pd.read_csv(
            log_file,
            sep=r"\s*\|\s*",
            engine="python",
            header=None,
            names=["proc", "event", "timestamp", "pid", "op", "extra"],
            skip_blank_lines=True,
        )
        if self.verbose:
            print(f"Loaded {len(df)} log entries from {log_file}")

        # 2) Trim whitespace from string columns
        for c in ["proc", "event", "op", "extra"]:
            df[c] = df[c].astype(str).str.strip()
        if self.verbose:
            print("Trimmed whitespace from string columns.")

        # 3) Convert timestamp and PID to appropriate types
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["pid"] = pd.to_numeric(df["pid"], errors="coerce").astype("Int64")
        if self.verbose:
            print("Converted timestamp and pid columns.")

        # 4) Extract function names from uprobe events (format: "uprobe:/lib/...:FuncName")
        parts = df["event"].str.split(":", n=2, expand=True)
        df["func"] = parts[2]
        del df["event"]
        if self.verbose:
            print("Extracted function names from event column.")

        # 5) Normalize column data
        df["op"] = df["op"].str.upper()
        del df["proc"]
        del df["pid"]
        del df["timestamp"]
        if self.verbose:
            print("Normalized operation names and removed metadata columns.")

        # 6) Filter out EVP_KEYMGMT_fetch (not needed for analysis)
        df = df[df["func"] != "EVP_KEYMGMT_fetch"].reset_index(drop=True)

        # 7) Merge EVP fetch operations with preceding init operations
        i = 1
        while i < len(df):
            if re.search(r"EVP.*CIPHER_fetch$", df.at[i, "func"]) or re.search(
                r"EVP_SIGNATURE_fetch$", df.at[i, "func"]
            ):
                prev_func = df.at[i - 1, "func"]
                if re.search(r"EVP_PKEY_.*_init$", prev_func) or re.search(
                    r"EVP_.*Init.*$", prev_func
                ):
                    df.at[i - 1, "op"] = df.at[i, "op"]
                    df = df.drop(i).reset_index(drop=True)
            i += 1

        # 8) Remove init functions with missing operation data
        df = df[
            ~(
                (df["op"] == "NAN")
                & (
                    df["func"].str.contains(r"EVP_PKEY_.*_init$", regex=True, na=False)
                    | df["func"].str.contains(r"EVP_.*Init.*$", regex=True, na=False)
                )
            )
        ].reset_index(drop=True)
        if self.verbose:
            print("Removed incomplete init function records.")

        # 9) Process EVP_PKEY_CTX_new pointer relationships to extract key sizes
        self._extract_pkey_sizes(df)
        if self.verbose:
            print("Processed EVP_PKEY_CTX_new pointer relationships.")

        # 10) Remove EVP context tracking rows (no longer needed)
        df = df[~df["func"].isin(["EVP_PKEY_CTX_new", "EVP_PKEY_get_size"])].reset_index(drop=True)
        if self.verbose:
            print("Removed EVP context tracking rows.")

        # 11) Aggregate identical records by operation, extra metadata, and function
        df["count"] = 1
        df = df.groupby(["op", "extra", "func"], as_index=False).agg({"count": "sum"})
        if self.verbose:
            print("Aggregated identical records with counts.")

        # 12) Clean pointer references from extra metadata
        self._clean_pointer_metadata(df)
        if self.verbose:
            print("Cleaned pointer metadata from extra field.")

        # 13) Aggregate functions by operation
        df = df.groupby(["op"], as_index=False).agg(
            {
                "func": lambda funcs: list(funcs.unique()),
                "count": "sum",
                "extra": lambda extras: ",".join(extras.unique()),
            }
        )
        if self.verbose:
            print("Aggregated functions by operation.")

        # 14) Map OpenSSL function names to generic operations
        self._map_function_names(df)

        if self.verbose:
            print("Final processed DataFrame:")
            print(df.to_string())

        return df

    def _extract_pkey_sizes(self, df: pd.DataFrame) -> None:
        """Extract key sizes from EVP_PKEY_CTX_new pointer relationships.

        Searches for EVP_PKEY_get_size rows and adds the key size to the
        corresponding EVP_PKEY_*_init rows based on pointer tracking.

        Args:
            df: DataFrame with log records.
        """
        for i in range(len(df)):
            if df.at[i, "func"] != "EVP_PKEY_CTX_new":
                continue

            extra = df.at[i, "extra"]
            prev_match = re.search(r"prev=\s*(0x[0-9a-fA-F]+)", extra)
            next_match = re.search(r"next=\s*(0x[0-9a-fA-F]+)", extra)

            if not (prev_match or next_match):
                continue

            prev_ptr = int(prev_match.group(1), 16) if prev_match else None
            next_ptr = int(next_match.group(1), 16) if next_match else None

            # Find corresponding EVP_PKEY_get_size row
            size_row_index = None
            for j in range(len(df)):
                if df.at[j, "func"] == "EVP_PKEY_get_size":
                    size_extra = df.at[j, "extra"]
                    size_next_match = re.search(r"next=\s*(\d+)", size_extra)
                    if size_next_match and int(size_next_match.group(1)) == prev_ptr:
                        size_row_index = j
                        break

            # Find corresponding EVP_PKEY_*_init row
            init_row_index = None
            for k in range(len(df)):
                if re.search(r"EVP_PKEY_.*_init$", df.at[k, "func"]):
                    init_extra = df.at[k, "extra"]
                    init_prev_match = re.search(r"prev=\s*(0x[0-9a-fA-F]+)", init_extra)
                    if init_prev_match and int(init_prev_match.group(1), 16) == next_ptr:
                        init_row_index = k
                        break

            # Propagate key size to init row
            if init_row_index is not None and size_row_index is not None:
                size_extra = df.at[size_row_index, "extra"]
                pkey_size_match = re.search(r"pkey_size=\s*(\d+)", size_extra)
                if pkey_size_match:
                    pkey_size = pkey_size_match.group(1)
                    df.at[init_row_index, "extra"] = f"pkey_size={pkey_size}"

    def _clean_pointer_metadata(self, df: pd.DataFrame) -> None:
        """Remove pointer addresses from extra metadata field.

        Args:
            df: DataFrame with log records.
        """
        for i in range(len(df)):
            extra = df.at[i, "extra"]
            extra = re.sub(r"prev=\s*0x[0-9a-fA-F]+\s*,?\s*", "", extra)
            extra = re.sub(r"next=\s*0x[0-9a-fA-F]+\s*,?\s*", "", extra)
            extra = extra.strip().strip(",")
            df.at[i, "extra"] = extra if extra else "nan"

    def _map_function_names(self, df: pd.DataFrame) -> None:
        """Map OpenSSL function names to generic operation names.

        Converts OpenSSL EVP function names to their semantic operations
        (e.g., EVP_PKEY_encrypt_init -> 'encrypt').

        Args:
            df: DataFrame with log records.
        """
        function_mapping = {
            "EVP_PKEY_encrypt_init": "encrypt",
            "EVP_PKEY_decrypt_init": "decrypt",
            "EVP_PKEY_sign_init": "sign",
            "EVP_PKEY_verify_init": "verify",
            "EVP_EncryptInit_ex": "encrypt",
            "EVP_DecryptInit_ex": "decrypt",
        }

        for i in range(len(df)):
            funcs = df.at[i, "func"]
            mapped_funcs = [
                function_mapping.get(func, func) for func in funcs if func in function_mapping
            ]
            df.at[i, "func"] = mapped_funcs

    def _load_rules(self) -> None:
        """Load and compile cryptographic rules from YAML configuration.

        Reads the rules file, compiles rule-engine expressions, and sorts
        rules by priority (highest first).
        """
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        self.defaults = cfg.get(
            "defaults",
            {"primitive": "other", "cryptoFunctions": []},
        )

        rules_cfg = cfg.get("rules", [])
        compiled: List[CompiledRule] = []

        for rc in rules_cfg:
            expr = rc["expr"]
            rule_id = rc.get("id", expr)
            priority = int(rc.get("priority", 0))
            primitive = rc["primitive"]
            crypto_functions = list(rc.get("cryptoFunctions", []))
            extra = dict(rc.get("extra", {}))

            re_rule = rule_engine.Rule(expr, context=self._context)

            compiled.append(
                CompiledRule(
                    id=rule_id,
                    priority=priority,
                    rule=re_rule,
                    primitive=primitive,
                    crypto_functions=crypto_functions,
                    extra=extra,
                )
            )

        compiled.sort(key=lambda r: r.priority, reverse=True)
        self._rules = compiled

    def _translate_into_CBOM_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Translate processed log data into CycloneDX CBOM format.

        Matches records against configured rules and creates CycloneDX
        components with cryptographic properties.

        Args:
            df: Processed DataFrame with log records.

        Returns:
            CBOM dictionary in CycloneDX 1.6 format.
        """
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        cbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {"timestamp": now, "tools": {"components": [], "services": []}},
            "components": [],
        }

        dicts = df.to_dict(orient="records")

        # Parse extra metadata from comma-separated key=value format
        for record in dicts:
            extra_str = record.get("extra", "")
            extra_dict = {}
            for part in extra_str.split(","):
                if "=" in part:
                    key, value = part.split("=", 1)
                    extra_dict[key.strip()] = value.strip()
            record["extra"] = extra_dict

        # Apply rules and create CBOM components
        for record in dicts:
            for rule in self._rules:
                if rule.rule.matches(record):
                    component = {
                        "type": "cryptographic-asset",
                        "bom-ref": str(uuid.uuid4()),
                        "name": record["op"],
                        "cryptoProperties": {
                            "assetType": "algorithm",
                            "algorithmProperties": {
                                "primitive": rule.primitive,
                                "cryptoFunctions": record["func"],
                                "parameterSetIdentifier": (
                                    int(record["extra"]["pkey_size"]) * 8
                                    if "pkey_size" in record["extra"]
                                    else None
                                ),
                            },
                        },
                    }
                    cbom["components"].append(component)
        return cbom

    def _save_cbom_to_file(self, cbom: Dict[str, Any], output_path: str) -> None:
        """Save CBOM dictionary to a JSON file.

        Args:
            cbom: CBOM dictionary to save.
            output_path: Destination file path.
        """
        path = Path(output_path)

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                cbom,
                f,
                ensure_ascii=False,
                indent=2,
            )

    def process_log(self, log_file: str, output_path: str) -> None:
        """Process a bpftrace log file and generate a CBOM JSON file.

        Args:
            log_file: Path to the input bpftrace log file.
            output_path: Path where the CBOM JSON file will be written.
        """
        df = self._load_and_summarize_log(log_file)
        cbom = self._translate_into_CBOM_format(df)
        self._save_cbom_to_file(cbom, output_path=output_path)
