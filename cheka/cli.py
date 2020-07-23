#!/usr/bin/env python3
import argparse
import pprint
import rdflib
from cheka import Cheka


# used to determine whether or not a given path is actually a real file
def is_valid_file(parser, arg):
    try:
        return open(arg, 'r')
    except:
        parser.error('The file %s does not exist!' % arg)


if __name__ == '__main__':
    # check input vars
    parser = argparse.ArgumentParser()

    group_data = parser.add_mutually_exclusive_group()

    group_data.add_argument(
        '-dg', '--datagraph',
        help='RDF data as an in-memory RDFlib graph, which is being validated.',
        type=rdflib.Graph,
        required=True
    )

    group_data.add_argument(
        '-ds', '--datastring',
        help='RDF data as a string, in the Turtle format, which is being validated.',
        type=str,
        required=True
    )

    group_data.add_argument(
        '-df', '--datafile',
        help='The an RDF file, the data from which is being validated.',
        type=lambda x: is_valid_file(parser, x),
        required=True
    )

    group_profiles = parser.add_mutually_exclusive_group()

    group_data.add_argument(
        '-pg', '--profilesgraph',
        help='The profiles hierarchy as an in-memory RDFlib graph.',
        type=rdflib.Graph,
        required=True
    )

    group_data.add_argument(
        '-ps', '--profilesstring',
        help='The profiles hierarchy as a string, in the Turtle format.',
        type=str,
        required=True
    )

    group_profiles.add_argument(
        '-p', '--profiles',
        help='The profiles hierarchy, as an RDF file.',
        type=lambda x: is_valid_file(parser, x),
        required=True
    )

    validation_type = parser.add_mutually_exclusive_group()

    validation_type.add_argument(
        '-s', '--shacl-only',
        help='\'SHACL\': use this flag to perform normal SHACL validation. Prevents any profiles-based validation.',
        action='store_false'
    )

    validation_type.add_argument(
        '-i', '--instance-uri',
        help='The specific profile URI that you wish to validate the data graph against. This need not be set, in which'
             'case, Cheka will look for conformance claims (dct:conformsTo) in the data graph.',
        type=str
    )

    validation_type.add_argument(
        '-u', '--profile-uri',
        help='The specific profile URI that you wish to validate the data graph against. This need not be set, in which'
             'case, Cheka will look for conformance claims (dct:conformsTo) in the data graph.',
        type=str
    )

    args = parser.parse_args()

    # do stuff
    c = Cheka(args.data.name, args.profiles.name)
    v = c.validate(profile_uri=args.uri)
    if v[0]:
        pprint.pprint('valid')
    else:
        pprint.pprint('invalid')
        pprint.pprint(v[2])
