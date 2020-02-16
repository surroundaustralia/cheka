import rdflib
from rdflib.namespace import DCTERMS
from os.path import dirname, realpath, join, abspath
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
        for s, o in self.dg.subject_objects(DCTERMS.conformsTo):
            print('Stub _find_validation_targets(): {} -> {}'.format(s, o))

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

    def validate(self, profile_uri):
        self._parse_shacl_files_for_profile(profile_uri)

        # use pySHACL to validate data graph against all shapes graphs
        r = validate(
            self.dg,
            shacl_graph=self.sg,
            # inference='rdfs', # not sure if this should be used
            abort_on_error=False
        )
        # conforms, results_graph, results_text = r
        return r
