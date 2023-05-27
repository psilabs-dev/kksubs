import pkg_resources

KKSUBS_VERSION = pkg_resources.require('kksubs')[0].version

def get_kksubs_version():
    return KKSUBS_VERSION