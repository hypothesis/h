from mock import Mock


class DictMock(Mock):
    """A mock class providing basic dict semantics

    Usage example:
        Annotation = DictMock()
        a = Annotation({'text': 'bla'})
        a['user'] = 'alice'

        assert a['text'] == 'bla'
        assert a['user'] == 'alice'
    """
    def __init__(self, *args, **kwargs):
        super(DictMock, self).__init__(*args, **kwargs)
        self.instances = []
        def side_effect(*args_, **kwargs_):
            d = dict(*args_, **kwargs_)
            def getitem(name):
                return d[name]
            def setitem(name, value):
                d[name] = value
            def contains(name):
                return name in d
            m = Mock()
            m.__getitem__ = Mock(side_effect=getitem)
            m.__setitem__ = Mock(side_effect=setitem)
            m.__contains__ = Mock(side_effect=contains)
            m.get = Mock(side_effect=d.get)
            m.pop = Mock(side_effect=d.pop)
            m.update = Mock(side_effect=d.update)
            self.instances.append(m)
            return m
        self.side_effect = side_effect
