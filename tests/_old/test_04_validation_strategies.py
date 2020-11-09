import pytest
from cheka import Cheka


@pytest.fixture
def data_rdf():
    return """
            PREFIX dcterms:http://purl.org/dc/terms/> 
            PREFIX sdo:https://schema.org/> 
            PREFIX void:http://rdfs.org/ns/void#> 
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


@pytest.fixture
def data_rdf2():
    return """
            PREFIX dcterms:http://purl.org/dc/terms/> 
            PREFIX sdo:https://schema.org/> 
            PREFIX void:http://rdfs.org/ns/void#> 
            PREFIX xsd:http://www.w3.org/2001/XMLSchema#> 
            BASE <http://example.org/dataset/>

            <One>
                a void:Dataset ;
                dcterms:title "Dataset One" ;
                dcterms:conformsTo <http://example.org/profile/Profile_C> ;
                dcterms:creator [
                    a sdo:Person ;
                    sdo:name "Nicholas J. Car" ;          
                ] ;
                dcterms:created "2020-07-01"^^xsd:date ;
            .
            """


@pytest.fixture
def profiles_rdf():
    return """
            PREFIX dcterms:http://purl.org/dc/terms/> 
            PREFIX prof:http://www.w3.org/ns/dx/prof/> 
            PREFIX role: http://www.w3.org/ns/dx/prof/role/> 
            BASE <http://example.org/profile/>


            <Standard_A>
                a dcterms:Standard ;
                prof:hasResource [
                    a prof:ResourceDescriptor ;
                    prof:hasRole role:validation ;
                    prof:hasArtifact <file://test_01_shacl_j.ttl> ;
                ] ,
                [
                    a prof:ResourceDescriptor ;
                    prof:hasRole role:guidance ;
                    prof:hasArtifact <file://some_fake_file.pdf> ;
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
                prof:hasArtifact <http://fake.com/test_01_shacl_k.ttl> ;
                prof:hasArtifact <file://test_01_shacl_k.ttl> ;
            .                

            <Profile_C>
                a prof:Profile ;
                prof:isProfileOf <Profile_B> ;
                prof:hasResource [
                    a prof:ResourceDescriptor ;
                    prof:hasRole role:validation ;
                    prof:hasArtifact <file://{}/test_01_shacl_l.ttl> ;
                ] ;
            .

            <Profile_D>
                a prof:Profile ;
                prof:isProfileOf <Profile_B> ;
                prof:hasResource [
                    a prof:ResourceDescriptor ;
                    prof:hasRole role:validation ;
                    prof:hasArtifact <http://mock.com/artifact/validator-x.ttl> ;
                ] ;
            .
            """.format(Cheka.VALIDATORS_DIR)


def test_shacl_fail(data_rdf, profiles_rdf):
    c = Cheka(data_graph_ttl=data_rdf, profiles_graph_ttl=profiles_rdf)
    x = c.validate()
    assert "A void:Dataset must have a dcterms:created property indicating an xsd:date or xsd:dateTime" in x[2]
    assert x[3] is None


def test_shacl_pass(data_rdf2, profiles_rdf):
    c = Cheka(data_graph_ttl=data_rdf2, profiles_graph_ttl=profiles_rdf)
    x = c.validate()
    assert x[0]  # i.e. valid

