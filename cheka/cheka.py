import logging
from typing import Union
from pathlib import Path
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import DCTERMS, PROF, RDF, SH
from os import mkdir
from rdflib.paths import ZeroOrMore
from pyshacl import validate
import uuid
import json
import pickle
import shutil
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


class UnknownProfileError(ValueError):
    pass


class Cheka:
    ROLE = Namespace("http://www.w3.org/ns/dx/prof/role/")
    RDF_SERIALIZER_TYPES_MAP = {
        "text/turtle": "turtle",
        "text/n3": "n3",
        "application/n-triples": "nt",
        "application/ld+json": "json-ld",
        "application/rdf+xml": "xml",
        # Some common but incorrect mimetypes
        "application/rdf": "xml",
        "application/rdf xml": "xml",
        "application/json": "json-ld",
        "application/ld json": "json-ld",
        "text/ttl": "turtle",
        "text/ntriples": "nt",
        "text/n-triples": "nt",
        "text/plain": "nt",  # text/plain is the old/deprecated mimetype for n-triples
    }

    """The Cheka program main class that contains all of the functionality

    """
    def __init__(
        self,
        data: Union[Graph, str],
        profiles: Union[Graph, str],
        get_remote_profiles: bool = False
    ):
        self.VALIDATORS_DIR = Path(__file__).parent / "cache"

        self.dg = Graph()
        self.pg = Graph()
        self.sg = Graph()

        # validate & parse inputs
        self.dg = self._parse_input_parameter(data, "data")
        self.pg = self._parse_input_parameter(profiles, "profiles")

        # check graph aren't empty
        if len(self.dg) == 0:
            raise AssertionError("The data parameter you've supplied is a zero-length Graph")
        if len(self.pg) == 0:
            raise AssertionError("The profiles parameter you've supplied is a zero-length Graph")

        self.get_remote_profiles = get_remote_profiles

        # make nice namespaces
        self.pg.bind('prof', PROF)
        self.pg.bind('sh', SH)
        self.pg.bind('role', Cheka.ROLE)

        # expand the profiles graph
        self._expand_profiles_graph(self.pg)

        # establish cache dir & map
        if not Path.is_dir(self.VALIDATORS_DIR):
            mkdir(self.VALIDATORS_DIR)
        if not Path.is_dir(self.VALIDATORS_DIR):
            raise Exception("Could not create or access the validators cache directory, {}".format(self.VALIDATORS_DIR))
        self.VALIDATORS_MAP_FILE = Path(self.VALIDATORS_DIR) / "map.py"
        if not Path.is_file(self.VALIDATORS_MAP_FILE):
            with open(self.VALIDATORS_MAP_FILE, "w") as f:
                f.write(json.dumps({}))
        else:
            # we seem to already have a MAP file
            pass

        # cache all the artifacts for all the Profiles within the profile grapf (self.pg)
        # with RD with role of validator and conforming to SHACL
        self._cache_pg_validating_artifacts(self.pg)

    def _parse_input_parameter(self, parameter, parameter_name):
        if type(parameter) not in [Graph, str]:
            raise ValueError(
                "The parameter '{}' must be either an RDFlib graph object, "
                "a string of RDF (turtle format only) or the path of an RDF file (any format)".format(parameter_name)
            )

        if type(parameter) == Graph:
            return parameter
        elif type(parameter) == str:
            try:
                p = Path(parameter)

                if Path.is_file(p):
                    try:
                        return Graph().parse(parameter, format="turtle")
                    except Exception as e:
                        raise ValueError(
                            "You've supplied an invalid RDF file for parameter 'data', it could not be parsed. "
                            "The parser said: {}".format(e))
            except:
                pass

            try:
                return Graph().parse(data=parameter, format="turtle")
            except Exception as e:
                raise ValueError(
                    "You've supplied an invalid string value for parameter 'data' - no RDF data could be parse. "
                    "Either you've supplied a path to a file that cannot be found or, if supplying a string of "
                    "data, it is not valid in the Turtle format. The RDF parser said: {}".format(e))
        else:
            pass
            # can't ever get here due to type checking earlier in constructor

    def _expand_profiles_graph(self, pg: Graph):
        # type all profiles
        # dcterms:Standard instances are prof:Profiles instances
        for s, p, o in pg.triples((None, RDF.type, DCTERMS.Standard)):
            pg.add((s, RDF.type, PROF.Profile))
        # anything using prof:isProfileOf is a prof:Profile
        for s, p, o in pg.triples((None, PROF.isProfileOf, None)):
            pg.add((o, RDF.type, PROF.Profile))

        # type all RDs
        # anything indicated by prof:hasResource is a prof:ResourceDescriptor
        for s, p, o in pg.triples((None, PROF.hasResource, None)):
            pg.add((o, RDF.type, PROF.ResourceDescriptor))

    def _cache_pg_validating_artifacts(self, pg: Graph):
        # for each profile,
        #   get all its RDs with role 'validation' and conforms to SHACL,
        #       get all their artifacts' content
        #           lump them into a single validator graph for that Profile
        # store the validator per-profile in cache
        with open(self.VALIDATORS_MAP_FILE, "r") as f:
            map = json.load(f)

        for profile in pg.subjects(predicate=RDF.type, object=PROF.Profile):
            logging.debug("profile {}".format(profile))
            # if we already have a validator for this profile, do nothing
            if str(profile) in map.keys():
                logging.info("Using cached validators for Profile {}".format(profile))
            else:
                logging.info("Storing Profile {} in cache".format(profile))
                validator_graph = Graph()
                for rd in pg.objects(subject=profile, predicate=PROF.hasResource):
                    if (rd, PROF.hasRole, self.ROLE.validation) in pg \
                       and (rd, DCTERMS.conformsTo, URIRef("https://www.w3.org/TR/shacl/")) in pg:
                        for artifact_uri in pg.objects(subject=rd, predicate=PROF.hasArtifact):
                            # artifacts are either local file URIs or HTTP/HTTPS URIs
                            # either way, RDFlib's parse() can handle it
                            logging.debug("Seen artifact URI {}".format(artifact_uri))
                            try:
                                if str(artifact_uri).startswith("http"):
                                    logging.debug("Attempting to parse remote artifact {}".format(artifact_uri))
                                    rdf_request_headers = {
                                        "Accept": "text/turtle,application/x-turtle, "
                                                  "application/rdf+xml, "
                                                  "application/ld+json"
                                    }
                                    req = Request(str(artifact_uri), None, rdf_request_headers)
                                    with urlopen(req) as f:
                                        data = f.read().decode('utf-8')
                                    validator_graph.parse(data=data)
                                elif str(artifact_uri).startswith("file"):
                                    artifact_path = Path(str(artifact_uri).replace("file://", ""))
                                    logging.debug("Attempting to parse local artifact {}".format(artifact_path))
                                    if Path.is_file(artifact_path):
                                        logging.debug("Found file at location {}".format(artifact_path))
                                        validator_graph.parse(artifact_path)
                                    else:
                                        artifact_path = Path(__file__).parent.parent / "tests" / "validators" / artifact_path
                                        if Path.is_file(artifact_path):
                                            logging.debug("Found file in tests validators dir {}".format(artifact_path))
                                            validator_graph.parse(artifact_path)
                                        else:
                                            raise ValueError("Validator local file indicated at {} but not found"
                                                             .format(artifact_path))
                                else:
                                    raise ValueError("Validator not indicated as wither a web resource ('http...') or "
                                                     "a local file ('file:///...') in its URI so it cannot be found")
                            except Exception as e:
                                # do nothing, can't parse RDF
                                print(e)
                                logging.info(
                                    "Attempted to dereference Artifact {} but got an error: {}"
                                        .format(artifact_uri, str(e))
                                )

                if len(validator_graph) > 0:
                    # make up a file name for the validator
                    fn = str(uuid.uuid4())
                    # write to map
                    map[str(profile)] = fn
                    with open(self.VALIDATORS_MAP_FILE, "w") as f:
                        f.write(json.dumps(map, indent=4))
                    # write validator content
                    # validator_graph.serialize(destination=str(Path(self.VALIDATORS_DIR / (fn + ".ttl"))), format="turtle")
                    with open(str(Path(self.VALIDATORS_DIR / (fn + ".p"))), "wb") as f:
                        pickle.dump(validator_graph, f)

        # warn about Profiles with no validators
        with open(self.VALIDATORS_MAP_FILE, "r") as f:
            map = json.load(f)
        for profile in pg.subjects(predicate=RDF.type, object=PROF.Profile):
            if str(profile) not in map.keys():
                logging.info("No validators are recorded for Profile {}".format(profile))

    def _get_profiles_hierarchy(self, pg, profile_uri: str) -> set:
        print("_get_profiles_hierarchy()")
        profiles = []
        for o in pg.objects(subject=URIRef(profile_uri), predicate=PROF.isProfileOf*ZeroOrMore):
            profiles.append(str(o))
        return set(profiles)

    def _get_artifact_uris_per_profile(self, pg: Graph, profile_uri: URIRef):
        artifact_uris = []

        for o in pg.objects(subject=profile_uri, predicate=PROF.hasResource):
            if (o, PROF.hasRole, Cheka.ROLE.validation) in pg:
                rds_artifact_uris = []
                for o2 in pg.objects(subject=o, predicate=PROF.hasArtifact):
                    rds_artifact_uris.append(str(o2))
                # for this RD,
                # prefer a file already in the VALIDATORS_DIR
                # over one still local, but prefer local bot in VALIDATORS_DIR
                # to remote
                u = next((x for x in rds_artifact_uris if Cheka.VALIDATORS_DIR in x), None)
                if u is None:
                    u = next((x for x in rds_artifact_uris if x.startswith("file://") or x.startswith("/")), None)
                    if u is None:
                        u = rds_artifact_uris[0]
                artifact_uris.append(u)
        return artifact_uris

    def _get_artifact_uris(self, pg: Graph, profile_uri=None):
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

        artifact_uris = []

        if profile_uri is None:
            # get all profiles' validators

            # for every subject,
            # if it's a Profile (or a Standard, as included by graph expansion)
            # get all of it's ResourceDescriptors
            # if the Role is validator,
            # get the artifact link
            for s, o in pg.subject_objects(predicate=RDF.type):
                if o == PROF.Profile:
                    artifact_uris.extend(self._get_artifact_uris_per_profile(self.pg, s))
        else:
            # for the given profile_uri
            # get all of it's ResourceDescriptors
            # if the Role is validator,
            # get the artifact link
            for s, p, o in pg.triples((URIRef(profile_uri), PROF.isProfileOf*ZeroOrMore, None)):
                artifact_uris.extend(self._get_artifact_uris_per_profile(self.pg, o))

        return artifact_uris

    # def _get_shapes_from_profiles_graph(self, profile_uri=None):
    #     """Parses the profiles hierarchy graph and, if no profile_uri is given, collects and merges all the SHACL
    #     validator resources related to all profiles. If a profile_uri is given, collects and merges all the SHACL
    #     validator resources related to the identified profile and the things it profiles.
    #
    #     :param profile_uri: the URI of a profile within the hierarchy
    #     :return:
    #     """
    #
    #     q = '''
    #         SELECT ?shacl_file
    #         WHERE {{
    #             <{}> prof:isProfileOf* ?p .
    #             ?p prof:hasResource ?r .
    #             ?r prof:hasRole role:validation .
    #             ?r prof:hasArtifact ?shacl_file .
    #         }}
    #         '''
    #     # TODO: indicated graphs already stored in memory to avoid repeated parsing
    #     # TODO: pickle parsed RDF files for future stateless use
    #     for r in self.pg.query(q.format(profile_uri)):
    #         if str(r['shacl_file']).startswith('file://'):
    #             # this is a local file
    #             PROFILES_GRAPH_FILE_DIR = dirname(realpath(self.profiles_graph_file_path))
    #             f = join(PROFILES_GRAPH_FILE_DIR, str(r['shacl_file']).replace('file://', ''))
    #             self.sg.parse(
    #                 f,
    #                 format=rdflib.util.guess_format(f)
    #             )
    #         else:
    #             # TODO: test shapes graph from URI
    #             # get the shapes graph from URI
    #             r = requests.get(str(r['shacl_file']))
    #             if r.ok:
    #                 self.sg.parse(
    #                     r.text,
    #                     format=r.headers['Content-Type']
    #                 )

    def _validate_pyshacl(self, validator_graph: Graph) -> tuple:
        """Perform standard pySHACL validation"""
        return validate(
            self.dg,
            meta_shacl=True,
            shacl_graph=validator_graph,
            # inference='rdfs', # not sure if this should be used
            abort_on_error=False
        )

    def validate(self, strategy: str = "shacl", profile_uri: str = None, instance_uri: str = None):
        """
        """

        strategies = [
            "shacl",
            "profile",
            "claims"
        ]
        if strategy not in strategies:
            raise ValueError(
                "Strategy unknown: You must supply a strategy parameter of either None or one of '{}' to the "
                "validate() function".format("', '".join(strategies))
            )

        with open(self.VALIDATORS_MAP_FILE, "r") as f:
            validators_map = json.load(f)

        vg = Graph()

        if strategy == "shacl":
            # use all the validators for all profile in pg
            for p in self.pg.subjects(predicate=RDF.type, object=PROF.Profile):
                inc = validators_map.get(str(p))
                if inc is not None:
                    with open(Path(self.VALIDATORS_DIR / (validators_map.get(str(p)) + ".p")), "rb") as f:
                        vg = vg + pickle.load(f)

            return self._validate_pyshacl(vg)

        elif strategy == "profile":
            if profile_uri is None:
                raise ValueError(
                    "profile_uri None: You must supply a profile_uri value to the validate() function if selecting "
                    "the strategy 'profile'"
                )
            # get all the validators for all the Profiles in this Profile's hierarchy
            # validate the data one Profile at a time
            hierarchies = self._get_profiles_hierarchy(self.pg, profile_uri)

            # if we don't have profile info for a profile and if get_remote_profiles is True, try and get it online
            if self.get_remote_profiles:
                with open(self.VALIDATORS_MAP_FILE, "r") as f:
                    map = json.load(f)

                missing = []
                for h in hierarchies:
                    if h not in map.keys():
                        missing.append(h)
                if len(missing) > 0:
                    logging.info(
                        "The supplied profiles graph and the profiles cache do not contain information for the "
                        "profiles:\n{}.\nAttempting to get info online".format("\n".join(missing))
                    )
                for m in missing:
                    self._dereference_and_cache_remote_profile(m)

            # if len(hierarchies) == 1 and hierarchies.pop() == profile_uri:
            #     raise UnknownProfileError(
            #         "The profile_uri value you supplied validate(), {}, didn't match any known profile URIs"
            #             .format(profile_uri)
            #     )
            vs = []
            for h in hierarchies:
                inc = validators_map.get(h)
                if inc is not None:
                    with open(Path(self.VALIDATORS_DIR / (inc + ".p")), "rb") as f:
                        vg = vg + pickle.load(f)
                vs.append((h,) + self._validate_pyshacl(vg))
            all_valid = all([x[1] for x in vs])
            return [all_valid] + vs

        elif strategy == "claims":
            raise NotImplemented("This strategy is planned but not implemented yet")
            # look in the Data Graph
            # find all instances that claim conformance to something
            # test each conformance claim
            #   if we know the profile: ok
            #   else: report claim un-actionable without download
            vs = []
            for inst, profile in self.dg.subject_objects(predicate=DCTERMS.conformsTo):
                inc = validators_map.get(profile)
                if inc is not None:
                    with open(Path(self.VALIDATORS_DIR / (inc + ".p")), "rb") as f:
                        vg = vg + pickle.load(f)
                vs.append((profile,) + self._validate_pyshacl(vg))

    def clear_cache(self):
        """Clears the cache of Profiles' validators

        Deleted the VALIDATORS_DIR directory and all of its content"""
        if Path.is_dir(self.VALIDATORS_DIR):
            shutil.rmtree(self.VALIDATORS_DIR)

    def _dereference_and_cache_remote_profile(self, profile_uri):
        # go online, get the profile, bring it in to the Profiles Graph
        logging.info("Trying to get info online for Profile {}".format(profile_uri))
        g = Graph()
        try:
            g.parse(location=profile_uri)
            if len(g) == 0:
                r = urlopen(Request(profile_uri, headers={'Accept-Profile': "<>"}))
        except Exception as e:
            # do nothing, can't parse RDF
            logging.info(
                "Attempted to dereference Profile {} but got an error: {}".format(profile_uri, str(e))
            )

        self._expand_profiles_graph(g)

        self._cache_pg_validating_artifacts(g)
