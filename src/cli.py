#!/usr/bin/env python3
import argparse
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

    args = parser.parse_args()

    # do stuff
    c = Cheka(args.data.name, args.profiles.name)
    v = c.validate(profile_uri='http://example.org/profile/Profile_B')
    if v[0]:
        print('valid')
    else:
        print('invalid')
        print(v[2])
