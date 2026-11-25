import os
from record_layer import (load_schema, insert_structured_record,
                          read_all_structured_records, encode_record, decode_record)
from query_processor import execute_query, parse_select_query, parse_insert_query


def main():
    schema = load_schema("schema.json")
    for table in schema:                       # start from clean files
        if os.path.exists(table["file_name"]):
            os.remove(table["file_name"])

    print("=== Lab 02 : encode / decode ===")
    rec = {"id": 1, "name": "Alice", "salary": 4500}
    b = encode_record(rec, "Employee", schema)
    print(len(b), "bytes ->", b)
    print(decode_record(b, "Employee", schema))

    print("\n=== Lab 02 : insert / read ===")
    insert_structured_record("Employee", schema, {"id": 1, "name": "Alice", "salary": 4500})
    insert_structured_record("Employee", schema, {"id": 2, "name": "Bob", "salary": 4000})
    insert_structured_record("Dept", schema, {"id": 1, "name": "IT", "Location": "New York"})
    insert_structured_record("Dept", schema, {"id": 2, "name": "HR", "Location": "London"})
    for t in ("Employee", "Dept"):
        print(f"-- {t}")
        for r in read_all_structured_records(t, schema):
            print(r)

    print("\n=== Lab 03 : parse ===")
    print(parse_select_query("SELECT name, salary FROM Employee WHERE id = 2;", schema))
    print(parse_insert_query("INSERT INTO Employee (id, name, salary) VALUES (4, 'Alice', 4500);", schema))

    print("\n=== Lab 03 : execute ===")
    queries = [
        "INSERT INTO Employee (id, name, salary) VALUES (3, 'Ali', 4800);",
        "INSERT INTO Employee (id, name, salary) VALUES (4, 'Sara', 3000);",
        "SELECT * FROM Employee;",
        "SELECT name, salary FROM Employee WHERE id = 3;",
        # optional part: comparison operators + AND
        "SELECT name FROM Employee WHERE salary > 3500;",
        "SELECT * FROM Employee WHERE salary >= 3000 AND salary < 4600;",
        "SELECT name FROM Employee WHERE id > 1 AND name != 'Bob' AND salary <= 4800;",
        "SELECT * FROM Dept WHERE Location = 'New York';",
    ]
    for q in queries:
        print("\n>", q)
        print(execute_query(q, schema))


if __name__ == "__main__":
    main()
