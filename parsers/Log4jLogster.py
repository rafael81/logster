###  Author: Mike Babineau <michael.babineau@gmail.com>, EA2D <http://ea2d.com>
###
###  A sample logster parser file that can be used to count the number
###  of events for each log level in a log4j log.
###
###  Example (note WARN,ERROR,FATAL is default):
###  sudo ./logster --output=stdout Log4jLogster /var/log/example_app/app.log --parser-options '-l WARN,ERROR,FATAL'
###
###
###  Logster copyright 2011, Etsy, Inc.
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

import time
import re
import optparse

from logster_helper import MetricObject, LogsterParser
from logster_helper import LogsterParsingException

class Log4jLogster(LogsterParser):
    
    def __init__(self, option_string=None):
        '''Initialize any data structures or variables needed for keeping track
        of the tasty bits we find in the log we are parsing.'''

        setattr(self, "metrics", dict())

        # Regular expression for matching lines we are interested in, and capturing
        # fields from the line (in this case, a log level such as timestamp, log_level, api, elapse_time).
        self.reg = re.compile('(?P<timestamp>[0-9-_:,\s\.]+) (?P<log_level>\w+) \[(?P<api>.+?java:\w+)\].+?\s== (?P<elapse_time>\d+$)')
        
    def parse_line(self, line):
        '''This function should digest the contents of one line at a time, updating
        object's state variables. Takes a single argument, the line to be parsed.'''
        
        try:
            # Apply regular expression to each line and extract interesting bits.
            regMatch = self.reg.match(line)
            
            if regMatch:
                print line
                linebits = regMatch.groupdict()
                api = linebits['api']
                elapse_time = linebits['elapse_time']
                timestamp = linebits['timestamp']

                if api in self.metrics.keys():
                    self.metrics[api].append({timestamp:elapse_time})
                else:
                    self.metrics[api] = list()
                    self.metrics[api].append({timestamp:elapse_time})
                                   
            else:
                raise LogsterParsingException, "regmatch failed to match"
                
        except Exception, e:
            raise LogsterParsingException, "regmatch or contents failed with %s" % e
            

    def get_state(self, duration):
        '''Run any necessary calculations on the data collected from the logs
        and return a list of metric objects.'''
        self.duration = duration
        
        metrics = [MetricObject(metric, elapse_time) for metric, elapse_time in self.metrics.iteritems()]
        return metrics