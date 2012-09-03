#!/bin/bash

instanceid=`/usr/bin/curl -s http://169.254.169.254/latest/meta-data/instance-id`
/usr/sbin/logster --dry-run --output=cloudwatch Log4jLogster log4j.log $instanceid
