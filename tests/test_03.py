from cheka.cheka import Cheka
import logging
logging.basicConfig(level=logging.INFO)


def test_03():
    logging.info("test_03")
    v = Cheka("data/01.ttl", "profiles/03.ttl").validate()
    assert not v[0]

    v = Cheka("data/05.ttl", "profiles/03.ttl").validate()
    assert v[0]


if __name__ == "__main__":
    test_03()
