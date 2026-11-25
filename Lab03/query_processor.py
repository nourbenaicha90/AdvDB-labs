# query_processor.py  --  Lab 03 : Simple Query Processor over Heap File
#   SELECT field_list FROM table [WHERE cond [AND cond ...]]
#   INSERT INTO table (f1, f2, ...) VALUES (v1, v2, ...)
#   cond :  field  (=  !=  <>  >  <  >=  <=)  value          (optional part: AND + operators)
import re
import struct
import operator
from record_layer import get_table_schema, insert_structured_record, read_all_structured_records

OPS = {"=": operator.eq, "!=": operator.ne, "<>": operator.ne,
       ">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}

_VALUE = r"""'[^']*'|"[^"]*"|[^\s,;()]+"""
_COND = rf"""\w+\s*(?:>=|<=|<>|!=|=|>|<)\s*(?:{_VALUE})"""
_COND_PARTS = re.compile(rf"""(\w+)\s*(>=|<=|<>|!=|=|>|<)\s*({_VALUE})""")

_SELECT_RE = re.compile(
    rf"""^\s*select\s+(?P<fields>.+?)\s+from\s+(?P<table>\w+)
         (?:\s+where\s+(?P<where>{_COND}(?:\s+and\s+{_COND})*))?
         \s*;?\s*$""", re.I | re.X | re.S)

_INSERT_RE = re.compile(
    r"""^\s*insert\s+into\s+(?P<table>\w+)\s*\((?P<fields>[^)]*)\)\s*
        values\s*\((?P<values>.*)\)\s*;?\s*$""", re.I | re.X | re.S)


def _convert(token):
    """'text' -> str ; 12 -> int ; 1.5 -> float."""
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "'\"":
        return token[1:-1]
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        raise ValueError(f"Invalid value: {token!r} (text must be quoted)")


# =========================
# 1. Parse SELECT
#    condition = None                      -> no WHERE
#              = {"field","op","value"}    -> one condition
#              = [ {...}, {...} ]          -> conditions joined by AND
# =========================
def parse_select_query(query, schema):
    m = _SELECT_RE.match(query)
    if not m:
        raise ValueError("Invalid SELECT syntax")

    fields = ["*"] if m["fields"].strip() == "*" else [f.strip() for f in m["fields"].split(",")]
    if any(not f for f in fields):
        raise ValueError("Invalid field list")

    condition = None
    if m["where"]:
        conds = [{"field": f, "op": op, "value": _convert(v)}
                 for f, op, v in _COND_PARTS.findall(m["where"])]
        condition = conds[0] if len(conds) == 1 else conds

    return {"fields": fields, "table": m["table"], "condition": condition}


# =========================
# 2. Parse INSERT
# =========================
def parse_insert_query(query, schema):
    m = _INSERT_RE.match(query)
    if not m:
        raise ValueError("Invalid INSERT syntax")

    fields = [f.strip() for f in m["fields"].split(",")]
    values = [_convert(v) for v in re.findall(_VALUE, m["values"])]
    if len(fields) != len(values):
        raise ValueError(f"{len(fields)} columns but {len(values)} values")

    return {"table": m["table"], "fields": fields, "values": values}


# =========================
# 3. Execute
# =========================
def _column(table, name):
    """Exact column definition (case-insensitive lookup) or error."""
    for f in table["fields"]:
        if f["name"].lower() == name.lower():
            return f
    raise ValueError(f"Unknown column '{name}' in table {table['table_name']}")


def _to_float32(x):
    return float(f"{struct.unpack('>f', struct.pack('>f', x))[0]:.7g}")


def _make_filter(table, condition):
    """Build a predicate(record) -> bool from one condition or a list (AND)."""
    conds = [condition] if isinstance(condition, dict) else condition
    checks = []
    for c in conds:
        col = _column(table, c["field"])
        ctype, value = col["type"].lower(), c["value"]
        is_num = ctype in ("int", "float")
        if is_num and isinstance(value, str):
            raise ValueError(f"Column '{col['name']}' is numeric, got text {value!r}")
        if not is_num and not isinstance(value, str):
            raise ValueError(f"Column '{col['name']}' is text, got number {value!r}")
        if ctype == "float":
            value = _to_float32(value)
        checks.append((col["name"], OPS[c["op"]], value))
    return lambda r: all(op(r[name], v) for name, op, v in checks)


def execute_query(query, schema):
    stripped = query.strip()
    head = stripped.split(None, 1)[0].lower() if stripped else ""

    if head == "select":
        p = parse_select_query(query, schema)
        table = get_table_schema(schema, p["table"])
        records = read_all_structured_records(table["table_name"], schema)

        if p["condition"]:
            keep = _make_filter(table, p["condition"])
            records = [r for r in records if keep(r)]

        if p["fields"] == ["*"]:
            return records
        cols = [_column(table, f)["name"] for f in p["fields"]]
        return [{c: r[c] for c in cols} for r in records]

    if head == "insert":
        p = parse_insert_query(query, schema)
        table = get_table_schema(schema, p["table"])
        record = {_column(table, f)["name"]: v for f, v in zip(p["fields"], p["values"])}
        page, slot = insert_structured_record(table["table_name"], schema, record)
        return f"Inserted into {table['table_name']} (page={page}, slot={slot})"

    raise ValueError("Unsupported query (only SELECT and INSERT)")
