import importlib.metadata

KKSUBS_VERSION = importlib.metadata.version('kksubs')

def get_kksubs_version():
    return KKSUBS_VERSION