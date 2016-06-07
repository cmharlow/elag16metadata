#!/usr/bin/env python
import sys
from argparse import ArgumentParser
from lxml import etree
import re


class RepoInvestigatorException(Exception):
    """This is our base exception for this script."""

    def __init__(self, value):
        """Exception Object init.

        Returns exception value if exception occurs. Part of legacy metadata
        breakers script, not heavily used here.
        """
        self.value = value

    def __str__(self):
        """String value of exception.

        Returns exception value as string. Part of legacy metadata breakers
        script, not heavily used here.
        """
        return "%s" % (self.value,)


class Record:
    """Base class for nested metadata record in a DLXS export."""

    def __init__(self, elem, args):
        """Record XML init.

        Elem is the XML node that stands in for an item level 'record'. Args
        contains all the arguments passed.
        """
        self.elem = elem
        self.args = args

    def get_record_id(self):
        """Get Record Identifier."""
        try:
            record_id = self.elem.find("FILEDESC/PUBLICATIONSTMT/IDNO").text
            return record_id
        except:
            raise RepoInvestigatorException("Record does not have valid ID")

    def get_elements(self):
        """Get Element Values.

        If element argument is passed, get & return a list of
        values.
        """
        out = []
        for desc in self.elem.iterdescendants():
            if desc.tag == self.args.element and desc.text is not None:
                out.append(desc.text.encode("utf-8").strip())
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_xpath(self):
        """Get XPath Values.

        If XPath expression argument is passed, get & return a list of
        values.
        """
        out = []
        if self.elem.xpath(self.args.xpath) is not None:
            for value in self.elem.xpath(self.args.xpath):
                if value.text is not None:
                    out.append(value.text.encode("utf-8").strip())
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_stats(self):
        """Get Field Usage Statistics.

        When no arguments passed, this is run to get all possible fields
        containing text and generate field statistics from this.
        """
        stats = {}
        record = etree.ElementTree(self.elem)
        for desc in self.elem.iterdescendants():
            if len(desc) is 0 and desc.text is not None:
                # ignore empties, does NOT have children elements
                statskey = re.sub('\[\d+\]', '', record.getpath(desc))
                statskey = statskey.replace('/record/', '')
                stats.setdefault(statskey, 0)
                stats[statskey] += 1
        return stats

    def has_xpath(self):
        """Check if an XPath expression value exists.

        If the element (as XPath) and the present args are passed,
        this evaluates the XPath and returns true/false if not None.
        """
        present = False
        if self is not None:
            if self.elem.xpath(self.args.xpath) is not None:
                for value in self.elem.xpath(self.args.xpath):
                    if value.text is not None:
                        present = True
                        return present


def collect_stats(stats_agg, stats):
    """Collect field usage statistics.

    The following methods are all for taking a dictionary of field usage
    statistics and generate the overall assessment output.
    """
    # increment the record counter
    stats_agg["record_count"] += 1

    for field in stats:
        # get the total number of times a field occurs
        stats_agg["field_info"].setdefault(field, {"field_count": 0})
        stats_agg["field_info"][field]["field_count"] += 1

        # get average of all fields
        stats_agg["field_info"][field].setdefault("field_count_total", 0)
        stats_agg["field_info"][field]["field_count_total"] += stats[field]


def create_stats_averages(stats_agg):
    """Generate field averages for field usage statistics output."""
    for field in stats_agg["field_info"]:
        field_count = stats_agg["field_info"][field]["field_count"]
        field_count_total = stats_agg["field_info"][field]["field_count_total"]

        field_count_total_average = (float(field_count_total) /
                                     float(stats_agg["record_count"]))
        stats_agg["field_info"][field]["field_count_total_average"] = field_count_total_average

        field_count_element_average = (float(field_count_total) / float(field_count))
        stats_agg["field_info"][field]["field_count_element_average"] = field_count_element_average

    return stats_agg


def pretty_print_stats(stats_averages):
    """Print the field usage statistics and averages."""
    record_count = stats_averages["record_count"]
    # get header length
    element_length = 0
    for element in stats_averages["field_info"]:
        if element_length < len(element):
            element_length = len(element)

    print("\n\n")
    for element in sorted(stats_averages["field_info"]):
        percent = (stats_averages["field_info"][element]["field_count"] /
                   float(record_count)) * 100
        percentPrint = "=" * (int((percent) / 4))
        columnOne = " " * (element_length - len(element)) + element
        print("%s: |%-25s| %6s/%s | %3d%% " % (
                    columnOne,
                    percentPrint,
                    stats_averages["field_info"][element]["field_count"],
                    record_count,
                    percent
                ))


def main():
    """Main operation of script."""
    # start the field usage statistics dictionary that will be used later.
    stats_aggregate = {
        "record_count": 0,
        "field_info": {}
    }

    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("-x", "--xpath", dest="xpath",
                        help="get response of xpath expression on record")
    parser.add_argument("-i", "--id", action="store_true", dest="id",
                        default=False, help="prepend meta_id to line")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats",
                        default=False, help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true", dest="present",
                        default=False, help="print if element is in record")
    parser.add_argument("datafile", help="datafile you want analyzed")

    args = parser.parse_args()

    if not len(sys.argv) > 0:
        parser.print_help()
        exit()

    if args.xpath is None:
        args.stats = True

    s = 0
    for event, elem in etree.iterparse(args.datafile):
        if elem.tag == "record":
            r = Record(elem, args)
            record_id = r.get_record_id()

            if args.stats is False and args.present is False and args.xpath:
                if r.get_xpath() is not None:
                    for i in r.get_xpath():
                        if args.id:
                            print("\t".join([record_id, i]))
                        else:
                            print(i)

            if args.stats is False and args.xpath and args.present:
                print("%s %s" % (record_id, r.has_xpath()))

            if args.stats and args.xpath is None:
                if (s % 1000) == 0 and s != 0:
                    print("%d records processed" % s)
                s += 1
                collect_stats(stats_aggregate, r.get_stats())
            elem.clear()

    if args.stats and args.xpath is None:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
