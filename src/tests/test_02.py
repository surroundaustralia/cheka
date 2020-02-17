from src.cheka import Cheka

c = Cheka('test_02_d.ttl', 'test_01_p.ttl')

a = c.validate()
assert a[0], a[2]
