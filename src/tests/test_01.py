from src.cheka import Cheka

c = Cheka('01_d.ttl', '01_p.ttl')

# assert c.validate('http://example.org/profile/Profile_B')[0]
print(c.validate(profile_uri='http://example.org/profile/Profile_B')[2])

assert not c.validate('http://example.org/profile/Profile_C')[0]
