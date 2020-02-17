import rdflib
from rdflib.namespace import DCTERMS, RDF
from os.path import dirname, realpath, join
import requests
from pyshacl import validate


class Cheka:
    """The Cheka program main class that contains all of the functionality

    """
    def __init__(self, data_graph_file_path, profiles_graph_file_path):
        self.dg = rdflib.Graph()
        self.pg = rdflib.Graph()
        self.sg = rdflib.Graph()

        # parse input RDF files
        self.profiles_graph_file_path = profiles_graph_file_path
        self._parse_inputs(data_graph_file_path, profiles_graph_file_path)

        # register the SHACL namespace for convenience
        self.SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
    
    def _parse_inputs(self, data_graph_file_path, profiles_graph_file_path):
        try:
            # data graph
            self.dg.parse(
                data_graph_file_path, 
                format=rdflib.util.guess_format(data_graph_file_path)
            )

            # profiles graph
            self.pg.parse(
                profiles_graph_file_path, 
                format=rdflib.util.guess_format(profiles_graph_file_path)
            )
            PROF = rdflib.Namespace('http://www.w3.org/ns/dx/prof/')
            self.pg.bind('prof', PROF)
            ROLE = rdflib.Namespace('http://www.w3.org/ns/dx/prof/role/')
            self.pg.bind('role', ROLE)
        except Exception as e:
            print(e)
            exit()

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

    def validate(self, by_class=False, instance_uri=None, profile_uri=None):
        """Validates a data graph using a shapes graph generated from a profile hierarchy

        :param by_class: if this is set to True, instance_uri will be ignored and profile_uri MUST be set
        :param instance_uri: if this is set, by_class must not be set to True
        :param profile_uri: if this is set, validation against this profile and its hierarchy will be tested only,
        regardless of conformance claims in the data graph
        :return:
        """
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
            if instance_uri is not None:
                # if a profile_uri is given, indicate the instance is to be validated using that only
                if profile_uri is not None:
                    instances_for_validation.append((instance_uri, profile_uri))
                # if a profile_uri is not given, look for conformance claims for validation target. Can by multiple
                else:
                    for o in self.dg.objects(subject=rdflib.URIRef(instance_uri), predicate=DCTERMS.conformsTo):
                        instances_for_validation.append((instance_uri, o))
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

                if not local_valid[0]:  # i.e. invalid
                    valid = False
                    v_graph += local_v_graph
                    v_msg.append(local_v_msg)
                self.sg = None
                self.sg = rdflib.Graph()

            # emulate pySHACL's return style + profile URI
            return (valid, v_graph, v_msg, profile_uri)
