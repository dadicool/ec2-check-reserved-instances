ec2-check-reserved-instances
============================

EC2 Check Reserved Instances - Compare instance reservations with running instances

Amazon's reserved instances (ec2-describe-reserved-instances, ec2-describe-reserved-instances-offerings) are a great way to save money when using EC2. An EC2 instance reservation is specified by an availability zone, instance type, and quantity. Correlating the reservations you currently have active with your running instances is a manual, time-consuming, and error prone process.

This quick little Python script uses boto to inspect your reserved instances and running instances to determine if you currently have any reserved instances which are not being used. Additionally, it will give you a list of non-reserved instances which could benefit from additional reserved instance allocations.

To use the program, make sure you have boto installed. If you don't already have it, run:

    $ python setup.py install

The only configuration needed is your AWS keys. See [the boto docs](http://boto.readthedocs.org/en/latest/boto_config_tut.html) to learn how to configure your credentials.

EXAMPLE OUTPUT
===============

    $ ec2-check-reserved-instances --region eu-west-1
    
    UNUSED RESERVATION!	(1)	m3.large	linux	vpc	eu-west-1c
    UNUSED RESERVATION!	(4)	m1.medium	linux	vpc	eu-west-1c
    UNUSED RESERVATION!	(1)	m3.large	linux	vpc	eu-west-1a
    UNUSED RESERVATION!	(4)	m1.medium	linux	vpc	eu-west-1a
    UNUSED RESERVATION!	(2)	t2.small	linux	vpc	eu-west-1b
    UNUSED RESERVATION!	(1)	m4.large	linux	vpc	eu-west-1b
    UNUSED RESERVATION!	(1)	t2.medium	linux	vpc	eu-west-1a
    UNUSED RESERVATION!	(1)	t2.large	linux	vpc	eu-west-1b
    UNUSED RESERVATION!	(2)	m3.large	linux	vpc	eu-west-1b

    Instance not reserved:	(1)	t2.large	linux	vpc	eu-west-1c
    Instance not reserved:	(1)	m1.medium	linux	ec2	eu-west-1b
    Instance not reserved:	(4)	m1.medium	linux	ec2	eu-west-1c
    Instance not reserved:	(2)	m1.large	linux	ec2	eu-west-1b
    Instance not reserved:	(1)	m4.large	windows	vpc	eu-west-1b
    Instance not reserved:	(2)	c4.large	linux	vpc	eu-west-1a
    Instance not reserved:	(4)	m1.medium	linux	ec2	eu-west-1a
    Instance not reserved:	(1)	m1.large	linux	ec2	eu-west-1a
    Instance not reserved:	(1)	t2.large	linux	vpc	eu-west-1a
    Instance not reserved:	(1)	c1.medium	linux	ec2	eu-west-1c
    Instance not reserved:	(2)	t2.small	windows	vpc	eu-west-1b

    (39) running on-demand instances
    (36) reservations
    (17) unused reservations
