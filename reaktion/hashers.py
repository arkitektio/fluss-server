import hashlib
import json


def hash_graph(graph_hash) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(graph_hash, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


def hash_python_flow(source: str, entrypoint: str, manifest: list, runtime: str) -> str:
    """sha256 over what makes a PythonFlow version behave differently (not its title or ports)."""
    encoded = json.dumps({"source": source, "entrypoint": entrypoint, "manifest": manifest, "runtime": runtime}, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()
