import pytest
import sys
sys.path.append('..')
from cheka import Cheka

"""
These most basic tests ensure that a single thing in a data graph can be validated according to a profile hierarchy for 
a given Profile (by URI). 
"""
global c


def setup():
    global c
    c = Cheka('test_01_d.ttl', 'test_01_p.ttl')


def test_validate_simple():
    # should be true since the dataset has a title (<A>) and a creator (<B>)
    t1 = c.validate(profile_uri='http://example.org/profile/Profile_B')
    assert t1[0], t1[2]

    # should be false since the dataset does not have a created date (<C>)
    t2 = c.validate(profile_uri='http://example.org/profile/Profile_C')
    assert not t2[0], t2[2]

    # should be false since the dataset claims conformance with <C> but has no created date
    t3 = c.validate()
    assert not t3[0], t3[2]
