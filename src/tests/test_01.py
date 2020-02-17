from src.cheka import Cheka

"""
These most basic tests ensure that a single thing in a data graph can be validated according to a profile hierarchy for 
a given Profile (by URI). 
"""
c = Cheka('test_01_d.ttl', 'test_01_p.ttl')

assert c.validate(profile_uri='http://example.org/profile/Profile_B')[0]

assert not c.validate(profile_uri='http://example.org/profile/Profile_C')[0]
