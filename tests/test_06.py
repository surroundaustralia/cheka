from cheka.cheka import Cheka
import logging
logging.basicConfig(level=logging.INFO)


# strategy = claims
def test_06():
    c = Cheka("data/06.ttl", "profiles/04.ttl")
    v = c.validate(strategy="claims", profile_uri="http://example.org/profile/Profile_A")
    assert v[0]


if __name__ == "__main__":
    test_06()
