import rdflib
import requests
from lxml import etree
import sys
from argparse import ArgumentParser

base = "http://fedoraAdmin:secret3@localhost:8080/fcrepo/rest/digcoll"
auth = requests.auth.HTTPBasicAuth('fedoraAdmin', 'secret3')
updatehead = {"Content-Type": "application/sparql-update"}

def main():
    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("datafile", help="datafile to go to fedora")

    args = parser.parse_args()
    for event, elem in etree.iterparse(args.datafile):
        if elem.tag == "record":
            # record id
            record_id = elem.findtext("FILEDESC/PUBLICATIONSTMT/IDNO")
            # create fedora object for work
            resp = requests.post(base, headers={'Slug', record_id})
            record_uri = resp.text
            # work properties
            creation_date = elem.findtext("FILEDESC/SOURCEDESC/BIBL/DATE")
            extent = elem.findtext("FILEDESC/SOURCEDESC/BIBL/NOTE")
            identifier = elem.findtext("FILEDESC/PUBLICATIONSTMT/IDNO")
            author = elem.findtext("FILEDESC/SOURCEDESC/BIBL/AUTHOR")
            place_of_pub = elem.findtext("FILEDESC/SOURCEDESC/BIBL/PUBPLACE")
            publisher = elem.findtext("FILEDESC/SOURCEDESC/BIBL/PUBLISHER")
            subjects = elem.findtext("PROFILEDESC/TEXTCLASS/KEYWORDS/TERM")
            title = elem.findtext("FILEDESC/SOURCEDESC/BIBL/TITLE")
            # add PCDM relationship
            req_body = """PREFIX pcdm: <http://pcdm.org/models#> INSERT { <> pcdm:hasMember """ + record_uri + """ . }"""
            requests.patch(base, data=req_body, headers=updatehead)
            # add work metadata
            update_body = """PREFIX pcdm: <http://pcdm.org/models#>
dc: <http://purl.org/dc/elements/1.1/>
dct: <http://purl.org/dc/terms/>
marcrel: <http://id.loc.gov/vocabulary/relators/>
vivo: <http://vivoweb.org/ontology/core#>
INSERT { <> dct:created """ + creation_date + """ ;
            dc:format """ + extent + """ ;
            dct:format """ + identifier + """ ;
            marcrel:author """ + author + """ ;
            vivo:placeOfPublication """ + place_of_pub + """ ;
            dct:publisher """ + publisher + """ ;
            dct:title """ + title + """ ;
}"""
            requests.patch(record_uri, data=update_body, headers=updatehead, auth=auth)

            # part and file properties
            divnum = 0
            for div in elem.iterfind("TEXT/BODY/DIV1"):
                divnum += 1
                # create fedora object for work
                part_id = record_id + "_" + divnum
                resp = requests.post(record_uri, headers={'Slug', part_id}, auth=auth)
                part_uri = resp.text
                req_body = """PREFIX pcdm: <http://pcdm.org/models#> INSERT { <> pcdm:hasMember """ + part_uri + """ . }"""
                requests.patch(record_uri, data=req_body, headers=updatehead, auth=auth)
                for event2, elem2 in etree.iterwalk(div):
                    part_title = elem2.findtext("HEAD")
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
