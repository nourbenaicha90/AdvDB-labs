import os, struct

PAGE_SIZE = 4096  # Each page is 4 KB


# =====================================================================
# Part 1 : Given functions (as in Lab 01)
# =====================================================================
def create_heap_file(file_name):
    with open(file_name, 'wb') as f:  # Open in write-binary mode
        pass


def read_page(file_name, page_number):
    """Read a specific page (4 KB) from the heap file given the page number."""
    # Check if the file has enough pages to contain the requested page
    file_size = os.path.getsize(file_name)
    last_page_number = file_size // PAGE_SIZE - 1

    if page_number > last_page_number:
        raise ValueError(f"Page {page_number} does not exist in the file.")

    with open(file_name, 'rb') as f:
        f.seek(page_number * PAGE_SIZE)  # Go to the start of the specified page
        page_data = f.read(PAGE_SIZE)    # Read the 4 KB page
    return page_data


def append_page(file_name, page_data):
    """Appends the provided page data to the end of the file."""
    if len(page_data) != PAGE_SIZE:
        raise ValueError(f"Page data must be exactly {PAGE_SIZE} bytes.")

    with open(file_name, 'ab') as f:  # Open in append-binary mode
        f.write(page_data)            # Append the page data to the end of the file


def write_page(file_name, page_number, page_data):
    """Write data to a specific page in the heap file."""
    # Check if the file has enough pages to contain the requested page
    file_size = os.path.getsize(file_name)
    last_page_number = file_size // PAGE_SIZE - 1

    if page_number > last_page_number:
        raise ValueError(f"Page {page_number} does not exist in the file.")
    if len(page_data) != PAGE_SIZE:   # (the lab text wrote `data`, an undefined name)
        raise ValueError(f"Data must be exactly {PAGE_SIZE} bytes long.")

    with open(file_name, 'r+b') as f:  # Open for reading and writing in binary mode
        f.seek(page_number * PAGE_SIZE)  # Go to the start of the specified page
        f.write(page_data)               # Write the data to the page


# =====================================================================
# Page layout (from the lab description)
#   footer (last 4 bytes): [4092-4093] slot count | [4094-4095] free space offset
#   slot table just before the footer, 4 bytes per entry:
#       2 bytes record offset + 2 bytes record length
#   slot i is at  4092 - (i+1)*4
# =====================================================================

# ---------------------------------------------------------------------
# 1. Calculate the free space in a page
# ---------------------------------------------------------------------
def Calculate_free_space(page_data):
    free_space_offset = int.from_bytes(page_data[4094:4096], 'big')
    slot_count = int.from_bytes(page_data[4092:4094], 'big')
    # free space = from the free space offset up to the start of the slot table
    slot_table_start = 4092 - slot_count * 4
    return slot_table_start - free_space_offset


# ---------------------------------------------------------------------
# 2. Insert a record into a page
# ---------------------------------------------------------------------
def insert_record_data_to_page_data(page_data, record_data):
    # check the free space vs record length (record bytes + one 4-byte slot entry)
    if Calculate_free_space(page_data) < len(record_data) + 4:
        raise ValueError("Not enough space in the page to insert the record.")

    # get the free space offset and slot count
    free_space_offset = int.from_bytes(page_data[4094:4096], 'big')
    slot_count = int.from_bytes(page_data[4092:4094], 'big')
    record_length = len(record_data)

    page_buffer = bytearray(page_data)

    # insert record_data starting from free space offset
    page_buffer[free_space_offset:free_space_offset + record_length] = record_data

    # insert the new slot entry (offset and length) of the new record
    slot_position = 4092 - (slot_count + 1) * 4
    struct.pack_into('>H', page_buffer, slot_position, free_space_offset)
    struct.pack_into('>H', page_buffer, slot_position + 2, record_length)

    # update slot count and free space offset
    struct.pack_into('>H', page_buffer, 4092, slot_count + 1)
    struct.pack_into('>H', page_buffer, 4094, free_space_offset + record_length)

    # return the page_data with the inserted record in bytes format
    return bytes(page_buffer)


def insert_record_to_file(file_name, record_data):
    # a record (+ its slot entry + footer) must fit in one page
    if len(record_data) + 4 > PAGE_SIZE - 4:
        raise ValueError("Record is too large to fit in a page.")

    # Get the page that has enough free space
    if os.path.exists(file_name):
        total_pages = os.path.getsize(file_name) // PAGE_SIZE
        for page_number in range(total_pages):
            page_data = read_page(file_name, page_number)
            if Calculate_free_space(page_data) >= len(record_data) + 4:
                slot_id = int.from_bytes(page_data[4092:4094], 'big')
                page_data = insert_record_data_to_page_data(page_data, record_data)
                write_page(file_name, page_number, page_data)
                return (page_number, slot_id)

    # If there is no free space or the file is empty, create a new data page
    page_data = b'\x00' * PAGE_SIZE
    page_data = insert_record_data_to_page_data(page_data, record_data)
    page_number = os.path.getsize(file_name) // PAGE_SIZE if os.path.exists(file_name) else 0
    append_page(file_name, page_data)
    return (page_number, 0)


# ---------------------------------------------------------------------
# 3. Get a record from a page
# ---------------------------------------------------------------------
def get_record_from_page(page_data, record_id):
    slot_count = int.from_bytes(page_data[4092:4094], 'big')
    if record_id < 0 or record_id >= slot_count:
        raise IndexError(f"Record {record_id} does not exist in this page.")

    slot_position = 4092 - (record_id + 1) * 4
    offset = int.from_bytes(page_data[slot_position:slot_position + 2], 'big')
    length = int.from_bytes(page_data[slot_position + 2:slot_position + 4], 'big')
    return page_data[offset:offset + length]


def get_record_from_file(file_name, page_number, record_id):
    page_data = read_page(file_name, page_number)
    return get_record_from_page(page_data, record_id)


# ---------------------------------------------------------------------
# 4. Get all records from a file
#    (signature as written in the lab; record_id is not needed, default None)
# ---------------------------------------------------------------------
def get_all_record_from_page(page_data, record_id=None):
    slot_count = int.from_bytes(page_data[4092:4094], 'big')
    return [get_record_from_page(page_data, i) for i in range(slot_count)]


def get_all_record_from_file(file_name):
    records = []
    if not os.path.exists(file_name):
        return records
    total_pages = os.path.getsize(file_name) // PAGE_SIZE
    for page_number in range(total_pages):
        page_data = read_page(file_name, page_number)
        records.extend(get_all_record_from_page(page_data))
    return records


# =====================================================================
# Test (reproduces the lab figure: free offset 0x0B, 2 slots, slot0=(0,5))
# =====================================================================
if __name__ == "__main__":
    filename = "heap_file.bin"
    if os.path.exists(filename):
        os.remove(filename)
    create_heap_file(filename)

    for rec in [b"AAAAA", b"BBBBBB"]:
        insert_record_to_file(filename, rec)

    for i, rec in enumerate(get_all_record_from_file(filename)):
        print(f"Record {i}: {rec}")

    last_page = read_page(filename, os.path.getsize(filename) // PAGE_SIZE - 1)
    print("Free space offset:", hex(int.from_bytes(last_page[4094:4096], 'big')))
    print("Slot count:", int.from_bytes(last_page[4092:4094], 'big'))
    print("Free space:", Calculate_free_space(last_page))
    print("Record (page 0, id 1):", get_record_from_file(filename, 0, 1))
