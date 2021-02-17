#!/usr/bin/env python3
import argparse
import ast
import glob
import pathlib
import yaml

p = pathlib.Path('src/charm.py')


aliases = ['config']


def is_self_model_config(chunk):
    if (
        type(chunk) == ast.Attribute
        and chunk.attr == 'config'
        and type(chunk.value) == ast.Attribute
        and chunk.value.attr == 'model'
        and type(chunk.value.value) == ast.Name
        and chunk.value.value.id == 'self'
    ):
        return True
    return False


def is_config_lookup(chunk, aliases):
    """ Chunk should be of type ast.Subscript """
    if type(chunk.value) == ast.Name:
        if chunk.value.id in aliases:
            return True
    if type(chunk.value) == ast.Attribute and is_self_model_config(chunk.value):
        return True
    return False


def get_keys_from_code(code, aliases, keys):
    for chunk in ast.walk(code):
        if type(chunk) == ast.Subscript and is_config_lookup(chunk, aliases):
            if chunk.slice.value.value in keys:
                keys[chunk.slice.value.value].append(chunk.lineno)
            else:
                keys[chunk.slice.value.value] = [chunk.lineno]


def get_keys_from_config(path):
    with path.open() as f:
        conf = yaml.safe_load(f)
    return conf['options'].keys()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--files', action='store', default='src/*', help='Files to check'
    )
    parser.add_argument(
        '-c',
        '--config',
        action='store',
        type=pathlib.Path,
        default=pathlib.Path('config.yaml'),
        help='path to config.yaml',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    code_keys = {}
    for path in glob.glob(args.files, recursive=True):
        with open(path) as f:
            code = ast.parse(f.read())
        get_keys_from_code(code, aliases, code_keys)
    config_keys = get_keys_from_config(args.config)
    errors = []
    for key in code_keys:
        if key not in config_keys:
            errors.append({key: code_keys[key]})
    print(errors)


if __name__ == '__main__':
    main()
