import pytest
from rdflib import Graph
from cheka import Cheka


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
                    prof:hasArtifact <http://mock.com/articfact/validator-x.ttl> ;
                ] ;
            .
            """.format(Cheka.VALIDATORS_DIR)


def _get_all_artifact_uris_sparql(graph):
    q = '''
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        PREFIX prof: <http://www.w3.org/ns/dx/prof/>
        
        SELECT ?rd ?a
        WHERE {
            ?rd prof:hasRole role:validation .
            ?rd prof:hasArtifact ?a .
        }
        ORDER BY ?rd
        '''
    artifact_uris = []
    rd_as = {}
    for r in graph.query(q):
        if r["rd"] in rd_as.keys():
            rd_as[r["rd"]].append(str(r["a"]))
        else:
            rd_as[r["rd"]] = [str(r["a"])]

    for a in rd_as.values():
        for a2 in sorted(a):  # this ensures file:// URIs come before http:// URIs
            if Cheka.VALIDATORS_DIR in a2:
                artifact_uris.append(a2)
                break
            elif a2.startswith("file://"):
                artifact_uris.append(a2)
                break
            else:
                artifact_uris.append(a2)
                break

    return artifact_uris


def _get_artifact_uris_for_profile(graph, profile_uri):
    q = '''
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        PREFIX prof: <http://www.w3.org/ns/dx/prof/>

        SELECT ?rd ?a
        WHERE {{
            <{}> prof:isProfileOf* ?p . 
            ?p prof:hasResource ?rd .
            ?rd prof:hasRole role:validation .
            ?rd prof:hasArtifact ?a .
        }}
        '''.format(profile_uri)
    artifact_uris = []
    rd_as = {}
    for r in graph.query(q):
        if r["rd"] in rd_as.keys():
            rd_as[r["rd"]].append(str(r["a"]))
        else:
            rd_as[r["rd"]] = [str(r["a"])]

    for a in rd_as.values():
        for a2 in sorted(a):  # this ensures file:// URIs come before http:// URIs
            if Cheka.VALIDATORS_DIR in a2:
                artifact_uris.append(a2)
                break
            elif a2.startswith("file://"):
                artifact_uris.append(a2)
                break
            else:
                artifact_uris.append(a2)
                break

    return artifact_uris


def test_all_artifact_uris(data_rdf, profiles_rdf):
    expected = _get_all_artifact_uris_sparql(Graph().parse(data=profiles_rdf, format="turtle"))
    c = Cheka(data_graph_ttl=data_rdf, profiles_graph_ttl=profiles_rdf)
    c._get_artifact_uris()

    assert set(c.artifact_uris) == set(expected), \
        "Expected:\n<{}>\nbut got:\n<{}>".format(">, <".join(expected), ">, <".join(c.artifact_uris))


def test_profile_artifact_uris(data_rdf, profiles_rdf):
    expected = _get_artifact_uris_for_profile(
        Graph().parse(data=profiles_rdf, format="turtle"),
        profile_uri="http://example.org/profile/Profile_C"
    )
    c = Cheka(data_graph_ttl=data_rdf, profiles_graph_ttl=profiles_rdf)
    c._get_artifact_uris(profile_uri="http://example.org/profile/Profile_C")
    assert set(c.artifact_uris) == set(expected), \
        "Expected:\n<{}>\nbut got:\n<{}>".format(">, <".join(expected), ">, <".join(c.artifact_uris))
