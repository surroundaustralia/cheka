import pytest
import sys
sys.path.append('..')
from cheka import Cheka

"""
These tests check that multiple objects in the data graph can be validated only according to the Profiles they claim 
conformance to. In test_02_d.ttl, they are:

<http://example.org/dataset/One> dct:conformsTo <http://example.org/profile/Profile_C> ;

<http://example.org/dataset/Two> dct:conformsTo <http://example.org/profile/Profile_B> ;

This test is designed to ensure that not every single thing in the data graph is validated according to very Profile.
"""
global c


def setup():
    global c
    c = Cheka('test_02_d.ttl', 'test_01_p.ttl')


def test_validate():
    global c
    # should be valid since both <One> & <Two> have title (A) & creator (B)
    t1 = c.validate(profile_uri='http://example.org/profile/Profile_B')
    assert t1[0], t1[2]

    # should be false since <Two> has no created
    t2 = c.validate(profile_uri='http://example.org/profile/Profile_C')
    assert not t2[0], t2[2]

    # should be true since <One> claims <A> & <Two> claims <B>
    t3 = c.validate()
    assert t3[0], t3[2]

    # should be true since <One> has title (A) & creator (B)
    t4 = c.validate(instance_uri='http://example.org/dataset/One', profile_uri='http://example.org/profile/Profile_B')
    assert t4[0], t4[2]

    # should be true since <Two> has title (A) & creator (B)
    t5 = c.validate(instance_uri='http://example.org/dataset/Two', profile_uri='http://example.org/profile/Profile_B')
    assert t5[0], t5[2]

    # should be true since <One> has title (A) & creator (B) & created (C)
    t6 = c.validate(instance_uri='http://example.org/dataset/One', profile_uri='http://example.org/profile/Profile_C')
    assert t6[0], t6[2]

    # should be false since <Two> has title (A) & creator (B) but not created (C)
    t7 = c.validate(instance_uri='http://example.org/dataset/Two', profile_uri='http://example.org/profile/Profile_C')
    assert not t7[0], t7[2]

    # should be true since <One> & <Two> are void:Dataset instances and both meet <B> reqs
    t8 = c.validate(by_class=True, profile_uri='http://example.org/profile/Profile_B')
    assert t8[0], t8[2]

    # should be false since <One> & <Two> are void:Dataset instances and <Two> doesn't meet <C> created req
    t9 = c.validate(
        by_class=True,
        profile_uri='http://example.org/profile/Profile_C'
    )
    assert not t9[0], t9[2]


def test_errors():
    # edge case: both by_class and instance_uri set illegally
    with pytest.raises(Exception) as e_info:
        t10 = c.validate(
            by_class=True,
            instance_uri='http://example.org/dataset/Two',
            profile_uri='http://example.org/profile/Profile_C'
        )
