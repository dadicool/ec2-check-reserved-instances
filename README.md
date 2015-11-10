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
    
    UNUSED RESERVATION!	(1)	m3.large	linux	eu-west-1a
    UNUSED RESERVATION!	(2)	m3.large	linux	eu-west-1b
    UNUSED RESERVATION!	(1)	t2.medium	linux	eu-west-1a
    UNUSED RESERVATION!	(1)	m4.large	linux	eu-west-1b
    UNUSED RESERVATION!	(1)	m3.large	linux	eu-west-1c
    UNUSED RESERVATION!	(1)	t2.large	linux	eu-west-1b
    UNUSED RESERVATION!	(2)	t2.small	linux	eu-west-1b

    Instance not reserved:	(2)	c4.large	linux	eu-west-1a
    Instance not reserved:	(1)	t2.large	linux	eu-west-1a
    Instance not reserved:	(1)	c1.medium	linux	eu-west-1c
    Instance not reserved:	(1)	m1.large	linux	eu-west-1a
    Instance not reserved:	(1)	m4.large	windows	eu-west-1b
    Instance not reserved:	(2)	t2.small	windows	eu-west-1b
    Instance not reserved:	(1)	m1.medium	linux	eu-west-1b
    Instance not reserved:	(1)	t2.large	linux	eu-west-1c
    Instance not reserved:	(2)	m1.large	linux	eu-west-1b

    (39) running on-demand instances
    (36) reservations
    (9) unused reservations

In this example, you can easily see that an m2.2xlarge was spun up in the wrong AZ (us-east-1b vs. us-east-1a), as well as an m1.small. The "Instance not reserved" section shows that you could benefit from reserving:

* (1) t1.micro
* (1) m1.small (not 2, since you'll likely want to move your us-east-1b small to us-east-1d)
* (3) m1.medium


TODO
====

- Add some sort of sorting, by Availability Zone/instance type
- Add VPC support
- Add option to use API to purchase the additional reservations (need to be EXTREMELY careful here, any mistake or miscommunication could cost quite a bit of money)
- Windows? Not taking Windows reserved instances into account
