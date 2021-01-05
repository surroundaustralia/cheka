from cheka.cheka import Cheka
import logging
logging.basicConfig(level=logging.INFO)


def test_05():
    # logging.info("test_05")
    # c = Cheka("data/06.ttl", "profiles/04.ttl", get_remote_profiles=False)
    # v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Profile_A")
    # assert v[0]

    c = Cheka("data/06.ttl", "profiles/04.ttl", get_remote_profiles=True)
    v = c.validate(strategy="profile", profile_uri="http://example.org/profile/Profile_A")
    assert v[0]


if __name__ == "__main__":
    test_05()
