from cheka.cheka import Cheka
import logging
logging.basicConfig(level=logging.INFO)


def test_01():
    logging.info("test_01")
    v = Cheka("data/01.ttl", "profiles/01.ttl").validate()
    assert not v[0]  # False
    assert "<https://data.surroundaustralia.com/shapes/dataset/TitleShape>" in v[2]
    assert "<http://example.org/dataset/One>" in v[2]
    assert "A void:Dataset must have either a skos:prefLabel" in v[2]
    v = Cheka("data/06.ttl", "profiles/02.ttl").validate()
    assert not v[0]  # False
    assert "A void:Dataset must have either a skos:prefLabel" not in v[2]
    assert "A void:Dataset must have a dcterms:created property" in v[2]


if __name__ == "__main__":
    test_01()
