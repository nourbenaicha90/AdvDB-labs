import os, heap_file as h
from record_layer import *
from query_processor import *

# ---------- Lab 01 (heap file) ----------
fn = "t.bin"; h.create_heap_file(fn)
assert h.insert_record_to_file(fn, b"AAAAA") == (0, 0)
assert h.insert_record_to_file(fn, b"BBBBBB") == (0, 1)
p = h.read_page(fn, 0)
assert p[4092:4096] == b"\x00\x02\x00\x0b" and p[4088:4092] == b"\x00\x00\x00\x05"
for _ in range(1500): h.insert_record_to_file(fn, b"x" * 20)
assert len(h.get_all_record_from_file(fn)) == 1502 and os.path.getsize(fn) > 4096
os.remove(fn)

# ---------- Lab 02 ----------
schema = load_schema()
for t in schema:
    if os.path.exists(t["file_name"]): os.remove(t["file_name"])
e = {"id": 12, "name": "Alice", "salary": 4500.5}
b = encode_record(e, "Employee", schema)
assert len(b) == 4 + 20 + 4 and decode_record(b, "Employee", schema) == e
d = {"id": 1, "name": "IT", "Location": "Paris, France"}
b = encode_record(d, "Dept", schema)
assert len(b) == 4 + 20 + 1 + 40 and b[24] == 13          # varchar = 1 length byte + 40 content bytes
assert decode_record(b, "Dept", schema) == d
sc = [{"table_name":"T","file_name":"tt.bin","fields":[{"name":"a","type":"varchar(30)"},{"name":"b","type":"int"}]}]
insert_structured_record("T", sc, {"a":"hi","b":7}); insert_structured_record("T", sc, {"a":"مرحبا","b":9})
assert read_all_structured_records("T", sc) == [{"a":"hi","b":7},{"a":"مرحبا","b":9}]
os.remove("tt.bin")

# ---------- Lab 03 ----------
assert parse_select_query("SELECT name, salary FROM Employee WHERE id = 3;", schema) == \
    {"fields": ["name","salary"], "table": "Employee", "condition": {"field":"id","op":"=","value":3}}
assert parse_insert_query("INSERT INTO Employee (id, name, salary) VALUES (4, 'Alice', 4500);", schema) == \
    {"table":"Employee","fields":["id","name","salary"],"values":[4,"Alice",4500]}
assert parse_select_query("SELECT * FROM Employee;", schema)["condition"] is None

for q in ["INSERT INTO Employee (id, name, salary) VALUES (1, 'Alice', 4500);",
          "insert into Employee (id,name,salary) values (2,'Bob Marley',0.1)",
          "INSERT INTO Employee (id, name, salary) VALUES (3, 'Ali', 4800);",
          "INSERT INTO Dept (id, name, Location) VALUES (1, 'IT', 'Paris, France');",
          "INSERT INTO Dept (id, name, Location) VALUES (2, 'HR', 'New York');"]:
    execute_query(q, schema)

assert len(execute_query("SELECT * FROM Employee;", schema)) == 3
assert execute_query("SELECT name, salary FROM Employee WHERE id = 3;", schema) == [{"name":"Ali","salary":4800.0}]
assert execute_query("select name from employee where salary = 0.1", schema) == [{"name":"Bob Marley"}]
assert [r["id"] for r in execute_query("SELECT * FROM Employee WHERE salary > 1000", schema)] == [1, 3]
assert [r["id"] for r in execute_query("SELECT * FROM Employee WHERE id >= 1 AND salary < 4600", schema)] == [1, 2]
assert [r["id"] for r in execute_query("SELECT * FROM Employee WHERE id > 1 AND name != 'Bob Marley' AND salary <= 4800", schema)] == [3]
assert execute_query("SELECT Location FROM Dept WHERE Location = 'New York'", schema) == [{"Location":"New York"}]
assert execute_query("SELECT * FROM Dept", schema)[0]["Location"] == "Paris, France"
for bad in ["SELECT foo FROM Employee", "SELECT * FROM Nope", "INSERT INTO Employee (id) VALUES (1)",
            "SELECT * FROM Employee WHERE name > 5", "SELECT * FROM Employee WHERE id = 'x'",
            "INSERT INTO Employee (id, name) VALUES (1, 'A', 3)", "DELETE FROM Employee"]:
    try: execute_query(bad, schema); assert False, bad
    except (ValueError, TypeError): pass
print("ALL TESTS PASSED")
