#!/usr/bin/env python3
import argparse


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
        help='The profiles hierarchy, an RDF file, that relates the Profiles and Standards for which you want to extract validating Profile Resources.',
        type=lambda x: is_valid_file(parser, x),
        required=True
    )

    args = parser.parse_args()

    # do stuff
    with open(args.profiles.name) as f:
        print(len(f.readlines()))

    print('end')