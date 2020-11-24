import tempfile
from requre.cassette import Cassette

keys = ["basic", "keys", 0.1]
value1 = {"cat": "tom", "mouse": "jerry"}
value2 = {"cat1": "pa", "cat2": "pi"}

cassette = Cassette()
cassette.storage_file = tempfile.mktemp()

cassette.store(keys, value1, metadata={})
cassette.store(keys, value2, metadata={})
cassette.dump()

cassette.storage_object = {}
cassette.load()
print(cassette.storage_object)
print(cassette.read(keys))
print(cassette.read(keys))
