from src.cheka import Cheka

c = Cheka('test_01_d.ttl', 'test_01_p.ttl')

assert c.validate(profile_uri='http://example.org/profile/Profile_B')[0]

assert not c.validate(profile_uri='http://example.org/profile/Profile_C')[0]
