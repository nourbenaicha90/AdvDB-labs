# record_layer.py  --  Lab 02 : Binary Record Management with Table Schema
import json
import struct
import heap_file


# =========================
# Schema handling
# =========================
def load_schema(schema_file="schema.json"):
    with open(schema_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_table_schema(schema, table_name):
    for table in schema:
        if table["table_name"].lower() == table_name.lower():
            return table
    raise ValueError(f"Table '{table_name}' not found in schema")


def _size(ftype):
    """n of char(n) / varchar(n)."""
    return int(ftype.split("(")[1].split(")")[0])


def _cut(text, n):
    """Cut text to at most n BYTES (utf-8) without splitting a character."""
    return text.encode("utf-8")[:n].decode("utf-8", errors="ignore").encode("utf-8")


# =========================
# 1. Encode: dict -> bytes
#   int        : 4 bytes (big-endian)
#   float      : 4 bytes (big-endian)
#   char(n)    : n bytes, padded with \x00
#   varchar(n) : 1 byte length + n bytes content (padded with \x00)
# =========================
def encode_record(record_dict, table_name, schema):
    table = get_table_schema(schema, table_name)

    unknown = set(record_dict) - {f["name"] for f in table["fields"]}
    if unknown:
        raise ValueError(f"Unknown column(s) {sorted(unknown)} in table {table['table_name']}")

    record_bytes = b''
    for field in table["fields"]:
        name, ftype = field["name"], field["type"].lower()
        if name not in record_dict:
            raise ValueError(f"Missing value for column '{name}'")
        value = record_dict[name]

        if ftype == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"Column '{name}' expects int, got {value!r}")
            record_bytes += struct.pack(">i", value)

        elif ftype == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Column '{name}' expects float, got {value!r}")
            record_bytes += struct.pack(">f", value)

        elif ftype.startswith("char"):
            if not isinstance(value, str):
                raise TypeError(f"Column '{name}' expects text, got {value!r}")
            n = _size(ftype)
            b = _cut(value, n)
            record_bytes += b + b'\x00' * (n - len(b))

        elif ftype.startswith("varchar"):
            if not isinstance(value, str):
                raise TypeError(f"Column '{name}' expects text, got {value!r}")
            n = _size(ftype)
            b = _cut(value, n)
            record_bytes += struct.pack("B", len(b)) + b + b'\x00' * (n - len(b))

        else:
            raise ValueError(f"Unknown field type: {ftype}")
    return record_bytes


# =========================
# 2. Decode: bytes -> dict
# =========================
def decode_record(record_bytes, table_name, schema):
    table = get_table_schema(schema, table_name)
    record_dict, offset = {}, 0

    for field in table["fields"]:
        name, ftype = field["name"], field["type"].lower()

        if ftype == "int":
            record_dict[name] = struct.unpack_from(">i", record_bytes, offset)[0]
            offset += 4

        elif ftype == "float":
            x = struct.unpack_from(">f", record_bytes, offset)[0]
            record_dict[name] = float(f"{x:.7g}")   # 32-bit float -> clean value (0.1, not 0.10000000149)
            offset += 4

        elif ftype.startswith("char"):
            n = _size(ftype)
            record_dict[name] = record_bytes[offset:offset + n].decode("utf-8").rstrip("\x00")
            offset += n

        elif ftype.startswith("varchar"):
            n = _size(ftype)
            length = record_bytes[offset]
            record_dict[name] = record_bytes[offset + 1:offset + 1 + length].decode("utf-8")
            offset += 1 + n

        else:
            raise ValueError(f"Unknown field type: {ftype}")
    return record_dict


# =========================
# 3. Insert a structured record into the heap file
# =========================
def insert_structured_record(table_name, schema, record_dict):
    record_bytes = encode_record(record_dict, table_name, schema)
    file_name = get_table_schema(schema, table_name)["file_name"]
    return heap_file.insert_record_to_file(file_name, record_bytes)   # (page, slot)


# =========================
# 4. Read all structured records from the heap file
# =========================
def read_all_structured_records(table_name, schema):
    file_name = get_table_schema(schema, table_name)["file_name"]
    return [decode_record(rb, table_name, schema)
            for rb in heap_file.get_all_record_from_file(file_name)]
