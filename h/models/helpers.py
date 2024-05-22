def repr_(obj, attrs):
    class_name = type(obj).__name__
    attrs = {attrname: getattr(obj, attrname) for attrname in attrs}
    return f"{class_name}({', '.join(f'{name}={value!r}' for name, value in attrs.items())})"
