__author__ = 'f-kratzenstein'


import libxml2
import logging
import sys
import os
import getopt
import subprocess

logging.basicConfig(format='[%(levelname)s].[%(asctime)s]: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%Z', level=logging.DEBUG)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))

#List of directories we want to use
dirs = {
    "data_dir"  : "/home/f-kratzenstein/Workspaces/DWD/CHARMe/WP6/WP610/bitbucket/cmsaf-annotator/stage"
}

#List of namespace we need to register in order to parse and query the atom feed
namespaces = {
    "rdf"   :   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "bibo"  :   "http://purl.org/ontology/bibo/",
    "foaf"  :   "http://xmlns.com/foaf/0.1/",
    "owl"   :   "http://www.w3.org/2002/07/owl#",
    "dc"    :   "http://purl.org/dc/terms/",
    "prism" :   "http://prismstandard.org/namespaces/basic/2.1/"
}

#List of xpaths we need in order to retrieve the information of interest
xpaths = {
    "title" :   "/rdf:RDF/rdf:Description/dc:title/text()",
    "endingPage":  "//prism:endingPage",
    "about" :   "/rdf:RDF/rdf:Description/@rdf:about",
    "test"  :   "/RDF/Description/title/text()"
}


def get_doi_xml(doi):
    logging.debug("get_doi_xml for: %s" % doi)
    doi_xml = "../stage/%s.xml" % doi.replace("/","_")
    status = subprocess.call(["./resolve_doi.sh", doi, doi_xml])
    logging.debug("status: %s" % status)

    return doi_xml

def getXPathValue(ifh, xpath):
    logging.debug("get_from %s xpath: %s" % (ifh, xpaths[xpath]))
    res = libxml2.parseFile(ifh)
    xp = res.xpathNewContext()

    for namespace in namespaces:
         xp.xpathRegisterNs(namespace, namespaces[namespace])

    doi_value = xp.xpathEval(xpaths["title"])

    if doi_value.__len__()>0:
        rv = doi_value[0].__str__()

    else:
       rv = "uups, no value found !"
    logging.debug("doi value: %s" % rv)

    return rv

def parse(ifh):
    res = libxml2.parseFile(ifh)
    xp = res.xpathNewContext()

    for namespace in namespaces:
         xp.xpathRegisterNs(namespace, namespaces[namespace])

    logging.debug("xpaths[title]: %s" % xpaths["title"])
    doi_title = xp.xpathEval(xpaths["title"])

    if doi_title.__len__()>0:
        logging.debug("doi title: %s" % doi_title[0].__str__())
    else:
        logging.warn("uups, no title found !")

    logging.debug("xpaths[about]: %s" % xpaths["about"])
    doi_uri = xp.xpathEval(xpaths["about"])

    if doi_uri.__len__()>0:
        logging.debug("doi_about title: %s" % doi_uri[0].__str__())
    else:
        logging.warn("uups, no uri found !")

    xp.xpathFreeContext()


def main(arguements):

    logging.debug("called module with arguements:  %s" % arguements)
    logging.debug("data_dir: %s" % dirs["data_dir"])

    try:
        opts, args = getopt.getopt(arguements, "i:", [ "inputDOI="])
        logging.debug("opts: %s" % opts)
        logging.debug("args: %s" % args)

    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            sys.exit(1)
        elif opt in ("-i", "--inputDOI"):
            logging.debug("--inputDOI: %s" %arg)
            # initialize
            global doi
            doi=arg

    #file_handle = os.path.join(dirs["data_dir"],inputFile)
    logging.debug("handle doi : %s" % doi)
    doix = get_doi_xml(doi)
    logging.debug("doix: %s" % doix)
    logging.debug("doi title: %s" % getXPathValue(doix,"title"))

    #parse(file_handle)

if __name__ == '__main__':
    main(sys.argv[1:])