#!/usr/bin/env python3
import argparse


# used to determine whether or not a given path is actually a real file
def is_valid_file(parser, arg):
    try:
        return open(arg, 'r')
    except:
        parser.error('The file %s does not exist!' % arg)


print('Yes, I am using Python')

parser = argparse.ArgumentParser()

parser.add_argument(
    '-d', '--datagraph',
    help='The input data graph, an RDF file, which is being validated.',
    type=lambda x: is_valid_file(parser, x),
    required=True
)

parser.add_argument(
    '-p', '--profiles',
    help='The Profiles Vocabulary hierarchy, an RDF file, that relates the Profiles and Standards for which you want to extract validating Profile Resources.',
    type=lambda x: is_valid_file(parser, x),
    required=True
)

args = parser.parse_args()

with open(args.profiles.name) as f:
    print(len(f.readlines()))

print('end')