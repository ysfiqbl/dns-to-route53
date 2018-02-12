import time
import logging
import argparse
import json, re
import logging
from connectors.dynect import Dynect
import boto3


class Dns(object):
    def __init__(self, connector, params):
        self.connector = connector
        self.params = params


    def init(self):
        """
        Initialize the connector
        """
        if self.connector == 'dynect':
            self.dynect_init()


    def get_zone(self, name):
        """
        Get zone
        TODO: Create a Zone class that can be used by all connectors

        Args:
            name (string): Name of zone

        Returns:
            Zone: Zone object of the configured connector
        """
        return self.dns.get_zone(name)


    def get_zones(self):
        """
        Get all zones
        TODO: Create a Zone class that can be used by all connectors

        Returns:
            Zones: List of Zone objects
        """
        return self.dns.get_zones()


    def get_zone_records(self, zone_name):
        """
        Get all zone records
        TODO: Create a Record class that can be used by all connectors

        Args:
            zone_name (string): Name of zone

        Returns:
            Records: List of Records belonging to a Zone
        """
        return self.dns.get_zone_records(zone_name)


    def dynect_init(self):
        """
        Initialize Dynect connector
        TODO: Create a Credentials class that can be used by all connectors

        Returns:
            Records: List of Records belonging to a Zone
        """
        self.dns = Dynect(self.params['customer'], self.params['username'], self.params['password'])


    def get_aws_change_batch(self, records):
        """
        Get the value for the 'ChangeBatch' attribute for the 'ChangeResourceRecordSets'
        http://boto3.readthedocs.io/en/latest/reference/services/route53.html#Route53.Client.change_resource_record_sets
        https://docs.aws.amazon.com/Route53/latest/APIReference/API_ChangeResourceRecordSets.html

        Args:
            records (string): List of Records belonging to a Zone

        Returns:
            ChangeBatch: value for the 'ChangeBatch' attribute 
        """
        return self.dns.get_aws_change_batch(records)


if __name__ == '__main__':
    logging.basicConfig(filename='/app/dns.log', level=logging.INFO)

    with open('/app/config.json', 'r') as config:
        conf = json.load(config)
        src_config = conf['source_dns']
        target_config = conf['target_dns']
        aws_access_key_id = target_config['aws_access_key_id']
        aws_secret_access_key = target_config['aws_secret_access_key']

    parser = argparse.ArgumentParser()
    parser.add_argument('connector', help='Source DNS account. e.g. dynect')
    parser.add_argument('command', help='create, migrate, get, delete entities.')
    parser.add_argument('entity', help='Entity to perform the comment on. E.g. zone')
    parser.add_argument('--zone-name', help='Name of zone')
    parser.add_argument('--input-file', help='Used for bulk operations. Path to file containing the inputs required for the bulk operation')
    args = parser.parse_args()
    
    connector = args.connector
    command = args.command
    entity = args.entity
    zone_name = args.zone_name
    input_file = args.input_file
    
    dns = Dns(connector, src_config)
    dns.init()
    boto_client = boto3.client('route53')
    timestamp = str(time.time()).split('.')[0]

    if command == 'get':
        if entity == 'zone':
            print(dns.get_zone(zone_name))
        
        if entity == 'records':
            records = dns.get_zone_records(zone_name)
            for record in records:
                for entry in records[record]:
                    print(entry.fqdn)
                    print(entry.rdata())

        if entity == 'statistics':
            stats = {}
            with open(input_file, 'r') as zones:
                for zone in zones:
                    records = dns.get_zone_records(zone.strip('\n'))
                    for record in records:
                        for entry in records[record]:
                            name = entry.rec_name
                            print(name)
                            if name in stats:
                                stats[name] += 1
                            else:
                                stats[name] = 1
                    print(stats)
                    time.sleep(5)
            
            print(stats)


    if command == 'migrate':
        if entity == 'records':
            if input_file != None:
                z_info = '/app/output_files/zones.info'
                z_err = '/app/output_files/zones.err'
                with open(input_file, 'r') as zones, open(z_info, 'a') as zone_info, open(z_err, 'a') as zone_err:

                    for zone in zones:
                        zone = zone.strip('\n')
                        logging.info('Creating hosted zone {0}...'.format(zone))
                        result = boto_client.create_hosted_zone(
                            Name = zone,
                            CallerReference = '{0}-{1}'.format(zone, timestamp),
                            HostedZoneConfig = {
                                'Comment': 'Migrated from Dynect'
                            }
                        )
                        
                        zone_id = result['HostedZone']['Id'].split('/')[2]
                        change_id = result['ChangeInfo']['Id'].split('/')[2]
                        insync = result['ChangeInfo']['Status'] == 'INSYNC'
                        nameservers = result['DelegationSet']['NameServers']
                        
                        zone_info.write(zone + '\n')
                        for nameserver in nameservers:
                            zone_info.write(nameserver + '\n')
                        zone_info.write('\n')                            

                        logging.info('Created hosted zone {0} with id {1}'.format(zone, zone_id))
                        logging.info('Name Servers for {0}: {1}'.format(zone, nameservers))
                        records = dns.get_zone_records(zone)

                        change_batch = dns.get_aws_change_batch(records)
                        print(change_batch)
                        response = boto_client.change_resource_record_sets(
                            HostedZoneId=zone_id,
                            ChangeBatch=change_batch
                        )

                        print(response)
                        
            else:
                print('Non bulk transfer. Not implmented yet.')
