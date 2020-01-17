from requre.objects import ObjectStorage
from requre.storage import PersistentObjectStorage


@ObjectStorage.decorator_plain
def return_result():
    return {"value": input("insert value: ")}


PersistentObjectStorage().storage_file = "values.yaml"
value = return_result()

ObjectStorage.persistent_storage.dump()
print(PersistentObjectStorage().storage_object)
print(value)
