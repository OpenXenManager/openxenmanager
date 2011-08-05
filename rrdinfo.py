#!/usr/bin/python
#
# Example code for reading RRDs
# Contact: Jon Ludlam (jonathan.ludlam@eu.citrix.com)
#
# Mostly this script is taken from perfmon, by Alex Zeffert
#

import urllib
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import time

# Per VM dictionary (used by RRDUpdates to look up column numbers by variable names)
class VMReport(dict):
    """Used internally by RRDUpdates"""
    def __init__(self, uuid):
        self.uuid = uuid

# Per Host dictionary (used by RRDUpdates to look up column numbers by variable names)
class HostReport(dict):
    """Used internally by RRDUpdates"""
    def __init__(self, uuid):
        self.uuid = uuid

class RRDUpdates:
    """ Object used to get and parse the output the http://localhost/rrd_udpates?... 
    """
    def __init__(self, url):
        self.url = url 

    def get_nrows(self):
        return self.rows

    def get_vm_list(self):
        return self.vm_reports.keys()

    def get_vm_param_list(self, uuid):
        report = self.vm_reports[uuid]
        if not report:
            return []
        return report.keys()

    def get_vm_data(self, uuid, param, row):
        report = self.vm_reports[uuid]
        col = report[param]
        return self.__lookup_data(col, row)

    def get_host_uuid(self):
        report = self.host_report
        if not report:
            return None
        return report.uuid

    def get_host_param_list(self):
        report = self.host_report
        if not report:
            return []
        return report.keys()
        
    def get_host_data(self, param, row):
        report = self.host_report
        col = report[param]
        return self.__lookup_data(col, row)

    def get_row_time(self,row):
        return self.__lookup_timestamp(row)

    # extract float from value (<v>) node by col,row
    def __lookup_data(self, col, row):
        # Note: the <rows> nodes are in reverse chronological order, and comprise
        # a timestamp <t> node, followed by self.columns data <v> nodes
        if len(self.data_node.childNodes) >= (self.rows - 1 - row) and \
                len(self.data_node.childNodes[self.rows - 1 - row].childNodes) > (col+1):
            node = self.data_node.childNodes[self.rows - 1 - row].childNodes[col+1]
            return float(node.firstChild.toxml()) # node.firstChild should have nodeType TEXT_NODE
        return float(0)

    # extract int from value (<t>) node by row
    def __lookup_timestamp(self, row):
        # Note: the <rows> nodes are in reverse chronological order, and comprise
        # a timestamp <t> node, followed by self.columns data <v> nodes
        node = self.data_node.childNodes[self.rows - 1 - row].childNodes[0]
        return int(node.firstChild.toxml()) # node.firstChild should have nodeType TEXT_NODE

    def refresh(self):
        sock = urllib.URLopener().open(self.url)
        xmlsource = sock.read()
        #sock.close()
        xmldoc = minidom.parseString(xmlsource)
        self.__parse_xmldoc(xmldoc)
        # Update the time used on the next run

    def __parse_xmldoc(self, xmldoc):
        
        # The 1st node contains meta data (description of the data)
        # The 2nd node contains the data
        self.meta_node = xmldoc.firstChild.childNodes[0]
        self.data_node = xmldoc.firstChild.childNodes[1]

        def lookup_metadata_bytag(name):
            return int (self.meta_node.getElementsByTagName(name)[0].firstChild.toxml())

        # rows = number of samples per variable
        # columns = number of variables
        self.rows = lookup_metadata_bytag('rows')
        self.columns = lookup_metadata_bytag('columns')

        # These indicate the period covered by the data
        self.start_time = lookup_metadata_bytag('start')
        self.step_time  = lookup_metadata_bytag('step')
        self.end_time   = lookup_metadata_bytag('end')

        # the <legend> Node describes the variables
        self.legend = self.meta_node.getElementsByTagName('legend')[0]

        # vm_reports matches uuid to per VM report
        self.vm_reports = {}

        # There is just one host_report and its uuid should not change!
        self.host_report = None

        # Handle each column.  (I.e. each variable)
        for col in range(self.columns):
            self.__handle_col(col)

    def __handle_col(self, col):
        # work out how to interpret col from the legend
        col_meta_data = self.legend.childNodes[col].firstChild.toxml()

        # vm_or_host will be 'vm' or 'host'.  Note that the Control domain counts as a VM!
        (cf, vm_or_host, uuid, param) = col_meta_data.split(':')

        if vm_or_host == 'vm':
            # Create a report for this VM if it doesn't exist
            if uuid not in self.vm_reports:
                self.vm_reports[uuid] = VMReport(uuid)
    
            # Update the VMReport with the col data and meta data
            vm_report = self.vm_reports[uuid]
            vm_report[param] = col

        elif vm_or_host == 'host':
            # Create a report for the host if it doesn't exist
            if not self.host_report:
                self.host_report = HostReport(uuid)
            elif self.host_report.uuid != uuid:
                raise PerfMonException, "Host UUID changed: (was %s, is %s)" % (self.host_report.uuid, uuid)
            
            # Update the HostReport with the col data and meta data
            self.host_report[param] = col

        else:
            raise PerfMonException, "Invalid string in <legend>: %s" % col_meta_data


def main():

    rrd_updates = RRDUpdates() 

    rrd_updates.refresh({})

    for uuid in rrd_updates.get_vm_list():
        print "Got values for VM: "+uuid

        for param in rrd_updates.get_vm_param_list(uuid):
            print "param: "+param
            data=""
            for row in range(rrd_updates.get_nrows()):
                data=data+"(%d,%f) " % (rrd_updates.get_row_time(row),
                                        rrd_updates.get_vm_data(uuid,param,row))
            print data
            

#main()

