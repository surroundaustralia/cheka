import sys
from cheka import Cheka
from rdflib import Graph
sys.path.append('..')


DATA = """
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX sdo: <https://schema.org/>
        PREFIX void: <http://rdfs.org/ns/void#>
        BASE <http://example.org/dataset/>
        
        <One>
            a void:Dataset ;
            dcterms:title "Dataset One" ;
            dcterms:conformsTo <http://example.org/profile/Profile_C> ;
            dcterms:creator [
                a sdo:Person ;
                sdo:name "Nicholas J. Car" .             
            ] .
        """


def setup():
    global c
    g = Graph()
    c = Cheka(data_graph_ttl="x", profiles_graph_obj=g)


def test_01():
    t1 = c.validate(shacl_only=True)
    assert t1[0], t1[2]


if __name__ == "__main__":
    setup()
    test_01()
