import pytest
from rdflib import Graph
from cheka import Cheka

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


def setup():
    global c
    c = Cheka(data_graph_ttl=DATA_RDF, profiles_graph_ttl=PROFILES_RDF)


def _get_all_artifact_uris_sparql(graph):
    q = '''
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        PREFIX prof: <http://www.w3.org/ns/dx/prof/>
        
        SELECT ?a_url
        WHERE {
            { ?p a prof:Profile . } 
            UNION 
            { ?p a dcterms:Standard . } 
            ?p prof:hasResource ?rd .
            ?rd prof:hasRole role:validation .
            # ?rd dcterms:conformsTo <https://www.w3.org/TR/shacl/> .
            # ?rd dcterms:format "text/turtle" ;
            ?rd prof:hasArtifact ?a_url .
        }
        '''
    artifact_uris = []
    for r in graph.query(q):
        artifact_uris.append(str(r["a_url"]))

    return artifact_uris


def _get_artifact_uris_for_profile(graph, profile_uri):
    q = '''
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        PREFIX prof: <http://www.w3.org/ns/dx/prof/>

        SELECT ?a_url
        WHERE {{
            <{}> prof:isProfileOf* ?p . 
            ?p prof:hasResource ?rd .
            ?rd prof:hasRole role:validation .
            # # ?rd dcterms:conformsTo <https://www.w3.org/TR/shacl/> .
            # # ?rd dcterms:format "text/turtle" ;
            ?rd prof:hasArtifact ?a_url .
        }}
        '''.format(profile_uri)
    artifact_uris = []
    for r in graph.query(q):
        artifact_uris.append(str(r["a_url"]))

    return artifact_uris


def test_all_artifact_uris():
    expected = _get_all_artifact_uris_sparql(Graph().parse(data=PROFILES_RDF, format="turtle"))
    got = Cheka.get_artifact_uris(Graph().parse(data=PROFILES_RDF, format="turtle"))
    assert set(got) == set(expected), "Expected <{}> but got <{}>".format(">, <".join(expected), ">, <".join(got))


def test_profile_artifact_uris():
    expected = _get_artifact_uris_for_profile(
        Graph().parse(data=PROFILES_RDF, format="turtle"),
        profile_uri="http://example.org/profile/Profile_C"
    )
    got = Cheka.get_artifact_uris(
        Graph().parse(data=PROFILES_RDF, format="turtle"),
        profile_uri="http://example.org/profile/Profile_C"
    )
    assert set(got) == set(expected), "Expected <{}> but got <{}>".format(">, <".join(expected), ">, <".join(got))


if __name__ == "__main__":
    # setup()
    test_profile_artifact_uris()

