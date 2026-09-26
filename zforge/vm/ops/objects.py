"""§15 object opcodes, delegating to vm.objects (the §12 ObjectTable).

Object 0 means "nothing". Using it is technically an error, but real games
do it; like Frotz we WARN and carry on with a harmless result (ADR-003)."""
from __future__ import annotations


def _nothing(vm, name: str) -> bool:
    vm.warn(f"{name} called with object 0")
    return True


def op_jin(vm, obj1, obj2):
    """§15 jin (2OP:6): branch if obj1's parent is obj2."""
    if obj1 == 0 and _nothing(vm, "jin"):
        vm.branch(obj2 == 0)
        return
    vm.branch(vm.objects.parent(obj1) == obj2)


def op_test_attr(vm, obj, attr):
    """§15 test_attr (2OP:10): branch if obj has attribute attr."""
    if obj == 0 and _nothing(vm, "test_attr"):
        vm.branch(False)
        return
    vm.branch(vm.objects.test_attr(obj, attr))


def op_set_attr(vm, obj, attr):
    """§15 set_attr (2OP:11)."""
    if obj == 0 and _nothing(vm, "set_attr"):
        return
    vm.objects.set_attr(obj, attr, True)


def op_clear_attr(vm, obj, attr):
    """§15 clear_attr (2OP:12)."""
    if obj == 0 and _nothing(vm, "clear_attr"):
        return
    vm.objects.set_attr(obj, attr, False)


def op_insert_obj(vm, obj, destination):
    """§15 insert_obj (2OP:14): obj becomes the first child of destination."""
    if (obj == 0 or destination == 0) and _nothing(vm, "insert_obj"):
        return
    vm.objects.insert(obj, destination)


def op_remove_obj(vm, obj):
    """§15 remove_obj (1OP:137): detach obj from its parent."""
    if obj == 0 and _nothing(vm, "remove_obj"):
        return
    vm.objects.remove(obj)


def op_get_parent(vm, obj):
    """§15 get_parent (1OP:131): store the parent (no branch)."""
    vm.store_result(0 if obj == 0 and _nothing(vm, "get_parent") else vm.objects.parent(obj))


def op_get_child(vm, obj):
    """§15 get_child (1OP:130): store first child; branch if it exists."""
    child = 0 if obj == 0 and _nothing(vm, "get_child") else vm.objects.child(obj)
    vm.store_result(child)
    vm.branch(child != 0)


def op_get_sibling(vm, obj):
    """§15 get_sibling (1OP:129): store next sibling; branch if it exists."""
    sibling = 0 if obj == 0 and _nothing(vm, "get_sibling") else vm.objects.sibling(obj)
    vm.store_result(sibling)
    vm.branch(sibling != 0)


def op_get_prop(vm, obj, prop):
    """§15 get_prop (2OP:17): property value, or the default (§12.2)."""
    vm.store_result(0 if obj == 0 and _nothing(vm, "get_prop") else vm.objects.get_prop(obj, prop))


def op_get_prop_addr(vm, obj, prop):
    """§15 get_prop_addr (2OP:18): address of the property data, or 0."""
    vm.store_result(0 if obj == 0 and _nothing(vm, "get_prop_addr")
                    else vm.objects.property_address(obj, prop))


def op_get_next_prop(vm, obj, prop):
    """§15 get_next_prop (2OP:19): next property number (0 -> first)."""
    vm.store_result(0 if obj == 0 and _nothing(vm, "get_next_prop")
                    else vm.objects.next_property(obj, prop))


def op_get_prop_len(vm, data_address):
    """§15 get_prop_len (1OP:132): length of property data at address."""
    vm.store_result(vm.objects.property_length(data_address))


def op_put_prop(vm, obj, prop, value):
    """§15 put_prop (VAR:227)."""
    if obj == 0 and _nothing(vm, "put_prop"):
        return
    vm.objects.put_prop(obj, prop, value)
