import pkg_resources

def _is_package_available(package_name:str):
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

_librarian_available = _is_package_available('kksubs-librarian')

def is_librarian_available():
    return _librarian_available
