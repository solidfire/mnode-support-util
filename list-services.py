#!/usr/bin/env python3

import argparse
import logging
import sys
import yaml
from git import Git
import json

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

_LOG = logging.getLogger()
DOCKER_COMPOSE_FILE='./docker-compose.yml'

class Service:
    def __init__(self, name: str, image_name: str, version: str):
        self.name = name
        self.image_name = image_name
        self.version = version

    def __str__(self):
        return f'{self.name},{self.image_name},{self.version}'

def to_service(name: str, imageStr: str) -> Service:
    if name == 'simple-data':
        image, version = imageStr.split(':', 1)
        return Service(name=name, version=version, image_name=image)
    delim = '/' if 'sf-art' in imageStr else ':'
    _, image_map = imageStr.split(delim, 1)
    image_name, version = image_map.split(':', 1)
    return Service(name=name, image_name=image_name, version=version)


def logger_setup():
    """ logger_setup will configure the a logger to stdout. """
    _LOG.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _LOG.addHandler(handler)

def get_args() -> argparse.Namespace:
    """ get_args will pull the --tag parameter. """
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', help='The tag to display child service versions.', required=True)
    n = parser.parse_args()
    return n
    
def checkout_tag(version_tag: str) -> None:
    import os
    cwd = os.getcwd
    g = Git(working_dir=cwd)
    g.checkout(version_tag)

def parse_compose():
    with open(DOCKER_COMPOSE_FILE) as compose_file:
        compose_data = yaml.load(compose_file, Loader=yaml.FullLoader)
        return compose_data

def get_services(service_map : dict) -> list:
    current = []
    for service in service_map:
        image = service_map[service]['image']
        s = to_service(name=service, imageStr=image)
        current.append(s)
    return current


def main():
    args = get_args()
    checkout_tag(version_tag=args.tag)
    services = parse_compose()
    service_map = services['services']
    _LOG.info(service_map)
    s = get_services(service_map=service_map)
    [_LOG.info(str(a)) for a in s]

    tag = args.tag.replace('/','-')
    csv_output_file = f'management-services-{tag}.csv'
    json_output_file = f'management-services-{tag}.json'

    with open (csv_output_file,'w') as output:
        output.write('service-name,image-name,version\n')
        [output.write(str(a)+'\n') for a in s]

    json_str = json.dumps(s, default= lambda x: x.__dict__, indent=4)
    with open (json_output_file,'w') as output:
        output.write(json_str+'\n')

if __name__ == "__main__":
    logger_setup()
    args = get_args()
    main()