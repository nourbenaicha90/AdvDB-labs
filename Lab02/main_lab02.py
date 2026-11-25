import os
from record_layer import (load_schema, encode_record, decode_record,
                          insert_structured_record, read_all_structured_records)

schema = load_schema("schema.json")
for t in schema:
    if os.path.exists(t["file_name"]):
        os.remove(t["file_name"])

# 1 + 2 : encode / decode
rec = {"id": 1, "name": "Alice", "salary": 4500}
data = encode_record(rec, "Employee", schema)
print(len(data), "bytes:", data)
print(decode_record(data, "Employee", schema))

# 3 + 4 : insert / read all
insert_structured_record("Employee", schema, {"id": 1, "name": "Alice", "salary": 4500})
insert_structured_record("Employee", schema, {"id": 2, "name": "Bob", "salary": 4000})
insert_structured_record("Dept", schema, {"id": 1, "name": "IT", "Location": "New York"})
insert_structured_record("Dept", schema, {"id": 2, "name": "HR", "Location": "London"})
for t in ("Employee", "Dept"):
    print("--", t)
    for r in read_all_structured_records(t, schema):
        print(r)
