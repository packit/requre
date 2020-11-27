from requre.objects import ObjectStorage
from requre.cassette import Cassette

cassette = Cassette()


@ObjectStorage.decorator_plain(cassette=cassette)
def return_result():
    return {"value": input("insert value: ")}


cassette.storage_file = "values.yaml"
value = return_result()

cassette.dump()
print(cassette.storage_object)
print(value)
