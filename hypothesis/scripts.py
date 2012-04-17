def prepare(zest=None):
    """A zest releaser entry point which compiles and minifies all resources"""
    from fanstatic import set_resource_file_existence_checking
    from fanstatic.scripts import prepare
    set_resource_file_existence_checking(False)
    prepare(zest=zest)
