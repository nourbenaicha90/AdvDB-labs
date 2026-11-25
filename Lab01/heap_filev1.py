
import os
import struct

PAGE_SIZE = 4096


# 1. Create Heap File
def create_heap_file(filename):
    with open(filename, 'wb') as f:
        pass


# 2. Read Page
def read_page(filename, page_number):
    with open(filename, 'rb') as f:
        f.seek(page_number * PAGE_SIZE)
        return f.read(PAGE_SIZE)


# 3. Append Page
def append_page(filename, page_data):
    with open(filename, 'ab') as f:
        f.write(page_data)


# 4. Write Page
def write_page(filename, page_number, page_data):
    with open(filename, 'r+b') as f:
        f.seek(page_number * PAGE_SIZE)
        f.write(page_data)


# 5. Calculate Free Space
def Calculate_free_space(page):
    slot_count = int.from_bytes(page[4092:4094], 'big')
    free_offset = int.from_bytes(page[4094:4096], 'big')

    return 4092 - slot_count * 4 - free_offset


# 6. Insert Record into Page
def insert_record_data_to_page_data(page, record):

    free_offset = int.from_bytes(page[4094:4096], 'big')
    slot_count = int.from_bytes(page[4092:4094], 'big')

    if Calculate_free_space(page) < len(record) + 4:
        raise ValueError("Not enough space")

    page = bytearray(page)

    # Write record
    page[free_offset:free_offset + len(record)] = record

    # Write slot
    position = 4092 - (slot_count + 1) * 4

    struct.pack_into('>H', page, position, free_offset)
    struct.pack_into('>H', page, position + 2, len(record))

    # Update footer
    struct.pack_into('>H', page, 4092, slot_count + 1)
    struct.pack_into('>H', page, 4094, free_offset + len(record))

    return bytes(page)


# 7. Insert Record into File
def insert_record_to_file(filename, record):
    print('nbr=>',os.path.getsize(filename))

    pages = os.path.getsize(filename) // PAGE_SIZE

    for i in range(pages):
        page = read_page(filename, i)

        if Calculate_free_space(page) >= len(record) + 4:
            slot_id = int.from_bytes(page[4092:4094], 'big')

            page = insert_record_data_to_page_data(page, record)
            write_page(filename, i, page)

            return (i, slot_id)

    # Create a new page
    page = bytes(PAGE_SIZE)
    page = insert_record_data_to_page_data(page, record)

    page_number = pages
    append_page(filename, page)

    return (page_number, 0)


# 8. Get Record from Page
def get_record_from_page(page, record_id):

    count = int.from_bytes(page[4092:4094], 'big')

    if record_id < 0 or record_id >= count:
        raise IndexError("Record does not exist")

    position = 4092 - (record_id + 1) * 4

    offset = int.from_bytes(page[position:position+2], 'big')
    length = int.from_bytes(page[position+2:position+4], 'big')

    return page[offset:offset+length]


# 9. Get Record from File
def get_record_from_file(filename, page_number, record_id):
    page = read_page(filename, page_number)
    return get_record_from_page(page, record_id)


# 10. Get All Records from Page
def get_all_record_from_page(page):

    count = int.from_bytes(page[4092:4094], 'big')

    records = []

    for i in range(count):
        records.append(get_record_from_page(page, i))

    return records


# 11. Get All Records from File
def get_all_record_from_file(filename):

    records = []
    pages = os.path.getsize(filename) // PAGE_SIZE

    for i in range(pages):
        page = read_page(filename, i)
        records.extend(get_all_record_from_page(page))

    return records


# 12. TEST
if __name__ == "__main__":

    filename = "heap_file.bin"

    if os.path.exists(filename):
        os.remove(filename)

    create_heap_file(filename)

    insert_record_to_file(filename, b"AAAAA")
    insert_record_to_file(filename, b"BBBBBB")

    print("All records:")

    for record in get_all_record_from_file(filename):
        print(record)

    page = read_page(filename, 0)

    print("Free space:", Calculate_free_space(page))
    print("Record 1:", get_record_from_file(filename, 0, 1))
