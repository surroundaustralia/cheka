from cheka.cheka import Cheka
import logging
logging.basicConfig(level=logging.INFO)


def test_04():
    logging.info("test_04")
    c = Cheka("data/01.ttl", "profiles/03.ttl")
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Standard_A")
    assert not v[0]
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Profile_B")
    assert not v[0]

    c = Cheka("data/06.ttl", "profiles/03.ttl")
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Standard_A")
    assert v[0]
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Profile_B")
    assert v[0]
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Profile_C")
    assert not v[0]  # since no created date
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Standard_X")
    assert v[0]  # since no validators

    v = Cheka("data/05.ttl", "profiles/03.ttl").validate()
    assert v[0]


if __name__ == "__main__":
    test_04()
