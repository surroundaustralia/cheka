from src.cheka import Cheka

"""
These tests check that the objects in the data graph can be validated only according to the Profiles they claim 
conformance to. In test_02_d.ttl, they are:

<http://example.org/dataset/One> dct:conformsTo <http://example.org/profile/Profile_C> ;

<http://example.org/dataset/Two> dct:conformsTo <http://example.org/profile/Profile_B> ;

This test is designed to ensure that not every single thing in the data graph is validated according to very Profile.
"""
c = Cheka('test_02_d.ttl', 'test_01_p.ttl')

a = c.validate()
assert a[0], a[2]
