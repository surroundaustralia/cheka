import pytest
from cheka import Cheka
from os.path import join, isfile


@pytest.fixture
def data_rdf():
    return """
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


@pytest.fixture
def profiles_rdf():
    return """
            PREFIX dct: <http://purl.org/dc/terms/> 
            PREFIX prof: <http://www.w3.org/ns/dx/prof/> 
            PREFIX role:  <http://www.w3.org/ns/dx/prof/role/> 
            @base <http://example.org/profile/> .


            <Standard_A>
                a dct:Standard ;
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


def test_artifact_dereferencing(data_rdf, profiles_rdf):
    c = Cheka(data_graph_ttl=data_rdf, profiles_graph_ttl=profiles_rdf)
    c._get_artifact_uris()
    c._dereference_artifact_uris()

    for uri in c.artifact_uris:
        file_name = uri.replace("file://", "").replace(Cheka.VALIDATORS_DIR, "").split("/")[-1]
        file_path = join(Cheka.VALIDATORS_DIR, file_name)
        assert isfile(file_path)


def test_combine_validators(data_rdf, profiles_rdf):
    c = Cheka(data_graph_ttl=data_rdf, profiles_graph_ttl=profiles_rdf)
    c._get_artifact_uris()
    c._dereference_artifact_uris()
    c._make_shapes_graph()

    assert(len(c.sg) == 60)
