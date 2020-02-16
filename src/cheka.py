import rdflib
from rdflib.namespace import DCTERMS
from os.path import dirname, realpath, join
import requests
from pyshacl import validate


class Cheka:
    def __init__(self, data_graph_file_path, profiles_graph_file_path):
        # parse input RDF files
        self.profiles_graph_file_path = profiles_graph_file_path
        self._parse_inputs(data_graph_file_path, profiles_graph_file_path)

        # find all the things in the data graph that need to be validated
        self._find_validation_targets()
    
    def _parse_inputs(self, data_graph_file_path, profiles_graph_file_path):
        try:
            # data graph
            self.dg = rdflib.Graph().parse(
                data_graph_file_path, 
                format=rdflib.util.guess_format(data_graph_file_path)
            )

            # profiles graph
            self.pg = rdflib.Graph().parse(
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

    def _find_validation_targets(self):
        objects_profiles = []
        for s, o in self.dg.subject_objects(DCTERMS.conformsTo):
            objects_profiles.append((s, o))
            # print('Stub _find_validation_targets(): {} -> {}'.format(s, o))

        return objects_profiles

    def _parse_shacl_files_for_profile(self, profile_uri):
        self.sg = rdflib.Graph()

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

    def _validate_against_hierarchy(self, data_graph, profile_uri):
        self._parse_shacl_files_for_profile(profile_uri)

        # use pySHACL to validate data graph against all shapes graphs
        valid, v_graph, v_msg = validate(
            data_graph,
            shacl_graph=self.sg,
            # inference='rdfs', # not sure if this should be used
            abort_on_error=False
        )
        # conforms, results_graph, results_text = r
        return (valid, v_graph, v_msg, profile_uri)

    def validate(self, profile_uri=None):
        if profile_uri is None:
            # get profile_uris from data graph for all things claiming conformance
            valid = True
            v_graph = rdflib.Graph()
            v_msg = []
            for pair in self._find_validation_targets():
                object_uri, profile_uri = pair
                # extract from self.dg just the object to be validated
                mini_graph = rdflib.Graph()
                for s, p, o in self.dg.triples((object_uri, None, None)):
                    mini_graph.add((s, p, o))

                # validate the object against the profile hierarchy it claims conformance to
                mini_result = self._validate_against_hierarchy(mini_graph, profile_uri)
                if not mini_result[0]:  # i.e. invalid
                    valid = False
                    v_graph += mini_result[1]
                    v_msg.append(mini_result[2])

            # emulate pySHACL's return style + profile URI
            return (valid, v_graph, v_msg, profile_uri)
        else:
            return self._validate_against_hierarchy(self.dg, profile_uri)
