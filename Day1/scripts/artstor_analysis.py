# !/usr/bin/env python
import sys
from argparse import ArgumentParser
import json
import objectpath


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
    """Base class for an Artstor metadata record JSON Object."""

    def __init__(self, obj, args):
        """Object init.

        Object is the JSON property that stands in for an item level
        'record'. Args contains all the arguments passed.
        """
        self.obj = obj
        self.args = args

    def get_elements(self):
        """Get Element Values.

        If element (as objectPath) argument is passed, get & return a list of
        values.
        """
        out = []
        tree = objectpath.Tree(self.obj)
        resp = list(tree.execute('$..' + self.args.element))
        if resp and resp is not []:
            out = resp
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_stats(self):
        """Get Field Usage Staistics.

        When no arguments passed, this is run to get all possible fields
        containing text and generate field statistics from this.
        """
        stats = {}
        for field, value in self.obj.items():
            if isinstance(value, dict):
                for field2, value2 in value.items():
                    if isinstance(value2, dict):
                        for field3, value3 in value2.items():
                            if isinstance(value3, dict):
                                for field4, value4 in value3.items():
                                    if value4:
                                        stats.setdefault(field + "." + field2 +
                                                         "." + field3 + "." +
                                                         field4, 0)
                                        stats[field + "." + field2 + "." +
                                              field3 + "." + field4] += 1
                            else:
                                if value and value2 and value3:
                                    stats.setdefault(field + "." + field2 +
                                                     "." + field3, 0)
                                    stats[field + "." + field2 + "." + field3] += 1
                    else:
                        if value is not None and value2 is not None:
                            stats.setdefault(field + "." + field2, 0)
                            stats[field + "." + field2] += 1
            else:
                if value is not None:
                    stats.setdefault(field, 0)
                    stats[field] += 1
        return stats

    def has_element(self):
        """Check if an element is present.

        If the element (as objectpath) and the present args are passed,
        this evaluates the objectpath and returns true/false if not None.
        """
        present = False
        tree = objectpath.Tree(self.obj)
        resp = list(tree.execute('$..' + self.args.element))
        if resp:
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
    stats_agg = {
        "record_count": 0,
        "field_info": {}
    }

    # CLI arguments.
    parser = ArgumentParser(usage='%(prog)s [options] data_filename.json')
    parser.add_argument("-e", "--element", dest="element",
                        help="element to print to screen")
    parser.add_argument("-i", "--id", action="store_true", dest="id",
                        default=False, help="prepend meta_id to line")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats",
                        default=False, help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true",
                        dest="present", default=False,
                        help="print if there is value of element in record")
    parser.add_argument("datafile", help="datafile you want analyzed")

    args = parser.parse_args()

    if not len(sys.argv) > 0:
        parser.print_help()
        exit()

    if args.element is None:
        args.stats = True

    s = 0
    with open(args.datafile) as data:
        artstordata = json.load(data)

    for key, value in artstordata.items():
        record = Record(value, args)
        record_id = str(value['project_id']) + "_" + str(key)

        if args.stats is False and args.present is False:
            if record.get_elements() is not None:
                for i in record.get_elements():
                    if args.id:
                        if i:
                            print("\t" + record_id + str(i))
                    else:
                        if i:
                            print(str(i).encode('utf8'))

        if args.stats is False and args.present is True:
            print("%s %s" % (record_id, record.has_element()))

        if args.stats is True and args.element is None:
            if (s % 1000) == 0 and s != 0:
                print("%d records processed" % s)
            s += 1
            collect_stats(stats_agg, record.get_stats())

    if args.stats is True and args.element is None:
        stats_averages = create_stats_averages(stats_agg)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
