__author__ = 'f-kratzenstein'

import logging
import sys
import getopt
import datetime
import subprocess
import glob
import uuid
import errno
import os

import libxml2
from rdflib import Graph
from rdflib import Namespace
from rdflib import URIRef,  Literal
from rdflib.namespace import RDF, DC


logging.basicConfig(format='[%(name)s].[%(levelname)s].[%(asctime)s]: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%Z', level=logging.INFO)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))

files2handle  =   "*.xml"
datacite_xsd_version = "2.2"

#List of directories to use
dirs        = dict()

#List of namespaces/prefixes we have to use
namespaces = {
    "charme":   "http://purl.org/spar/charme/",
    "cito"  :   "http://purl.org/spar/cito/",
    "cnt"   :   "http://www.w3.org/2011/content#" ,
    "dce"   :   "http://purl.org/dc/elements/1.1/",
    "dct"   :   "http://purl.org/dc/terms/",
    "dcmi"  :   "http://purl.org/dc/dcmitype/",
    "datacite"   :   "http://datacite.org/schema/kernel-{0}",
    "fabio" :   "http://purl.org/spar/fabio/",
    "foaf"  :   "http://purl.org/foaf/",
    "oa"    :   "http://www.w3.org/ns/oa#",
    "prov"  :   "http://www.w3.org/ns/prov#" ,
    "rdf"   :   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs"  :   "http://www.w3.org/2000/01/rdf-schema#",
    "skos"  :   "http://www.w3.org/2004/02/skos/core#",
    "xml"   :   "http://www.w3.org/XML/1998/namespace",
    "xsd"   :   "http://www.w3.org/2001/XMLSchema#",
}

#List of xpaths we need in order to retrieve the information of interest from the doi-xml-file
xpaths = {
    "cmsaf_doc"         :   '/datacite:resource/datacite:cmsaf_documentations/datacite:cmsaf_documentation',
    "doi_code"          :   'string(/datacite:resource/datacite:identifier[@identifierType="DOI"]/text())',
    "doi_type"          :   'string(//rdf:Description[@rdf:about="%s"]/rdf:type/@rdf:resource)',
    "@description"      :   'string(@description)',
    "@docTypeRdfUri"    :   'string(@docTypeRdfUri)',
}

#List of CHARMeService call parameter
service_config = {
    "service_file"  : "CHARMeService.sh" ,
    "service"       : "insert/annotation" ,
    "input"         : "" ,
    "format"        : "text/turtle",
    "output"        : "" ,
}

def setLogging(logLevel=logging.INFO):
    logger.setLevel(logLevel)

def get_timestamp():
    return "\"%s\"" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

#
#by using the rdflib
def xml2rdf(ifh, rdf_handles):
    """
    handling the doi-xml-file and writing the annotations into turtle-files
    """
    oa      = Namespace(namespaces["oa"])
    charme  = Namespace(namespaces["charme"])
    cito    = Namespace(namespaces["cito"])
    fabio   = Namespace(namespaces["fabio"])
    dcmi    = Namespace(namespaces["dcmi"])
    cnt     = Namespace(namespaces["cnt"])
    dce     = Namespace(namespaces["dce"])


    #get the xml handle
    res = libxml2.parseFile(ifh)
    xp = res.xpathNewContext()
    for namespace in namespaces:
         xp.xpathRegisterNs(namespace, namespaces[namespace])

    doi_uri = "http://dx.doi.org/%s" % xp.xpathEval(xpaths["doi_code"])
    logger.info("handle doi_uri: %s" % doi_uri)

    logger.debug("xmlns:".format(xp.xpathEval("/@xmlns")))

    cmsaf_docs = xp.xpathEval(xpaths["cmsaf_doc"])
    for doc in cmsaf_docs:
        try:
            ofh = open(os.path.join(dirs["n3_dir"],str(uuid.uuid1())+".ttl"),"w+")
        except IOError as e:
            logger.error ("I/O error({0}): {1}".format(e.errno, e.strerror))
            raise

        graph = Graph()

        citedEntity     = URIRef(doi_uri)
        citingEntity    = URIRef(doc.get_content().strip())

        logger.debug("create annotation as citation ...")
        #the OAnnotation
        subject = URIRef(charme.annoID)
        graph.add((subject, RDF.type, oa.Annotation))
        #graph.add((subject, RDF.type, cito.CitationAct))
        #the bodies
        graph.add((subject, oa.hasBody, charme.bodyID))
        graph.add((subject, oa.hasBody, citingEntity))
        #the target
        graph.add((subject, oa.hasTarget, citedEntity))
        #the motivation
        graph.add((subject, oa.motivatedBy, oa.describing))
        graph.add((subject, oa.motivatedBy, oa.linking))
        #the citation details
        #graph.add((subject, cito.hasCitingEntity, citingEntity))
        #graph.add((subject, cito.hasCitationCharacterization, cito.citesAsDatasource))
        #graph.add((subject, cito.hasCitedEntity, citedEntity))

        # creating the body
        subject = URIRef(charme.bodyID)
        graph.add((subject, RDF.type, cnt.ContentAsText))
        graph.add((subject, RDF.type, dcmi.Text))
        graph.add((subject, DC['format'], Literal('text/plain')))
        graph.add((subject, cnt.chars, Literal(doc.xpathEval(xpaths["@description"]))))

        #the citedEntityType
        subject=citedEntity
        graph.add((subject, RDF.type, dcmi.Dataset))

        #the citingEntity
        subject=citingEntity
        citingEntityType = URIRef(doc.xpathEval(xpaths["@docTypeRdfUri"]))
        if len(citingEntityType)==0:
            citingEntityType = fabio.JournalArticle
        graph.add((subject, RDF.type,citingEntityType))

        graph.bind("oa", oa)
        graph.bind("cito", cito)
        graph.bind("cnt", cnt)
        graph.bind("fabio",fabio)
        graph.bind("dc", DC)
        #graph.bind("charme", charme)

        logger.debug("graph: \n %s" % graph.serialize(format="turtle"))
        ofh.write(graph.serialize(format="turtle"))
        ofh.close()

        rdf_handles.append(ofh.name)

def init(working_directory):

    #init the path tree
    global dirs
    dirs["wrk_dir"]     = working_directory
    dirs["bin_dir"]     = os.path.join(dirs["wrk_dir"],"bin")
    dirs["doi_dir"]     = os.path.join(dirs["wrk_dir"],"doi")
    dirs["n3_dir"]      = os.path.join(dirs["doi_dir"],"n3")
    mkdir(dirs["n3_dir"])
    dirs["skos_dir"]    = os.path.join(dirs["wrk_dir"],"skos")
    logger.debug("dirs: %s" % dirs)
    service_config["service_file"] = os.path.join(dirs["bin_dir"],service_config["service_file"])



def curling(fh):
    """
    creating and executing a shell-script to transfer the annotations to the charme node
    """
    fh_curl = open(os.path.join(dirs["n3_dir"],"curling.sh"),"w+")
    fh_curl.write("#!/bin/sh \n")

    for ifh in fh:
        service_config["input"] = ifh
        logger.debug("ifh: %s <=> service_config[input]: %s" %(ifh,service_config["input"] ))
        fh_curl.write('\n%(service_file)s   --service="%(service)s" --input="%(input)s" --format="%(format)s" --output="%(input)s.log"' % service_config)
    fh_curl.close()
    logger.debug("fh_curl: %s" % fh_curl.name)

    # running the just created shell script
    subprocess.call(["chmod", "+x", fh_curl.name])
    status = subprocess.call([fh_curl.name])
    logger.debug("status: %s" % status)

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def usage():
    print "\nThis is the usage function\n"
    print 'Usage: '+sys.argv[0]+' -w -f -d -l -h'
    print '\t[*]\t-w|--working_dir\tbase directory of the charme_annotator containing the referenced subfolders like bin, doi , stage etc.; eg.".."'
    print '\t[*]\t-f|--files2handle\tname of a xml-file in the doi-folder which is to be processed, per default all *.xml in ${working_dir}/doi will be processed'
    print '\t[]\t-d|--datacite_version\tversion of the datacite-xml-schema; default 2.2'
    print '\t[]\t-l|--loglevel\t\tlogging level default=logging.INFO (DEBUG=10 INFO=20 WARN=30 ERROR=40 CRITICAL=50)'
    print '\t[]\t-h|--help\t\tdisplaying this usage info'


def main(arguements):

    logger.info("called module with arguements:  %s" % arguements)

    try:
        opts, args = getopt.getopt(arguements, "f:w:l:h:d:", [ "filter=","working_dir=","loglevel=","help=","datacite_version"])
        logger.debug("opts: %s" % opts)
        logger.debug("args: %s" % args)

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-w", "--working_dir"):
            logger.debug("--working_dir: %s" %arg)
            # initialize the base structure, references and global variables)
            init(arg)
        elif opt in ("-f", "--filter"):
            logger.debug("--filter: %s" %arg)
            files2handle = arg
        elif opt in ("-d", "--datacite_version"):
            logger.debug("--datacite_version: %s" %arg)
            global datacite_xsd_version
            datacite_xsd_version = arg
        elif opt in ("-l", "--loglevel"):
            logger.debug("--loglevel: %s" % arg)
            logger.setLevel(int(arg))

    namespaces["datacite"]=namespaces["datacite"].format(datacite_xsd_version)
    #getting the doi-xml-files we want to handle
    doi_xml_handles = glob.glob(dirs["doi_dir"]+"/"+files2handle)
    logger.debug ("doi files to handle: %s" % doi_xml_handles)

    #handling the doi-xml-files and writing the turtle-files
    rdf_handles = []
    for ifh in doi_xml_handles:
        xml2rdf (ifh, rdf_handles)

    #writing a shell script for transferring the turtle-files to the charme_node
    logger.debug ("annotation-file(s) to insert: %s" % rdf_handles)
    curling(rdf_handles)

if __name__ == '__main__':
    main(sys.argv[1:])


