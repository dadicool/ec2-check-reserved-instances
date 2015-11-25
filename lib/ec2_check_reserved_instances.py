#!/usr/bin/python

import sys
import os
import boto
import boto.ec2
import boto.rds2
import boto.redshift
import logging
from pprint import pformat,pprint
import argparse

def main():
	parser = argparse.ArgumentParser(description='Cross reference existing ec2 reservations to current instances.')
	parser.add_argument('--log', default="WARN", help='Change log level (default: WARN)')
	parser.add_argument('--region', default='us-east-1', help='AWS Region to connect to')
	parser.add_argument('--service', default='ec2', help='Comma-separated list of AWS Services to check (ec2,rds, etc)')
	parser.add_argument('--include-reserved-instance-ids', default=False, help='Flag to include Reserved Instance Ids in Unused instance report')

	args = parser.parse_args()
	services = args.service.split(",")

	if u'ec2' in services :
		logging.basicConfig(level=getattr(logging,args.log))
		logger = logging.getLogger('ec2-check')
		# Dump some environment details
		logger.debug("boto version = %s", boto.__version__)
	
		ec2_conn = boto.ec2.connect_to_region(args.region)
		ec2_instances = ec2_conn.get_only_instances()
	
		running_ec2_instances = {}
		for instance in ec2_instances:
			if instance.state != "running":
				logger.debug("Disqualifying instance %s: not running\n" % ( instance.id ) )
			elif instance.spot_instance_request_id:
				logger.debug("Disqualifying instance %s: spot\n" % ( instance.id ) )
			else:
				az = instance.placement
				instance_type = instance.instance_type
				logger.debug("Running instance: %s"% (instance.__dict__))
				if not instance.vpc_id :
					location = u'ec2'
				else:
					location = u'vpc'
				platform = instance.platform
				if not platform:
					platform = u'linux'
				running_ec2_instances[ (instance_type, az, platform, location ) ] = running_ec2_instances.get( (instance_type, az, platform, location ) , 0 ) + 1
	
	
		logger.debug("FOO -- Running instances: %s"% pformat(running_ec2_instances))
	
		ec2_reserved_instances = {}
		ec2_reserved_instances_ids = {}
		for reserved_instance in ec2_conn.get_all_reserved_instances():
			if reserved_instance.state != "active":
				logger.debug( "Excluding reserved instances %s: no longer active\n" % ( reserved_instance.id ) )
			else:
				az = reserved_instance.availability_zone
				instance_type = reserved_instance.instance_type
				logger.debug("Reserved instance: %s"% (reserved_instance.__dict__))
				description = reserved_instance.description
				if "Windows" in description:
					platform = u'windows'
				else:
					platform = u'linux'
				if "VPC" in description:
					location = u'vpc'
				else:
					location = u'ec2'
				instance_signature = ( instance_type, az, platform, location)
				ec2_reserved_instances[instance_signature] = ec2_reserved_instances.get ( instance_signature, 0 )  + reserved_instance.instance_count
				if instance_signature not in ec2_reserved_instances_ids :
					#print "Resetting instance_signature: (%s)" % (instance_signature)
					ec2_reserved_instances_ids[instance_signature] = []
				logger.debug("inserting reserved_instance_id (%s) into list (%s)" % (instance_signature, ec2_reserved_instances_ids[instance_signature]))
				ec2_reserved_instances_ids[instance_signature].append(reserved_instance.id)
	
		logger.debug("Reserved instances: %s"% pformat(ec2_reserved_instances))
		
		print "\nEC2 Checks"
		print "=========="
	
		# this dict will have a positive number if there are unused reservations
		# and negative number if an instance is on demand
		instance_diff = dict([(x, ec2_reserved_instances[x] - running_ec2_instances.get(x, 0 )) for x in ec2_reserved_instances])
	
		# instance_diff only has the keys that were present in ec2_reserved_instances. There's probably a cooler way to add a filtered dict here
		for placement_key in running_ec2_instances:
			if not placement_key in ec2_reserved_instances:
				instance_diff[placement_key] = -running_ec2_instances[placement_key]
	
		logger.debug('Instance diff: %s'% pformat(instance_diff))
	
		unused_ec2_reservations = dict((key,value) for key, value in instance_diff.iteritems() if value > 0)
		if unused_ec2_reservations == {}:
			print "Congratulations, you have no unused ec2 reservations"
		else:
			for unused_reservation in unused_ec2_reservations:
				print "UNUSED RESERVATION!\t(%s)\t%s\t%s\t%s\t%s" % ( unused_ec2_reservations[ unused_reservation ], unused_reservation[0],unused_reservation[2],unused_reservation[3], unused_reservation[1] )
				instance_signature = ( unused_reservation[0], unused_reservation[1], unused_reservation[2], unused_reservation[3])
				if args.include_reserved_instance_ids:
					for id in ec2_reserved_instances_ids[instance_signature]:
						print "\tReserved Instance ID : %s" % (id)

		unreserved_instances = dict((key,-value) for key, value in instance_diff.iteritems() if value < 0)
		if unreserved_instances == {}:
			print "Congratulations, you have no unreserved instances"
		else:
			for unreserved_instance in unreserved_instances:
				print "Instance not reserved:\t(%s)\t%s\t%s\t%s\t%s" % ( unreserved_instances[ unreserved_instance ], unreserved_instance[0], unreserved_instance[2], unreserved_instance[3], unreserved_instance[1] )
	
		if len(unused_ec2_reservations.values()) != 0:
			qty_unused_ec2_reservations = reduce( lambda x, y: x+y, unused_ec2_reservations.values())
		else:
			qty_unused_ec2_reservations = 0
	
		if len(running_ec2_instances.values()) != 0:
			qty_running_ec2_instances = reduce( lambda x, y: x+y, running_ec2_instances.values())
		else:
			qty_running_ec2_instances = 0
		
		if len(ec2_reserved_instances.values()) != 0:
			qty_ec2_reserved_instances = reduce( lambda x, y: x+y, ec2_reserved_instances.values())
		else:
			qty_ec2_reserved_instances = 0
	
		print "\n(%s) running on-demand instances\n(%s) ec2 reservations\n(%s) unused ec2 reservations" % ( qty_running_ec2_instances, qty_ec2_reserved_instances,qty_unused_ec2_reservations )
	else :
		print "Skipping EC2 checks\n"

	if u'rds' in services :
		logging.basicConfig(level=getattr(logging,args.log))
		logger = logging.getLogger('rds-check')
	
		rds_conn = boto.rds2.connect_to_region(args.region)
		rds_instances = rds_conn.describe_db_instances()[u'DescribeDBInstancesResponse'][u'DescribeDBInstancesResult'][u'DBInstances']
		logger.debug("rds instances %s\n" % ( rds_instances ) )
	
		running_rds_instances = {}
		for instance in rds_instances:
			if instance[u'DBInstanceStatus'] != u'available':
				logger.debug("Disqualifying instance %s: not running\n" % ( instance[u'DBInstanceIdentifier'] ) )
			else:
				instance_type = instance[u'DBInstanceClass']
				engine = instance[u'Engine']
				multiAZ = instance[u'MultiAZ']
				logger.debug("Running instance: %s"% (instance))
				instance_signature = (instance_type, engine, multiAZ)
				running_rds_instances[ instance_signature ] = running_rds_instances.get( instance_signature , 0 ) + 1
	
	
		logger.debug("FOO -- Running instances: %s"% pformat(running_rds_instances))
	
		reserved_rds_instances = {}
		reserved_rds_instances_ids = {}
		logger.debug("FOO -- instances %s\n" % ( rds_conn.describe_reserved_db_instances() ) )
		for reserved_instance in rds_conn.describe_reserved_db_instances()[u'DescribeReservedDBInstancesResponse'][u'DescribeReservedDBInstancesResult'][u'ReservedDBInstances'] :
			if reserved_instance[u'State'] != "active":
				logger.debug( "Excluding reserved instances %s: no longer active\n" % ( reserved_instance[u'ReservedDBInstanceId'] ) )
			else:
				instance_type = reserved_instance[u'DBInstanceClass']
				engine = reserved_instance[u'ProductDescription']
				if engine == u'postgresql':
					engine = 'postgres'
				multiAZ = reserved_instance[u'MultiAZ']
				instance_signature = (instance_type, engine, multiAZ)
				reserved_rds_instances[instance_signature] = reserved_rds_instances.get ( instance_signature, 0 )  + reserved_instance[u'DBInstanceCount']
				if instance_signature not in reserved_rds_instances_ids :
					#print "Resetting instance_signature: (%s)" % (instance_signature)
					reserved_rds_instances_ids[instance_signature] = []
				logger.debug("inserting reserved_instance_id (%s) into list (%s)" % (instance_signature, reserved_rds_instances_ids[instance_signature]))
				reserved_rds_instances_ids[instance_signature].append(reserved_instance[u'ReservedDBInstanceId'])
	
		logger.debug("Reserved instances: %s"% pformat(reserved_rds_instances))
	
		print "\nRDS Checks"
		print "=========="
		
		# this dict will have a positive number if there are unused reservations
		# and negative number if an instance is on demand
		instance_diff = dict([(x, reserved_rds_instances[x] - running_rds_instances.get(x, 0 )) for x in reserved_rds_instances])
	
		# instance_diff only has the keys that were present in reserved_rds_instances. There's probably a cooler way to add a filtered dict here
		for placement_key in running_rds_instances:
			if not placement_key in reserved_rds_instances:
				instance_diff[placement_key] = -running_rds_instances[placement_key]
	
		logger.debug('Instance diff: %s'% pformat(instance_diff))
	
		unused_rds_reservations = dict((key,value) for key, value in instance_diff.iteritems() if value > 0)
		if unused_rds_reservations == {}:
			print "Congratulations, you have no unused ec2 reservations"
		else:
			for unused_reservation in unused_rds_reservations:
				print "UNUSED RESERVATION!\t(%s)\t%s\t%s\t%s" % ( unused_rds_reservations[ unused_reservation ], unused_reservation[0],unused_reservation[1],unused_reservation[2] )
				instance_signature = ( unused_reservation[0], unused_reservation[1], unused_reservation[2])
				if args.include_reserved_instance_ids:
					for id in reserved_rds_instances_ids[instance_signature]:
						print "\tReserved Instance ID : %s" % (id)

		unreserved_rds_instances = dict((key,-value) for key, value in instance_diff.iteritems() if value < 0)
		if unreserved_rds_instances == {}:
			print "Congratulations, you have no unreserved instances"
		else:
			for unreserved_rds_instance in unreserved_rds_instances:
				print "Instance not reserved:\t(%s)\t%s\t%s\t%s" % ( unreserved_rds_instances[ unreserved_rds_instance ], unreserved_rds_instance[0], unreserved_rds_instance[1], unreserved_rds_instance[2] )
	
		if len(unused_rds_reservations.values()) != 0:
			qty_unused_rds_reservations = reduce( lambda x, y: x+y, unused_rds_reservations.values())
		else:
			qty_unused_rds_reservations = 0
	
		if len(running_rds_instances.values()) != 0:
			qty_running_rds_instances = reduce( lambda x, y: x+y, running_rds_instances.values())
		else:
			qty_running_rds_instances = 0
		
		if len(reserved_rds_instances.values()) != 0:
			qty_reserved_rds_instances = reduce( lambda x, y: x+y, reserved_rds_instances.values())
		else:
			qty_reserved_rds_instances = 0
	
		print "\n(%s) running on-demand instances\n(%s) rds reservations\n(%s) unused rds reservations" % ( qty_running_rds_instances, qty_reserved_rds_instances,qty_unused_rds_reservations )
	else :
		print "Skipping RDS checks\n"

	if u'redshift' in services :
		logging.basicConfig(level=getattr(logging,args.log))
		logger = logging.getLogger('redshift-check')
	
		redshift_conn = boto.redshift.connect_to_region(args.region)
		redshift_instances = redshift_conn.describe_clusters()[u'DescribeClustersResponse'][u'DescribeClustersResult'][u'Clusters']
		logger.debug("Redshift clusters %s\n" % ( redshift_instances ) )
	
		running_redshift_instances = {}
		for instance in redshift_instances:
			if instance[u'ClusterStatus'] != u'available':
				logger.debug("Disqualifying cluster %s: not running\n" % ( instance[u'ClusterIdentifier'] ) )
			else:
				instance_type = instance[u'NodeType']
				instance_qty = instance[u'NumberOfNodes']
				instance_signature = (instance_type)
				running_redshift_instances[ instance_signature ] = running_redshift_instances.get( instance_signature , 0 ) + instance_qty
	
	
		logger.debug("Running nodes: %s"% pformat(running_redshift_instances))
	
		reserved_redshift_instances = {}
		reserved_redshift_instances_ids = {}
		logger.debug("Redshift reserved nodes %s\n" % ( redshift_conn.describe_reserved_nodes() ) )
		
		for reserved_instance in redshift_conn.describe_reserved_nodes()[u'DescribeReservedNodesResponse'][u'DescribeReservedNodesResult'][u'ReservedNodes'] :
			if reserved_instance[u'State'] != "active":
				logger.debug( "Excluding reserved nodes %s: no longer active\n" % ( reserved_instance[u'ReservedNodeId'] ) )
			else:
				instance_type = reserved_instance[u'NodeType']
				instance_qty = reserved_instance[u'NodeCount']
				instance_signature = (instance_type)
				reserved_redshift_instances[instance_signature] = reserved_redshift_instances.get ( instance_signature, 0 )  + instance_qty
				if instance_signature not in reserved_redshift_instances_ids :
					#print "Resetting instance_signature: (%s)" % (instance_signature)
					reserved_redshift_instances_ids[instance_signature] = []
				logger.debug("inserting reserved_instance_id (%s) into list (%s)" % (instance_signature, reserved_redshift_instances_ids[instance_signature]))
				reserved_redshift_instances_ids[instance_signature].append(reserved_instance[u'ReservedNodeId'])
	
		logger.debug("Reserved node: %s"% pformat(reserved_redshift_instances))
	
		print "\Redshift Checks"
		print "=========="
		
		# this dict will have a positive number if there are unused reservations
		# and negative number if an instance is on demand
		instance_diff = dict([(x, reserved_redshift_instances[x] - running_redshift_instances.get(x, 0 )) for x in reserved_redshift_instances])
	
		# instance_diff only has the keys that were present in reserved_redshift_instances. There's probably a cooler way to add a filtered dict here
		for placement_key in running_redshift_instances:
			if not placement_key in reserved_redshift_instances:
				instance_diff[placement_key] = -running_redshift_instances[placement_key]
	
		logger.debug('Redshift Instance diff: %s'% pformat(instance_diff))
	
		unused_redshift_reservations = dict((key,value) for key, value in instance_diff.iteritems() if value > 0)
		if unused_redshift_reservations == {}:
			print "Congratulations, you have no unused redshift reservations"
		else:
			for unused_reservation in unused_redshift_reservations:
				print "UNUSED RESERVATION!\t(%s)\t%s" % ( unused_redshift_reservations[ unused_reservation ], unused_reservation[0] )
				instance_signature = ( unused_reservation[0])
				if args.include_reserved_instance_ids:
					for id in reserved_redshift_instances_ids[instance_signature]:
						print "\tReserved Nodes ID : %s" % (id)

		unreserved_redshift_instances = dict((key,-value) for key, value in instance_diff.iteritems() if value < 0)
		if unreserved_redshift_instances == {}:
			print "Congratulations, you have no unreserved nodes"
		else:
			for unreserved_redshift_instance in unreserved_redshift_instances:
				print "Instance not reserved:\t(%s)\t%s" % ( unreserved_redshift_instances[ unreserved_redshift_instance ], unreserved_redshift_instance[0] )
	
		if len(unused_redshift_reservations.values()) != 0:
			qty_unused_redshift_reservations = reduce( lambda x, y: x+y, unused_redshift_reservations.values())
		else:
			qty_unused_redshift_reservations = 0
	
		if len(running_redshift_instances.values()) != 0:
			qty_running_redshift_instances = reduce( lambda x, y: x+y, running_redshift_instances.values())
		else:
			qty_running_redshift_instances = 0
		
		if len(reserved_redshift_instances.values()) != 0:
			qty_reserved_redshift_instances = reduce( lambda x, y: x+y, reserved_redshift_instances.values())
		else:
			qty_reserved_redshift_instances = 0
	
		print "\n(%s) running on-demand instances\n(%s) redshift reservations\n(%s) unused redshift reservations" % ( qty_running_redshift_instances, qty_reserved_redshift_instances,qty_unused_redshift_reservations )
	else :
		print "Skipping Redshift checks\n"
