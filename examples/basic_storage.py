import tempfile
from requre.storage import PersistentObjectStorage

keys = ["basic", "keys", 0.1]
value1 = {"cat": "tom", "mouse": "jerry"}
value2 = {"cat1": "pa", "cat2": "pi"}

PersistentObjectStorage().storage_file = tempfile.mktemp()

PersistentObjectStorage().store(keys, value1, metadata={})
PersistentObjectStorage().store(keys, value2, metadata={})
PersistentObjectStorage().dump()

PersistentObjectStorage().storage_object = {}
PersistentObjectStorage().load()
print(PersistentObjectStorage().storage_object)
print(PersistentObjectStorage().read(keys))
print(PersistentObjectStorage().read(keys))
