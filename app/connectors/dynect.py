from dyn.tm.session import DynectSession
from dyn.tm.zones import Zone
from dyn.tm.zones import get_all_zones

class Dynect(object):
    """
    Wrapper object for the Dyn API
    See links below for detailed documentation on functions
    https://github.com/dyninc/dyn-python
    http://dyn.readthedocs.io/en/latest/
    """
    
    def __init__(self, customer, username, password):
        self.customer = customer
        self.username = username
        self.password = password

    
    def get_zone(self, name):
        self.start_session()
        zone = Zone(name)
        records = zone.get_all_records()
        self.close_session()
        return zone


    def get_zones(self):
        self.start_session()            
        zones = get_all_zones()
        self.close_session()
        return zones            
    

    def get_zone_records(self, zone_name):
        self.start_session()
        zone = Zone(zone_name)
        records = zone.get_all_records()
        self.close_session()
        return records

    
    def get_aws_change_batch(self, records):
        """
        Get the value for the 'ChangeBatch' attribute for the 'ChangeResourceRecordSets'
        http://boto3.readthedocs.io/en/latest/reference/services/route53.html#Route53.Client.change_resource_record_sets
        https://docs.aws.amazon.com/Route53/latest/APIReference/API_ChangeResourceRecordSets.html

        Args:
            records (string): List of Records belonging to a Zone

        Returns:
            ChangeBatch: JSON object for the value 'ChangeBatch' attribute 
        """

        changes = []
        rec_json = {}
        array_index_map = {}

        for key in records:
            for record in records[key]:
                print(record)
                rec_type = record.rec_name
                fqdn = record.fqdn
                value = self.get_value(record)

                if value['Value'] != None:
                    array_index_key = '{0}{1}'.format(rec_type, fqdn)
                    if array_index_key in array_index_map:
                        change = changes[array_index_map[array_index_key]]
                        change['ResourceRecordSet']['ResourceRecords'].append(value)
                    else:
                        change = {}
                        change['Action'] = 'CREATE'
                        change['ResourceRecordSet'] = {}
                        change['ResourceRecordSet']['Name'] = fqdn
                        change['ResourceRecordSet']['Type'] = rec_type.upper()
                        change['ResourceRecordSet']['TTL'] = record.ttl
                        change['ResourceRecordSet']['ResourceRecords'] = [value]
                        changes.append(change)
                        array_index_map[array_index_key] = len(changes) - 1
                
        change_batch = {
            'Changes': changes
        }

        return change_batch


    def get_value(self, record):
        """
        Helper function to extract and return the value of the DNS entry

        Args:
            record (string): DNS record the value needs to be extracted from
        Returns:
            Value: JSON object for the 'Value' attribute for the 'ChangeBatch' 
        """
        
	rec_type = record.rec_name

        if rec_type == 'a':
            value = record.address
        elif rec_type == 'txt':
            value = '\"{0}\"'.format(record.txtdata)
        elif rec_type == 'alias':
            value = record.alias
        elif rec_type == 'ptr':
            value = record.ptrdname
        elif rec_type == 'cname':
            value = record.cname
        elif rec_type == 'mx':
            value = "{0} {1}".format(record.preference, record.exchange)
        elif rec_type == 'srv':
            value = "{0} {1} {2} {3}".format(record.priority, record.weight, record.port, record.target)
        elif rec_type == 'spf':
            value = '\"{0}\"'.format(record.txtdata)
        else:
            value = None

        return { 'Value': value }


    def start_session(self):
        self.session = DynectSession(self.customer, self.username, self.password)

    
    def close_session(self):
        self.session.close_session()
