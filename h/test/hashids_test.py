from h import hashids

hashids.SALT = 'test salt'


# These tests are deliberately brittle, and dependent on the 'test salt' above,
# because we need these to not randomly change. If this test starts failing
# because the ids are encoding to something different, that is genuinely a
# problem.
def test_hashids_encode():
    assert hashids.encode('foo', 1) == '1V91V4'
    assert hashids.encode('bar', 1) == 'E8Rz8D'
    assert hashids.encode('foo', 123) == 'Lgq4nK'
    assert hashids.encode('foo', 1, 2, 3) == 'zvuvt2'

def test_hashids_decode():
    assert hashids.decode('foo', '1V91V4') == (1,)
    assert hashids.decode('bar', 'E8Rz8D') == (1,)
    assert hashids.decode('foo', 'Lgq4nK') == (123,)
    assert hashids.decode('foo', 'zvuvt2') == (1, 2, 3)

def test_hashids_decode_one():
    assert hashids.decode_one('foo', '1V91V4') == 1
    assert hashids.decode_one('bar', 'E8Rz8D') == 1
    assert hashids.decode_one('foo', 'Lgq4nK') == 123
    assert hashids.decode_one('foo', 'zvuvt2') is None
