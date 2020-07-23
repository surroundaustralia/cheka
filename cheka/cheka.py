import rdflib
from rdflib.namespace import DCTERMS, RDF
from os.path import dirname, realpath, join
import requests
from pyshacl import validate


class Cheka:
    """The Cheka program main class that contains all of the functionality

    """
    def __init__(
            self,
            data_graph_obj=None,
            data_graph_ttl=None,
            data_graph_file_path=None,
            profiles_graph_obj=None,
            profiles_graph_ttl=None,
            profiles_graph_file_path=None):

        self.dg = rdflib.Graph()
        self.pg = rdflib.Graph()
        self.sg = rdflib.Graph()

        # validate inputs
        assert any(elem is None for elem in [data_graph_obj, data_graph_ttl, data_graph_file_path]), \
            "You must supply either a data graph object, string of RDF or a file path"

        assert any(elem is None for elem in [profiles_graph_obj, profiles_graph_ttl, profiles_graph_file_path]), \
            "You must supply either a profiles graph object, string of RDF or a file path"

        if data_graph_obj is not None:
            assert type(data_graph_obj) == rdflib.Graph, \
                "The value data_graph_obj, if supplied, must be an in-memory RDFlib Graph object"

        if data_graph_ttl is not None:
            assert type(data_graph_ttl) == str, \
                "The value data_graph_rdf, if supplied, must be a string, of RDF"

        if data_graph_file_path is not None:
            assert type(data_graph_file_path) == str, \
                "The value data_graph_file_path, if supplied, must be a string, of RDF, in the Turtle format"

        if profiles_graph_obj is not None:
            assert type(profiles_graph_obj) == rdflib.Graph, \
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
                format=rdflib.util.guess_format(data_graph_file_path)
            )

        if profiles_graph_obj is not None:
            self.pg = data_graph_obj
        elif profiles_graph_ttl is not None:
            self.pg.parse(data=data_graph_ttl, format="turtle")
        elif profiles_graph_file_path is not None:
            self.pg.parse(
                profiles_graph_file_path,
                format=rdflib.util.guess_format(data_graph_file_path)
            )
            self.profiles_graph_file_path = profiles_graph_file_path

        assert len(self.dg) > 0, "The Data Graph has not been able to be read"

        assert len(self.pg) > 0, "The Profiles Graph has not been able to be read"

        # make nice namespaces
        self.SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        PROF = rdflib.Namespace('http://www.w3.org/ns/dx/prof/')
        self.pg.bind('prof', PROF)
        ROLE = rdflib.Namespace('http://www.w3.org/ns/dx/prof/role/')
        self.pg.bind('role', ROLE)

    def _build_shapes_graph_for_profile(self, profile_uri):
        """Parses the profiles hierarchy graph and collects and merges all the SHACL validator resources within the
        given Profile, indicated by profile_uri,'s hierarchy

        :param profile_uri:
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

    def validate(self, shacl_only=False, by_class=False, instance_uri_claim=None, profile_uri=None):
        """Validates a data graph using a shapes graph generated from a profile hierarchy

        :param shacl_only: if this is True, Cheka will perform normal SHACL validation only
        :param by_class: if this is True, instance_uri will be ignored and profile_uri MUST be set
        :param instance_uri_claim: if this is set, by_class must not be set to True
        :param profile_uri: if this is set, validation against this profile and its hierarchy will be tested only,
        regardless of conformance claims in the data graph
        :return:
        """
        if shacl_only:
            valid, v_graph, v_msg = validate(
                self.dg,
                meta_shacl=True,  # validate the SHACL graph first
                shacl_graph=self.sg,
                # inference='rdfs', # not sure if this should be used
                abort_on_error=False
            )
            # conforms, results_graph, results_text = r
            return (valid, v_graph, v_msg, profile_uri)

        # testing inputs
        if by_class and instance_uri_claim is not None:
            raise IOError('You must not set both by_class to True and give instance_uri a value simultaneously')
        # for testing - print('validate(): {}, {}, {}'.format(by_class, instance_uri, profile_uri))
        # if by_class is True, validate things by class (i.e. not by instance_uri)
        if by_class:
            # ignore instance_uri
            # if profile_uri is set, only load that profile's validation resource hierarchy
            if profile_uri is not None:
                self._build_shapes_graph_for_profile(profile_uri)

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
                self._build_shapes_graph_for_profile(inst[1])

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
