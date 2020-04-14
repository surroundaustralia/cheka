#!/usr/bin/env python3
import argparse
import pprint
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

    parser.add_argument(
        '-d', '--data',
        help='The data graph, an RDF file, which is being validated.',
        type=lambda x: is_valid_file(parser, x),
        required=True
    )

    parser.add_argument(
        '-p', '--profiles',
        help='The profiles hierarchy, an RDF file, that relates the Profiles and Standards for which you want to '
             'extract validating Profile Resources.',
        type=lambda x: is_valid_file(parser, x),
        required=True
    )

    parser.add_argument(
        '-i', '--instance-uri',
        help='The specific profile URI that you wish to validate the data graph against. This need not be set, in which'
             'case, Cheka will look for conformance claims (dct:conformsTo) in the data graph.',
        type=str
    )

    parser.add_argument(
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
