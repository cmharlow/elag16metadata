import rdflib
import requests
from lxml import etree
import sys
from argparse import ArgumentParser

# create auth credentials value, using default settings for VM
authcred = requests.auth.HTTPBasicAuth('fedoraAdmin', 'secret3')

# create work
# curl -i -X POST -H "Content-Type: text/turtle" --data-binary "@../data/hunt_books.ttl" "http://localhost:8080/fcrepo/rest/digcoll/hunt_books.ttl"


def main():
    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("datafile", help="datafile you want analyzed")

    args = parser.parse_args()
    for event, elem in etree.iterparse(args.datafile):
        if elem.tag == "record":
            workgraph = rdflib.Graph()
            # record id
            record_id = elem.findtext("FILEDESC/PUBLICATIONSTMT/IDNO")
            record_uri = 

            # work properties
            creation_date = elem.findtext("FILEDESC/SOURCEDESC/BIBL/DATE")
            extent = elem.findtext("FILEDESC/SOURCEDESC/BIBL/NOTE")
            identifier = elem.findtext("FILEDESC/PUBLICATIONSTMT/IDNO")
            author = elem.findtext("FILEDESC/SOURCEDESC/BIBL/AUTHOR")
            place_of_pub = elem.findtext("FILEDESC/SOURCEDESC/BIBL/PUBPLACE")
            publisher = elem.findtext("FILEDESC/SOURCEDESC/BIBL/PUBLISHER")

            if elem.find("PROFILEDESC/TEXTCLASS/KEYWORDS/TERM") is not None:
                subjects = []
                subjxpath = elem.findall("PROFILEDESC/TEXTCLASS/KEYWORDS/TERM")
                for subj in subjxpath:
                    subjects.append(subj)

            if elem.find("FILEDESC/SOURCEDESC/BIBL/TITLE") is not None:
                title = elem.find("FILEDESC/SOURCEDESC/BIBL/TITLE").text

            # part and file properties
            parts = []
            for div in elem.iterfind("TEXT/BODY/DIV1"):
                divn = []
                for event2, elem2 in etree.iterwalk(div):
                    if elem2.tag == "HEAD":
                        part_title = elem2.findtext("HEAD")
                    else:
                        part_title = None
                    divn.append(part_title)

                    for pb in elem2.iterfind("PB"):
                        filen = []
                        part_number = pb.findtext("N")
                        filename = pb.findtext("REF")
                        resolution = pb.findtext("RES")
                        file_format = pb.findtext("FMT")
                        filen.append(part_number)
                        filen.append(filename)
                        filen.append(resolution)
                        filen.append(file_format)
                        divn.append(filen)
                parts.append(divn)

        # fileset properties
        if elem.find("ENCODINGDESC/EDITORIALDECL/P"):
            ocr_note = elem.find("ENCODINGDESC/EDITORIALDECL/P").text

        if elem.find("FILEDESC/PUBLICATIONSTMT/PUBLISHER"):
            dig_publisher = elem.find("FILEDESC/PUBLICATIONSTMT/PUBLISHER").text

        g.add()

if __name__ == '__main__':
    main()
