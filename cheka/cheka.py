from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import DCTERMS, PROF, RDF, SH
from os.path import dirname, realpath, join
from rdflib.paths import ZeroOrMore
from rdflib.util import guess_format
import requests
from pyshacl import validate
import shutil


class Cheka:
    ROLE = Namespace("http://www.w3.org/ns/dx/prof/role/")
    VALIDATORS_DIR = join(dirname(__file__), "validators")

    """The Cheka program main class that contains all of the functionality

    """
    def __init__(
        self,
        data_graph_obj=None,
        data_graph_ttl=None,
        data_graph_file_path=None,
        profiles_graph_obj=None,
        profiles_graph_ttl=None,
        profiles_graph_file_path=None,
    ):
        self.dg = Graph()
        self.pg = Graph()
        self.sg = Graph()

        # validate inputs
        assert any(elem is None for elem in [data_graph_obj, data_graph_ttl, data_graph_file_path]), \
            "You must supply either a data graph object, string of RDF or a file path"

        assert any(elem is None for elem in [profiles_graph_obj, profiles_graph_ttl, profiles_graph_file_path]), \
            "You must supply either a profiles graph object, string of RDF or a file path"

        if data_graph_obj is not None:
            assert type(data_graph_obj) == Graph, \
                "The value data_graph_obj, if supplied, must be an in-memory RDFlib Graph object"

        if data_graph_ttl is not None:
            assert type(data_graph_ttl) == str, \
                "The value data_graph_rdf, if supplied, must be a string, of RDF"

        if data_graph_file_path is not None:
            assert type(data_graph_file_path) == str, \
                "The value data_graph_file_path, if supplied, must be a string, of RDF, in the Turtle format"

        if profiles_graph_obj is not None:
            assert type(profiles_graph_obj) == Graph, \
                "The value profiles_graph_obj, if supplied, must be an in-memory RDFlib Graph object"

        if profiles_graph_ttl is not None:
            assert type(profiles_graph_ttl) == str, \
                "The value profiles_graph_ttl, if supplied, must be a string, of RDF, in the Turtle format"

        if profiles_graph_file_path is not None:
            assert type(profiles_graph_file_path) == str, \
                "The value profiles_graph_file_path, if supplied, must be a string, of RDF"

        # parse inputs
        if data_graph_obj is not None:
            self.dg = data_graph_obj
        elif data_graph_ttl is not None:
            try:
                self.dg.parse(data=data_graph_ttl, format="turtle")
            except Exception as e:
                raise ValueError("You've supplied an invalid data_graph_ttl value. The parsing said: {}".format(e))
        elif data_graph_file_path is not None:
            self.dg.parse(
                data_graph_file_path,
                format=guess_format(data_graph_file_path)
            )

        if profiles_graph_obj is not None:
            self.pg = profiles_graph_obj
        elif profiles_graph_ttl is not None:
            self.pg.parse(data=profiles_graph_ttl, format="turtle")
        elif profiles_graph_file_path is not None:
            self.pg.parse(
                profiles_graph_file_path,
                format=guess_format(profiles_graph_file_path)
            )
            self.profiles_graph_file_path = profiles_graph_file_path

        assert len(self.dg) > 0, "The Data Graph has not been able to be read"

        assert len(self.pg) > 0, "The Profiles Graph has not been able to be read"

        # make nice namespaces
        self.pg.bind('prof', PROF)
        self.pg.bind('sh', SH)
        self.pg.bind('role', Cheka.ROLE)

        # expand the profiles graph
        self._expand_profiles_graph()

    def _expand_profiles_graph(self):
        # type all profiles
        # dcterms:Standard instances are prof:Profiles instances
        for s, p, o in self.pg.triples((None, RDF.type, DCTERMS.Standard)):
            self.pg.add((s, RDF.type, PROF.Profile))
        # anything using prof:isProfileOf is a prof:Profile
        for s, p, o in self.pg.triples((None, PROF.isProfileOf, None)):
            self.pg.add((o, RDF.type, PROF.Profile))

        # type all RDs
        # anything indicated by prof:hasResource is a prof:ResourceDescriptor
        for s, p, o in self.pg.triples((None, PROF.hasResource, None)):
            self.pg.add((o, RDF.type, PROF.ResourceDescriptor))

    def _get_artifact_uris(self, profile_uri=None):
        """Gets all the artifact URIs for all Resource Descriptors' artifacts from a profile hierarchy, where the
        Resource Descriptor's role is "validator".

        If a profile_uri is given, only that profile's Resource Descriptor's artifact URIs and those of Profiles or
        Standard it profiles are returned, else all Profiles or Standard's Resource Descriptor's artifact URIs in the
        given graph are returned.

        For each Resource Descriptor, if there is more than one artifact URI, retrieve only the local file URI.

        :param profile_uri: The URI of a prof:Profile or dcterms:Standard in the given graph
        :type profile_uri: str
        :return:
        :rtype:
        """
        def get_artifact_uris_per_profile(profile_uriref):
            uu = []

            for o2 in self.pg.objects(subject=profile_uriref, predicate=PROF.hasResource):
                for o3 in self.pg.objects(subject=o2, predicate=PROF.hasRole):
                    if o3 == Cheka.ROLE.validation:
                        rds_artifact_uris = []
                        for o4 in self.pg.objects(subject=o2, predicate=PROF.hasArtifact):
                            rds_artifact_uris.append(str(o4))
                        # for this RD,
                        # prefer a file already in the VALIDATORS_DIR
                        # over one still local, but prefer local bot in VALIDATORS_DIR
                        # to remote
                        u = next((x for x in rds_artifact_uris if Cheka.VALIDATORS_DIR in x), None)
                        if u is None:
                            u = next((x for x in rds_artifact_uris if x.startswith("file://") or x.startswith("/")), None)
                            if u is None:
                                u = rds_artifact_uris[0]
                        uu.append(u)
            return uu

        artifact_uris = []

        if profile_uri is None:
            # get all profiles' validators

            # for every subject,
            # if it's a Profile or a Standard,
            # get all of it's ResourceDescriptors
            # if the Role is validator,
            # get the artifact link
            for s, o in self.pg.subject_objects(predicate=RDF.type):
                if o == PROF.Profile:
                    artifact_uris.extend(get_artifact_uris_per_profile(s))
        else:
            # for the given profile_uri
            # get URIs of all the things it profiles
            # find their RDs' artifacts, as above
            for s, p, o in self.pg.triples((URIRef(profile_uri), PROF.isProfileOf*ZeroOrMore, None)):
                artifact_uris.extend(get_artifact_uris_per_profile(o))

        self.artifact_uris = artifact_uris

    def _dereference_artifact_uris(self):
        # for every URI,
        # if it's a local file, check to see if it's already in the validators/ folder
        # if so, do nothing
        # if not, copy it in
        # update URI for
        for uri in self.artifact_uris:
            if Cheka.VALIDATORS_DIR in uri:
                pass  # nothing to do since it's already in the cache
            elif uri.startswith("file://") or uri.startswith("/"):  # it is a local file
                shutil.copyfile(
                    uri.replace("file://", ""),
                    join(Cheka.VALIDATORS_DIR, uri.split("/")[-1])
                )
                # TODO: cater for potentially pre-existing duplicated file names in validators/ from other RDs
                # attempt write back new copy of file to self.pg
                # find the relevant RD
                for s in self.pg.subjects(predicate=PROF.hasArtifact, object=URIRef(uri)):
                    self.pg.add((
                        s,
                        PROF.hasArtifact,
                        URIRef(join("file://", Cheka.VALIDATORS_DIR, uri.split("/")[-1]))
                    ))
            else:
                # mock URL for testing
                if uri == "http://mock.com/artifact/validator-x.ttl":
                    shacl_file_content = """
                                            @prefix dct: <http://purl.org/dc/terms/> .
                                            @prefix owl: <http://www.w3.org/2002/07/owl#> .
                                            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
                                            @prefix sdo: <https://schema.org/> .
                                            @prefix sh: <http://www.w3.org/ns/shacl#> .
                                            @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
                                            @prefix void: <http://rdfs.org/ns/void#> .
                                            @base <https://data.surroundaustralia.com/shapes/dataset/> .
                                            
                                            
                                            # this shape adds a requirement for a dct:creator
                                            <CreatorShape>
                                                a sh:NodeShape ;
                                                sh:targetClass void:Dataset ;
                                                sh:property [
                                                    sh:path dct:creator ;
                                                    sh:minCount 1 ;
                                                    sh:or (
                                                        [
                                                            sh:class sdo:Organization ;
                                                        ]
                                                        [
                                                            sh:class sdo:Person ;
                                                        ]
                                                    ) ;
                                                    sh:message "A void:Dataset must have a dct:creator property indicating an sdo:Organization or an sdo:Person" ;
                                                ] ;
                                            .
                                            """
                else:  # resolve the URI for real
                    r = requests.get(uri)
                    shacl_file_content = r.text
                with open(join(Cheka.VALIDATORS_DIR, uri.split("/")[-1]), "w") as f:
                    f.write(shacl_file_content)
                # attempt write back new copy of file to self.pg
                # find the relevant RD
                for s in self.pg.subjects(predicate=PROF.hasArtifact, object=URIRef(uri)):
                    self.pg.add((
                        s,
                        PROF.hasArtifact,
                        URIRef(join("file://", Cheka.VALIDATORS_DIR, uri.split("/")[-1]))
                    ))

        # rerunning this should purge all non-VALIDATION_DIR URIs since all file should have been copied there
        self._get_artifact_uris()

    def _make_shapes_graph(self):
        for f in self.artifact_uris:
            self.sg.parse(f, format=guess_format(f))

    def _get_shapes_from_profiles_graph(self, profile_uri=None):
        """Parses the profiles hierarchy graph and, if no profile_uri is given, collects and merges all the SHACL
        validator resources related to all profiles. If a profile_uri is given, collects and merges all the SHACL
        validator resources related to the identified profile and the things it profiles.

        :param profile_uri: the URI of a profile within the hierarchy
        :return:
        """

        q = '''
            SELECT ?shacl_file
            WHERE {{
                <{}> prof:isProfileOf* ?p .
                ?p prof:hasResource ?r .
                ?r prof:hasRole role:validation .
                ?r prof:hasArtifact ?shacl_file .
            }}
            '''
        # TODO: indicated graphs already stored in memory to avoid repeated parsing
        # TODO: pickle parsed RDF files for future stateless use
        for r in self.pg.query(q.format(profile_uri)):
            if str(r['shacl_file']).startswith('file://'):
                # this is a local file
                PROFILES_GRAPH_FILE_DIR = dirname(realpath(self.profiles_graph_file_path))
                f = join(PROFILES_GRAPH_FILE_DIR, str(r['shacl_file']).replace('file://', ''))
                self.sg.parse(
                    f,
                    format=rdflib.util.guess_format(f)
                )
            else:
                # TODO: test shapes graph from URI
                # get the shapes graph from URI
                r = requests.get(str(r['shacl_file']))
                if r.ok:
                    self.sg.parse(
                        r.text,
                        format=r.headers['Content-Type']
                    )

    def validate(self, strategy="shacl", profile_uri=None, instance_uri=None):
        """Validates a data graph using a shapes graph generated from a profile hierarchy

        :param shacl_only: if this is True, Cheka will perform normal SHACL validation only
        :param by_class: if this is True, instance_uri will be ignored and profile_uri MUST be set
        :param instance_uri_claim: if this is set, by_class must not be set to True
        :param profile_uri: if this is set, validation against this profile and its hierarchy will be tested only,
        regardless of conformance claims in the data graph
        :return:
        """

        strategies = [
            "shacl",
            "profile",
            "instance",
            "claims"
        ]
        if strategy not in strategies:
            raise ValueError("The strategy selected must either be None or one of '{}'".format("', '".join(strategies)))

        if strategy == "shacl":
            # get all the SHACL validators for all profiles in the hierarchy

            self._get_artifact_uris()
            self._dereference_artifact_uris()
            self._make_shapes_graph()

            valid, v_graph, v_msg = validate(
                self.dg,
                meta_shacl=True,  # validate the SHACL graph first
                shacl_graph=self.sg,
                # inference='rdfs', # not sure if this should be used
                abort_on_error=False
            )
            # conforms, results_graph, results_text = r
            return valid, v_graph, v_msg, profile_uri

        # testing inputs
        if by_class and instance_uri_claim is not None:
            raise IOError('You must not set both by_class to True and give instance_uri a value simultaneously')
        # for testing - print('validate(): {}, {}, {}'.format(by_class, instance_uri, profile_uri))
        # if by_class is True, validate things by class (i.e. not by instance_uri)
        if by_class:
            # ignore instance_uri
            # if profile_uri is set, only load that profile's validation resource hierarchy
            if profile_uri is not None:
                self._get_shapes_from_profiles_graph(profile_uri)

                # validate data graph using shapes graph
                # use pySHACL to validate data graph against all shapes graphs
                valid, v_graph, v_msg = validate(
                    self.dg,
                    meta_shacl=True,  # validate the SHACL graph first
                    shacl_graph=self.sg,
                    # inference='rdfs', # not sure if this should be used
                    abort_on_error=False
                )
                # conforms, results_graph, results_text = r
                return (valid, v_graph, v_msg, profile_uri)
            # profile_uri is not set so no validation can be performed
            else:
                return (True, None, None, None)
        # else by_class is False, validate things by instance_uri (i.e. not by class)
        else:
            # get the list of instances to validate
            instances_for_validation = []
            # if an instance_uri is set, only list that thing for validation
            if instance_uri_claim is not None:
                # if a profile_uri is given, indicate the instance is to be validated using that only
                if profile_uri is not None:
                    instances_for_validation.append((instance_uri_claim, profile_uri))
                # if a profile_uri is not given, look for conformance claims for validation target. Can by multiple
                else:
                    for o in self.dg.objects(subject=rdflib.URIRef(instance_uri_claim), predicate=DCTERMS.conformsTo):
                        instances_for_validation.append((str(instance_uri_claim), str(o)))
            # if an instance_uri is not set, extract all things from data graph with conformance claims for validation
            else:
                # if a profile_uri is given, indicate instances are to be validated using that only
                if profile_uri is not None:
                    for s, o in self.dg.subject_objects(predicate=DCTERMS.conformsTo):
                        instances_for_validation.append((str(s), profile_uri))
                # if a profile_uri is not given, look for conformance claims for validation targets. Can by multiple
                else:
                    for s, o in self.dg.subject_objects(predicate=DCTERMS.conformsTo):
                        instances_for_validation.append((str(s), str(o)))

            # validate each instance
            valid = True
            v_graph = rdflib.Graph()
            v_msg = []
            for inst in instances_for_validation:
                # build the shapes graph for this instance
                self._get_shapes_from_profiles_graph(inst[1])

                # add to the self.sg, an instance-specific sh:targetNode statement for the given instance_uri
                # remove from self.sg, the generic targetClass statements
                for s in self.sg.subjects(
                        predicate=RDF.type,
                        object=self.SH.NodeShape):
                    self.sg.add((
                        s,
                        self.SH.targetNode,
                        rdflib.URIRef(inst[0])
                    ))
                    self.sg.remove((
                        s,
                        self.SH.targetClass,
                        None
                    ))

                # validate the instance against the profile_uri's hierarchy
                local_valid, local_v_graph, local_v_msg = validate(
                    self.dg,
                    shacl_graph=self.sg,
                    # inference='rdfs', # not sure if this should be used
                    abort_on_error=False
                )

                if not local_valid:  # i.e. invalid
                    valid = False
                    v_graph += local_v_graph
                    v_msg.append(local_v_msg)
                self.sg = None
                self.sg = rdflib.Graph()

            # emulate pySHACL's return style + profile URI
            return (valid, v_graph, v_msg, profile_uri)
