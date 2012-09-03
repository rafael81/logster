#!/usr/bin/python

###
###  Copyright 2011, Etsy, Inc.
###
###  This file is part of Logster.
###  
###  Logster is free software: you can redistribute it and/or modify
###  it under the terms of the GNU General Public License as published by
###  the Free Software Foundation, either version 3 of the License, or
###  (at your option) any later version.
###  
###  Logster is distributed in the hope that it will be useful,
###  but WITHOUT ANY WARRANTY; without even the implied warranty of
###  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
###  GNU General Public License for more details.
###  
###  You should have received a copy of the GNU General Public License
###  along with Logster. If not, see <http://www.gnu.org/licenses/>.
###

import httplib2, sys, os, base64, hashlib, hmac
import json as simplejson

from urllib import urlencode, quote_plus
from time import time


class MetricObject(object):
    """General representation of a metric that can be used in many contexts"""
    def __init__(self, name, value, units='', type='float'):
        self.name = name
        self.value = value
        self.units = units
        self.type = type
        self.timestamp = int(time())

class LogsterParser(object):
    """Base class for logster parsers"""
    def parse_line(self, line):
        """Take a line and do any parsing we need to do. Required for parsers"""
        raise RuntimeError, "Implement me!"

    def get_state(self, duration):
        """Run any calculations needed and return list of metric objects"""
        raise RuntimeError, "Implement me!"


class LogsterParsingException(Exception):
    """Raise this exception if the parse_line function wants to
        throw a 'recoverable' exception - i.e. you want parsing
        to continue but want to skip this line and log a failure."""
    pass

class LockingError(Exception):
    """ Exception raised for errors creating or destroying lockfiles. """
    def __init__(self, message):
        self.message = message

class Log4jData:
    def __init__(self, metricName, timestamp, elapse_time):
      self.metricName = metricName
      self.timestamp = timestamp
      self.elapse_time = elapse_time

## taken from http://www.thatsgeeky.com/2012/01/autoscaling-with-custom-metrics/
class CloudWatch:
    def __init__(self, key, secret_key):
        self.key = os.getenv('AWS_ACCESS_KEY_ID', key)
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY_ID', secret_key)

    def setCloudWatchTimestamp(self, timestamp):
        return timestamp.replace(' ','T').split(',')[0] + '.000Z'

    def setParams(self, data):
        self.params = {'Namespace': 'Logstory',
       'MetricData.member.1.MetricName': data.metricName,
       'MetricData.member.1.Value': data.elapse_time,
       'MetricData.member.1.Unit': 'Milliseconds',
       'MetricData.member.1.Dimensions.member.1.Name': 'InstanceID',
       'MetricData.member.1.Dimensions.member.1.Value': instance_id}
     
    def getSignedURL(self, key, secret_key, action, data):
        # base url
        base_url = "monitoring.eu-west-1.amazonaws.com"
     
        # build the parameter dictionary
        url_params = self.params
        url_params['AWSAccessKeyId'] = key
        url_params['Action'] = action
        url_params['SignatureMethod'] = 'HmacSHA256'
        url_params['SignatureVersion'] = '2'
        url_params['Version'] = '2010-08-01'
        url_params['Timestamp'] = self.setCloudWatchTimestamp(data.timestamp)
     
        # sort and encode the parameters
        keys = url_params.keys()
        keys.sort()
        values = map(url_params.get, keys)
        url_string = urlencode(zip(keys,values))
     
        # sign, encode and quote the entire request string
        string_to_sign = "GET\n%s\n/\n%s" % (base_url, url_string)
        signature = hmac.new( key=secret_key, msg=string_to_sign, digestmod=hashlib.sha256).digest()
        signature = base64.encodestring(signature).strip()
        urlencoded_signature = quote_plus(signature)
        url_string += "&Signature=%s" % urlencoded_signature
     
        # do it
        foo = "http://%s/?%s" % (base_url, url_string)
        return foo
 
    def putData(self, data):
        self.setParams(data)
        signedURL = self.getSignedURL(self.key, self.secret_key, 'PutMetricData', data)
        h = httplib2.Http()
        resp, content = h.request(signedURL)
        print resp
        print content

