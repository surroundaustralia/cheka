import pytest
from rdflib import Graph
from cheka import Cheka
from os.path import join, abspath, dirname

DATA_RDF = """
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
                    sdo:name "Nicholas J. Car" ;          
                ] .
            """

PROFILES_RDF = """
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX prof: <http://www.w3.org/ns/dx/prof/>
                PREFIX role:  <http://www.w3.org/ns/dx/prof/role/>
                PREFIX local_file: <file://>
                BASE <http://example.org/profile/>
                
                
                <Standard_A>
                    a dcterms:Standard ;
                    prof:hasResource [
                        a prof:ResourceDescriptor ;
                        prof:hasRole role:validation ;
                        prof:hasArtifact <file://test_01_shacl_j.ttl> ;
                    ]
                .
                
                <Profile_B>
                    a prof:Profile ;
                    prof:isProfileOf <Standard_A> ;
                    prof:hasResource <Resource_Descriptor_P> ;
                .
                
                <Resource_Descriptor_P>
                    a prof:ResourceDescriptor ;
                    prof:hasRole role:validation ;
                    prof:hasArtifact <file://test_01_shacl_k.ttl> ;
                .
                
                <Profile_C>
                    a prof:Profile ;
                    prof:isProfileOf <Profile_B> ;
                    prof:hasResource [
                        a prof:ResourceDescriptor ;
                        prof:hasRole role:validation ;
                        prof:hasArtifact <file://test_01_shacl_l.ttl> ;
                    ] ;
                .
                """


def test_good_strings():
    c = Cheka(DATA_RDF, PROFILES_RDF)


def test_bad_strings():
    with pytest.raises(ValueError):
        c = Cheka("blah", PROFILES_RDF)


def test_good_graphs():
    dg = Graph().parse(data=DATA_RDF, format="turtle")
    pg = Graph().parse(data=PROFILES_RDF, format="turtle")
    c = Cheka(dg, pg)


def test_bad_graphs():
    dg = "not a graph"
    pg = Graph().parse(data=PROFILES_RDF, format="turtle")
    with pytest.raises(ValueError):
        c = Cheka(dg, pg)

    # fail on an empty graph
    with pytest.raises(AssertionError):
        dg = Graph()
        c = Cheka(dg, pg)


def test_good_paths():
    c = Cheka(join(dirname(__file__), "test_01_d.ttl"), join(dirname(__file__), "test_01_p.ttl"))


def test_bad_paths():
    with pytest.raises(ValueError):
        c = Cheka("BORKED", join(dirname(__file__), "test_01_p.ttl"))


def test_strategies():
    # invalid strategy
    with pytest.raises(ValueError):
        c = Cheka(
            join(dirname(__file__), "test_01_d.ttl"), join(dirname(__file__), "test_01_p.ttl")
        ).validate(strategy="other")

    # profile strategy, no profile_uri given
