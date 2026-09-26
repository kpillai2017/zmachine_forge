"""§12 The object table (version 4 and later layout).

    +-----------------------------+  object table address (header 0x0A)
    | 63 words: property defaults |  §12.2 (get_prop falls back to these)
    +-----------------------------+
    | object 1: 14 bytes          |  §12.3.2
    | object 2 ...                |
    +-----------------------------+

Each 14-byte object entry:
    6 bytes  attributes 0..47 (attribute 0 = top bit of the first byte)
    2 bytes  parent   } object numbers are WORDS in v4+
    2 bytes  sibling  }
    2 bytes  child    }
    2 bytes  address of the property table

Property table (§12.4): a text-length byte (in words), the short name as a
z-string, then properties in DESCENDING number order, ended by a 0 byte.
Each property starts with a size byte (§12.4.2):
    bit 7 = 1: two size bytes; number = bits 0-5; 2nd byte bits 0-5 = length
               (a length of 0 means 64, §12.4.2.1.1)
    bit 7 = 0: one size byte; number = bits 0-5; length = 2 if bit 6 else 1
"""
from __future__ import annotations

from zforge.common.errors import ZMachineError
from zforge.common.memory import Memory

DEFAULTS_COUNT = 63
ENTRY_SIZE = 14
ATTRIBUTE_COUNT = 48
PARENT, SIBLING, CHILD, PROPS = 6, 8, 10, 12   # byte offsets inside an entry


class ObjectTable:
    def __init__(self, memory: Memory, table_address: int, warn=None):
        self.mem = memory
        self.base = table_address
        self.first_entry = table_address + 2 * DEFAULTS_COUNT
        self.warn = warn or (lambda message: None)

    # -- locating ----------------------------------------------------------
    def entry(self, obj: int) -> int:
        if obj < 1:
            raise ZMachineError("Object 0 has no entry (§12.3)")
        return self.first_entry + (obj - 1) * ENTRY_SIZE

    # -- attributes (§12.3.1) ----------------------------------------------
    def _attr_location(self, obj: int, attr: int) -> tuple[int, int]:
        if not 0 <= attr < ATTRIBUTE_COUNT:
            raise ZMachineError(f"Attribute {attr} out of range 0..47")
        return self.entry(obj) + attr // 8, 0x80 >> (attr % 8)

    def test_attr(self, obj: int, attr: int) -> bool:
        address, mask = self._attr_location(obj, attr)
        return bool(self.mem.read_byte(address) & mask)

    def set_attr(self, obj: int, attr: int, on: bool) -> None:
        address, mask = self._attr_location(obj, attr)
        byte = self.mem.read_byte(address)
        self.mem.write_byte(address, byte | mask if on else byte & ~mask)

    # -- tree links ----------------------------------------------------------
    def parent(self, obj: int) -> int:
        return self.mem.read_word(self.entry(obj) + PARENT)

    def sibling(self, obj: int) -> int:
        return self.mem.read_word(self.entry(obj) + SIBLING)

    def child(self, obj: int) -> int:
        return self.mem.read_word(self.entry(obj) + CHILD)

    def _set(self, obj: int, field: int, value: int) -> None:
        self.mem.write_word(self.entry(obj) + field, value)

    def remove(self, obj: int) -> None:
        """§15 remove_obj: detach obj (and its children) from its parent."""
        parent = self.parent(obj)
        if parent == 0:
            return
        if self.child(parent) == obj:
            self._set(parent, CHILD, self.sibling(obj))
        else:
            prev = self.child(parent)
            while prev and self.sibling(prev) != obj:
                prev = self.sibling(prev)
            if prev == 0:
                raise ZMachineError(f"Object tree corrupt: {obj} not a child of {parent}")
            self._set(prev, SIBLING, self.sibling(obj))
        self._set(obj, PARENT, 0)
        self._set(obj, SIBLING, 0)

    def insert(self, obj: int, destination: int) -> None:
        """§15 insert_obj: obj becomes the FIRST child of destination."""
        self.remove(obj)
        self._set(obj, PARENT, destination)
        self._set(obj, SIBLING, self.child(destination))
        self._set(destination, CHILD, obj)

    # -- properties (§12.4) --------------------------------------------------
    def property_table(self, obj: int) -> int:
        return self.mem.read_word(self.entry(obj) + PROPS)

    def short_name_address(self, obj: int) -> int:
        return self.property_table(obj) + 1

    def _first_property(self, obj: int) -> int:
        table = self.property_table(obj)
        return table + 1 + 2 * self.mem.read_byte(table)

    def _read_size(self, address: int) -> tuple[int, int, int]:
        """Parse a property's size byte(s) at `address`.
        Returns (number, length, address of the data)."""
        first = self.mem.read_byte(address)
        number = first & 0x3F
        if first & 0x80:
            length = self.mem.read_byte(address + 1) & 0x3F
            return number, (64 if length == 0 else length), address + 2
        return number, (2 if first & 0x40 else 1), address + 1

    def properties(self, obj: int):
        """Yield (number, length, data address) for each property of obj."""
        address = self._first_property(obj)
        while self.mem.read_byte(address) != 0:
            number, length, data = self._read_size(address)
            yield number, length, data
            address = data + length

    def property_address(self, obj: int, prop: int) -> int:
        """§15 get_prop_addr: data address of property `prop`, or 0."""
        for number, _length, data in self.properties(obj):
            if number == prop:
                return data
            if number < prop:            # properties are in descending order
                break
        return 0

    def property_length(self, data_address: int) -> int:
        """§15 get_prop_len: length of the property whose DATA starts here.
        get_prop_len 0 must return 0 (§15 get_prop_len)."""
        if data_address == 0:
            return 0
        size = self.mem.read_byte(data_address - 1)
        if size & 0x80:                   # this is the 2nd of two size bytes
            length = size & 0x3F
            return 64 if length == 0 else length
        return 2 if size & 0x40 else 1

    def get_prop(self, obj: int, prop: int) -> int:
        """§15 get_prop: value of a 1- or 2-byte property, else the default."""
        for number, length, data in self.properties(obj):
            if number == prop:
                if length == 1:
                    return self.mem.read_byte(data)
                if length != 2:
                    self.warn(f"get_prop on property {prop} of length {length} (§15)")
                return self.mem.read_word(data)
            if number < prop:
                break
        return self.mem.read_word(self.base + 2 * (prop - 1))

    def put_prop(self, obj: int, prop: int, value: int) -> None:
        """§15 put_prop: the property MUST exist and be 1 or 2 bytes long."""
        for number, length, data in self.properties(obj):
            if number == prop:
                if length == 1:
                    self.mem.write_byte(data, value & 0xFF)
                else:
                    self.mem.write_word(data, value)
                return
        raise ZMachineError(f"put_prop: object {obj} has no property {prop}")

    def next_property(self, obj: int, prop: int) -> int:
        """§15 get_next_prop: 0 -> first property; else the one after `prop`."""
        numbers = [number for number, _l, _d in self.properties(obj)]
        if prop == 0:
            return numbers[0] if numbers else 0
        if prop not in numbers:
            raise ZMachineError(f"get_next_prop: object {obj} has no property {prop}")
        index = numbers.index(prop)
        return numbers[index + 1] if index + 1 < len(numbers) else 0
