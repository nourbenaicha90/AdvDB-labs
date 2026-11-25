# Advanced Databases — Labs 01, 02, 03

A mini database engine built in three layers:

```
SQL query
   ↓
query_processor.py   (Lab 03: parse + execute SELECT / INSERT)
   ↓
record_layer.py      (Lab 02: dict <-> bytes using schema.json)
   ↓
heap_file.py         (Lab 01: slotted pages, 4096 bytes)
   ↓
Disk file (.bin)
```

## Files
| File | Lab | Role |
|---|---|---|
| `heap_file.py` | 01 | Page I/O, free space, insert/get records (slotted page) |
| `record_layer.py` | 02 | `encode_record`, `decode_record`, `insert_structured_record`, `read_all_structured_records` |
| `query_processor.py` | 03 | `parse_select_query`, `parse_insert_query`, `execute_query` |
| `schema.json` | 02 | Table descriptions (Employee, Dept) |
| `main.py` | all | Demo of the three labs |
| `test_all.py` | all | Automated tests |

## Page layout (Lab 01)
- Page size: 4096 bytes.
- Footer (last 4 bytes): slot count (2 bytes) + free-space offset (2 bytes).
- Slot table before the footer: 4 bytes per entry (record offset + record length).

## Field types (Lab 02)
`int` (4 bytes), `float` (4 bytes), `char(n)` (n bytes), `varchar(n)` (1 length byte + n bytes).

## Supported SQL (Lab 03)
```sql
SELECT * FROM Employee;
SELECT name, salary FROM Employee WHERE id = 3;
SELECT * FROM Employee WHERE salary >= 3000 AND salary < 4600;   -- optional: AND + comparison operators
INSERT INTO Employee (id, name, salary) VALUES (4, 'Alice', 4500);
```
Operators: `= != <> > < >= <=`.

## Run
```bash
python main.py       # demo
python test_all.py   # tests
```
Python 3.8+, no external dependencies.
