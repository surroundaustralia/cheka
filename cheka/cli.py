#!/usr/bin/env python3
import argparse
import pprint
import rdflib
from cheka import Cheka


if __name__ == '__main__':
    # check input vars
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--data',
        help='A file containing RDF data which is to be validated.',
        type=rdflib.Graph,
        required=True
    )

    parser.add_argument(
        '-p', '--profiles',
        help='A file containing RDF of the profiles hierarchy to be used for validating the data.',
        type=rdflib.Graph,
        required=True
    )

    validation_type = parser.add_mutually_exclusive_group()

    validation_type.add_argument(
        '-s', '--shacl',
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

    validation_type.add_argument(
        '-r', '--get-remotes',
        help='If set, tells Cheka to try and look up profile information, e.g. validators, via the profile\'s URI.',
        type=str
    )

    args = parser.parse_args()

    c = Cheka(args.data.name, args.profiles.name)
    v = c.validate(profile_uri=args.uri)  # TODO: read from any of the validation_type values
    if v[0]:
        pprint.pprint('valid')
    else:
        pprint.pprint('invalid')
        pprint.pprint(v[2])
