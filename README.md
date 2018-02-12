# DNS
CLI application used to migrate DNS entries from a source to a target DNS.
Currently supports migration from Dynect to AWS Route53 only.

# Pre-requisites 
* Docker
* Docker Compose 

# Usage

## Setup
* Update the contents in the `config.json` file. Currently supports `Dynect` only.
    - `customer`: the Dynect customer
    - `username`: the username of a user that has admin permissions on Dynect
    - `password`: the password of the user
* Update the `credentials` and `config` files with the respective AWS credentials and configs. This account should permissions to CRUD DNS records and host files in Route53
* `docker-compose build`


## Running the Application
* `docker-compose run dns_migration_tools bash`
* `python dns.py <connector> <command> <entity> <options>`
* E.g. `python dns.py dynect migrate zones --input-file /app/input_files/zones`
	- `/app/input_files/zones` is a file that contains the names of the zones that need to be migrated.


This code was run on `Python 2.7` and `Ubuntu 16.04` using `Docker 17.06.0-ce` and `Docker 1.14.0`

# TODO
* See comments in code.
