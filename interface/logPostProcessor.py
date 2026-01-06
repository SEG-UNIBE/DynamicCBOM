from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple
from interface.config import settings

import pandas as pd
import rule_engine
import yaml
import uuid
import datetime
import json
from pathlib import Path
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud

@dataclass
class CompiledRule:
    """One compiled rule-engine rule plus CBOM metadata."""
    id: str
    priority: int
    rule: rule_engine.Rule
    primitive: str
    crypto_functions: List[str]
    extra: Dict[str, Any]

class LogPostProcessor:
    def __init__(self, yaml_path: str = settings.default_rules_path, verbose: bool = False) -> None:
        self.yaml_path = yaml_path
        self.verbose = verbose
        self.defaults: Dict[str, Any] = {}
        self._rules: List[CompiledRule] = []
        self._context = rule_engine.Context(
            # If a rule references a symbol we don't pass, it becomes NULL,
            # which is falsy; that’s convenient for us.
            default_value=None
        )
        self._load_rules()
        
    def print_pandas_intermediate_results(self, log_file: str) -> None:
        df = self._load_and_summarize_log(log_file)
        # 7) aggregate by proc, func, with min/max timestamp and the list of ops
        df_aggregated = df.sort_values(by=["proc", "func", "timestamp"])
        df_aggregated = df_aggregated.groupby(["proc", "func"], as_index=False).agg({
            "timestamp": ["min", "max", "count"],
            "op": lambda ops: list(ops.unique()),
            "pid": lambda pids: list(pids.unique()),
        })
        df_aggregated.columns = ['_'.join(col).strip('_') for col in df_aggregated.columns.values]

        # 8) get records that have extra info
        info_records = df[df["extra"] != "nan"]

        # # print all
        # print(df_aggregated.to_string())
        # print(info_records.to_string())
    
    def generate_wordCloud(self, log_file: str, output_path: str) -> None:
        """Generate a wordcloud from the 'func' column of the log DataFrame."""
        

        df = self._load_and_summarize_log(log_file)
        text = ''
        for record in df.itertuples():
            for _ in range(record.count):
                # strip "-" from op
                text += ' ' + record.op
        
        if self.verbose:
            print("Generating wordcloud...")
            print(text)
                    
        
        # make wordcloud not split on "-"
        wordcloud = WordCloud(width=800, height=400, background_color='white', regexp=r'\S+').generate(text)
        
        
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(output_path)
        if self.verbose:
            print(f"Wordcloud saved to {output_path}")
    
        
        
    def _load_and_summarize_log(self, log_file: str):
        """Load and parse the log file into a DataFrame."""
        # 1) Read using a regex separator (engine='python' required)
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
            

        # 2) Trim whitespace
        for c in ["proc", "event", "op", "extra"]:
            df[c] = df[c].astype(str).str.strip()
        if self.verbose:
            print("Trimmed whitespace from string columns.")

        # 3) Convert types
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["pid"] = pd.to_numeric(df["pid"], errors="coerce").astype("Int64")
        if self.verbose:
            print("Converted timestamp and pid columns to appropriate types.")
            
        # 4) Split 'event' (format like "uprobe:/lib/...:FuncName") into probe, lib, func
        parts = df["event"].str.split(":", n=2, expand=True)
        df["func"] = parts[2]
        
        del df["event"]
        
        if self.verbose:
            print("Extracted function names from event column.")

        # 5) Canonicalize Column data
        df['op'] = df['op'].str.upper()
        del df['proc']
        del df['pid']
        del df['timestamp']
        
        if self.verbose:
            print("Removed proc, pid, and timestamp columns.")
        
        # ignore rows where func is EVP_KEYMGMT_fetch
        df = df[df['func'] != 'EVP_KEYMGMT_fetch'].reset_index(drop=True)
        
        
        # print(df.to_string())
        
        # 6) for each row with func name "EVP_*_fetch", if last row func name is "EVP_PKEY_*_init" or "EVP_*Init*", merge the op value into that row's extra field
        i = 1
        while i < len(df):  
            if re.search(r'EVP.*CIPHER_fetch$', df.at[i, 'func']) or re.search(r'EVP_SIGNATURE_fetch$', df.at[i, 'func']):
                prev_func = df.at[i-1, 'func']
                if re.search(r'EVP_PKEY_.*_init$', prev_func) or re.search(r'EVP_.*Init.*$', prev_func):
                    df.at[i-1, 'op'] = df.at[i, 'op']
                    df = df.drop(i).reset_index(drop=True)
            i += 1
        
        # print(df.to_string())
        # clear out rows with func name "EVP_PKEY_.*_init$" or "EVP_.*Init_ex$" that have no op
        df = df[~((df['op'] == 'NAN') & (df['func'].str.contains(r'EVP_PKEY_.*_init$', regex=True, na=False) | df['func'].str.contains(r'EVP_.*Init.*$', regex=True, na=False)))].reset_index(drop=True)
        
        if self.verbose:
            print("Cleared out rows with no op for certain init functions.")
        
        # 7) for each row(thisRow) with func name "EVP_PKEY_CTX_new" with prev and next:
        #        establish dict: thisRow.prev -> thisRow.next and thisRow.next -> thisRow.prev
        #        find next first get_size row(sizeRow) with sizeRow.next == thisRow.prev, modify thisRow.next -> sizeRow.pkey_size
        #        find next first EVP_PKEY_*_init(initRow) with initRow.prev == thisRow.next, add sizeRow.pkey_size to initRow.extra
       
        for i in range(len(df)):
            if df.at[i, 'func'] == 'EVP_PKEY_CTX_new':
                pkey_ctx_map: Dict[int, int] = {}
                extra = df.at[i, 'extra']
                # parse prev and next pointers
                prev_match = re.search(r'prev=\s*(0x[0-9a-fA-F]+)', extra)
                next_match = re.search(r'next=\s*(0x[0-9a-fA-F]+)', extra)
                assert prev_match or next_match, "EVP_PKEY_CTX_new row must have prev or next"
                # convert hex to int
                prev_ptr = int(prev_match.group(1), 16)
                next_ptr = int(next_match.group(1), 16)
                print(f"Mapping EVP_PKEY_CTX_new prev {prev_ptr} <-> next {next_ptr}")
                pkey_ctx_map[prev_ptr] = next_ptr
                pkey_ctx_map[next_ptr] = prev_ptr
                # Find sizeRow
                size_row_index = None
                for j in range(len(df)):
                    if df.at[j, 'func'] == 'EVP_PKEY_get_size':
                        size_extra = df.at[j, 'extra']
                        size_next_match = re.search(r'next=\s*(\d+)', size_extra)
                        if size_next_match and int(size_next_match.group(1)) == prev_ptr:
                            size_row_index = j
                            break
                # Find initRow
                init_row_index = None
                for k in range(len(df)):
                    if re.search(r'EVP_PKEY_.*_init$', df.at[k, 'func']):
                        init_extra = df.at[k, 'extra']
                        init_prev_match = re.search(r'prev=\s*(0x[0-9a-fA-F]+)', init_extra)
                        if init_prev_match and int(init_prev_match.group(1), 16) == next_ptr:
                            init_row_index = k
                            break
                # If initRow found, add sizeRow.pkey_size to initRow.extra
                if init_row_index is not None and size_row_index is not None:
                    size_extra = df.at[size_row_index, 'extra']
                    pkey_size_match = re.search(r'pkey_size=\s*(\d+)', size_extra)
                    pkey_size = pkey_size_match.group(1)
                    df.at[init_row_index, 'extra'] = f"pkey_size={pkey_size}"
        
        if self.verbose:
            print("Processed EVP_PKEY_CTX_new relationships to extract pkey_size.")
        
        # 8) Remove rows with func name "EVP_PKEY_CTX_new" and "EVP_PKEY_get_size"
        df = df[~df['func'].isin(['EVP_PKEY_CTX_new', 'EVP_PKEY_get_size'])].reset_index(drop=True)
        
        if self.verbose:
            print("Removed EVP_PKEY_CTX_new and EVP_PKEY_get_size rows.")
        
        # 9) group the same records together, summing counts
        df['count'] = 1
        df = df.groupby(['op', 'extra', 'func'], as_index=False).agg({
            'count': 'sum',
        })
        if self.verbose:
            print("After grouping similar records:")
            # print(df.to_string())
        
        
        # clean up all prev and next from extra
        for i in range(len(df)):
            extra = df.at[i, 'extra']
            extra = re.sub(r'prev=\s*0x[0-9a-fA-F]+\s*,?\s*', '', extra)
            extra = re.sub(r'next=\s*0x[0-9a-fA-F]+\s*,?\s*', '', extra)
            extra = extra.strip().strip(',')
            df.at[i, 'extra'] = extra if extra else 'nan'
        
        if self.verbose:
            print("Cleaned up prev and next pointers from extra field.")
        
            
        
        # 10) if op and extra are the same, concat the func into list
        # df = df.sort_values(by=["proc", "op", "extra", "func", "timestamp"])
        df = df.groupby(["op"], as_index=False).agg({
            "func": lambda funcs: list(funcs.unique()),
            "count": "sum",
            "extra": lambda extras: ','.join(extras.unique()),
        })
        # df.columns = ['_'.join(col).strip('_') for col in df.columns.values]
        if self.verbose:
            print("Aggregated functions by op and extra fields.")
        
        
        # 11) map EVP_PKEY_encrypt_init to encrypt, and so on for decrypt, sign, verify
        for i in range(len(df)):
            funcs = df.at[i, 'func']
            mapped_funcs = []
            for func in funcs:
                if func == 'EVP_PKEY_encrypt_init':
                    mapped_funcs.append('encrypt')
                elif func == 'EVP_PKEY_decrypt_init':
                    mapped_funcs.append('decrypt')
                elif func == 'EVP_PKEY_sign_init':
                    mapped_funcs.append('sign')
                elif func == 'EVP_PKEY_verify_init':
                    mapped_funcs.append('verify')
                elif func == 'EVP_EncryptInit_ex':
                    mapped_funcs.append('encrypt')
                elif func == 'EVP_DecryptInit_ex':
                    mapped_funcs.append('decrypt')
            
            df.at[i, 'func'] = mapped_funcs
        
        print(df.to_string())
        
        return df
        
    def _load_rules(self) -> None:
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

            # Compile rule-engine expression
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

        # Highest priority first
        compiled.sort(key=lambda r: r.priority, reverse=True)
        self._rules = compiled
        # print(f"Loaded {len(self._rules)} rules from {self.yaml_path}")
            

    
    
    def _translate_into_CBOM_format(self, df: pandas.DataFrame) -> None:
        """Translate parsed data into CBOM format."""
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        cbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": now,
                "tools": {
                    "components": [],
                    "services": []
                }
            },
            "components": []
        }
        
        dicts = df.to_dict(orient='records')
        # parse extra field into dict
        for record in dicts:
            extra_str = record.get('extra', '')
            extra_dict = {}
            for part in extra_str.split(','):
                if '=' in part:
                    key, value = part.split('=', 1)
                    extra_dict[key.strip()] = value.strip()
            record['extra'] = extra_dict
        # print("Processing records:")
        for record in dicts:
            # print(record)
            for rule in self._rules:
                # print(f"  Checking rule {rule}")
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
                                "parameterSetIdentifier": int(record["extra"]["pkey_size"]) * 8 if "pkey_size" in record["extra"] else None,
                            }
                        }
                    }
                    cbom["components"].append(component)
        return cbom
    
    def _save_cbom_to_file(self, cbom: Dict[str, Any], output_path: str) -> None:
        """Save the CBOM dictionary to a JSON file."""
        path = Path(output_path)

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                cbom,
                f,
                ensure_ascii=False,  # keep unicode readable
                indent=2,            # pretty-print
            )
    
    def process_log(self, log_file: str, output_path: str) -> None:
        """Process the log file and output CBOM data."""
        df = self._load_and_summarize_log(log_file)
        cbom = self._translate_into_CBOM_format(df)
        self._save_cbom_to_file(cbom, output_path=output_path)