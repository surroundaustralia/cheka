import pytest
from rdflib import Graph
from cheka import Cheka
from os.path import join, abspath, dirname

DATA_RDF = """
            @prefix dct: <http://purl.org/dc/terms/> .
            @prefix sdo: <https://schema.org/> .
            @prefix void: <http://rdfs.org/ns/void#> .
            @base <http://example.org/dataset/> .
    
            <One>
                a void:Dataset ;
                dct:title "Dataset One" ;
                dct:conformsTo <http://example.org/profile/Profile_C> ;
                dct:creator [
                    a sdo:Person ;
                    sdo:name "Nicholas J. Car" ;          
                ] .
            """

PROFILES_RDF = """
                @prefix dct: <http://purl.org/dc/terms/> .
                @prefix prof: <http://www.w3.org/ns/dx/prof/> .
                @prefix role:  <http://www.w3.org/ns/dx/prof/role/> .
                @prefix local_file: <file://> .
                @base <http://example.org/profile/> .
                
                
                <Standard_A>
                    a dct:Standard ;
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
    c = Cheka(data_graph_ttl=DATA_RDF, profiles_graph_ttl=PROFILES_RDF)


def test_bad_strings():
    with pytest.raises(ValueError):
        c = Cheka(data_graph_ttl="blah", profiles_graph_ttl=PROFILES_RDF)


def test_good_graphs():
    dg = Graph().parse(data=DATA_RDF, format="turtle")
    pg = Graph().parse(data=PROFILES_RDF, format="turtle")
    c = Cheka(data_graph_obj=dg, profiles_graph_obj=pg)


def test_bad_graphs():
    dg = "not a graph"
    pg = Graph().parse(data=PROFILES_RDF, format="turtle")
    with pytest.raises(AssertionError):
        c = Cheka(data_graph_obj=dg, profiles_graph_obj=pg)

    # fail on an empty graph
    with pytest.raises(AssertionError):
        dg = Graph()
        c = Cheka(data_graph_obj=dg, profiles_graph_obj=pg)


def test_good_paths():
    c = Cheka(data_graph_file_path=join(dirname(__file__), "test_01_d.ttl"), profiles_graph_file_path=join(dirname(__file__), "test_01_p.ttl"))


def test_bad_paths():
    with pytest.raises(FileNotFoundError):
        c = Cheka(data_graph_file_path="BORKED", profiles_graph_file_path=join(dirname(__file__), "test_01_p.ttl"))


def test_strategies():
    # invalid strategy
    with pytest.raises(ValueError):
        c = Cheka(
            data_graph_file_path=join(dirname(__file__), "test_01_d.ttl"),
            profiles_graph_file_path=join(dirname(__file__), "test_01_p.ttl"),
        ).validate(strategy="other")

    # profile strategy, no profile_uri given
