__author__ = 'fkratzen'

import csv
import logging
import sys
import getopt
import datetime
import subprocess
import errno

import os
from rdflib import Graph, URIRef,  Literal
from rdflib.namespace import Namespace, RDF, DC

import resolve_doi_xml


logging.basicConfig(format='[%(name)s].[%(levelname)s].[%(asctime)s]: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%Z', level=logging.INFO)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))

# some configurable properties
config_props = {
    "dialect" : "excel",
    "quotechar" : "\"",
    "delimiter" : "\t",
    "doi_org_prefix"  :"http://dx.doi.org/" ,
}

definedFieldNames = ["CitingEntity",
              "CitationEvent",
              "CitedEntity",
              "Motivation",
              "CitingEntityTitle",
              "CitingEntitySubTitle"
              ]

#List of namespaces/prefixes we have to use
namespaces = {
    "charme":       "http://purl.org/spar/charme/",
    "cito"  :       "http://purl.org/spar/cito/",
    "cnt"   :       "http://www.w3.org/2011/content#" ,
    "dce"   :       "http://purl.org/dc/elements/1.1/",
    "dct"   :       "http://purl.org/dc/terms/",
    "dcmi"  :       "http://purl.org/dc/dcmitype/",
    #"doi"   :       "http://datacite.org/schema/kernel-2.2",
    "fabio" :       "http://purl.org/spar/fabio/",
    "foaf"  :       "http://purl.org/foaf",
    "oa"    :       "http://www.w3.org/ns/oa#",
    "prov"  :       "http://www.w3.org/ns/prov#" ,
    "rdf"   :       "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs"  :       "http://www.w3.org/2000/01/rdf-schema#",
    "skos"  :       "http://www.w3.org/2004/02/skos/core#",
    "xml"   :       "http://www.w3.org/XML/1998/namespace",
    "xsd"   :       "http://www.w3.org/2001/XMLSchema#",
}

#List of CHARMeService call parameter
service_config = {
    "service_file"  : "CHARMeService.sh" ,
    "service"       : "insert/annotation" ,
    "input"         : "" ,
    "format"        : "text/turtle",
    "output"        : "" ,
}

def csv2ttl(ifh, delimiter=config_props["delimiter"]):
    """
    converting the csv into a turtle file

    Keywords arguements:

    ifh             --  file we want to convert
    delimiter       --  the delimiter used in the csv-file

    Keyword return:
    file_handles    --  handles of ttl-file we've created
    """

    with open(ifh, 'rb') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)

        reader = csv.DictReader(csvfile,
                                dialect=dialect,
                                delimiter=delimiter,
                                )
        #handles of ttl-file we'll create
        file_handles = []

        #just for readability when writing the turtle file
        oa      = Namespace(namespaces["oa"])
        charme  = Namespace(namespaces["charme"])
        cito    = Namespace(namespaces["cito"])
        fabio   = Namespace(namespaces["fabio"])
        dcmi    = Namespace(namespaces["dcmi"])
        cnt     = Namespace(namespaces["cnt"])

        #looping through the csv-file and transforming each row to an turtle-file
        next(reader)
        logger.debug("fieldnames: {0}".format(reader.fieldnames))

        for row in reader:
            try:
                logger.debug("row:{0}".format(row))
                if config_props["doi_org_prefix"] not in row["CitedEntity"] :
                    row["CitedEntity"] = "%s%s" % (config_props["doi_org_prefix"],row["CitedEntity"])

                stripped_doi = row["CitingEntity"].replace(config_props["doi_org_prefix"],"").replace("/","_")
                logger.debug("stripped doi: %s" % stripped_doi)
                #get the title of the doi
                citing_entity_xml = resolve_doi_xml.get_doi_xml(row["CitingEntity"].replace(config_props["doi_org_prefix"],""),
                                                                config_props["dir_stage"]
                                                                );

                citing_entity_title = resolve_doi_xml.getXPathValue(citing_entity_xml, "title")
                #citing_entity_title="some value as dx.doi.org is dead!"

                ofh = open(os.path.join(config_props["dir_data"],stripped_doi+".ttl"),"w+")

                logger.debug("create annotation as citation ...")
                graph = Graph()
                #the OAnnotation
                subject = URIRef(charme.annoID)
                logger.debug("subject: %s" % subject)
                graph.add((subject, RDF.type, oa.Annotation))
                graph.add((subject, RDF.type, cito.CitationAct))
                graph.add((subject, cito.hasCitationCharacterization, cito.citesAsDataSource))
                graph.add((subject, cito.hasCitedEntity, URIRef(row["CitedEntity"])))
                graph.add((subject, cito.hasCitingEntity, URIRef(row["CitingEntity"])))
                graph.add((subject, oa.motivatedBy, oa[row["Motivation"]]))
                graph.add((subject, oa.hasTarget, URIRef(row["CitedEntity"])))
                graph.add((subject, oa.hasBody, charme.bodyID))
                graph.add((subject, oa.hasBody, URIRef(row["CitingEntity"])))


                #creating the body
                subject = URIRef(charme.bodyID)
                graph.add((subject, RDF.type, cnt.ContentAsText))
                graph.add((subject, RDF.type, dcmi.Text))
                graph.add((subject, DC["format"], Literal("text/plain")))
                graph.add((subject, cnt["chars"], Literal(citing_entity_title)))

                #the citingEntityType
                subject=URIRef(row["CitingEntity"])
                graph.add((subject, RDF.type, fabio.JournalArticle))

                #the citedEntityType
                subject=URIRef(row["CitedEntity"])
                graph.add((subject, RDF.type, dcmi.Dataset))

                graph.bind("oa", oa)
                graph.bind("cito", cito)
                graph.bind("cnt", cnt)
                graph.bind("fabio",fabio)
                graph.bind("dc", DC)
                graph.bind("dcmi", dcmi)
                #graph.bind("charme", charme)

                logger.debug("graph: \n %s" % graph.serialize(format="turtle"))

                ofh.write(graph.serialize(format="turtle"))
                ofh.close()

                file_handles.append(ofh.name)

            except IOError as e:
                logger.error ("I/O error({0}): {1}".format(e.errno, e.strerror))
                raise

    return file_handles

def curling(fh):
    """
    creating a shell-script-file

    Keywords arguements:
    fh             --  file with an annotation to transfer to the charme node
    """

    #creating a shell-script-file
    fh_curl = open(os.path.join(config_props["dir_data"],"curling.sh"),"w+")
    fh_curl.write("#!/bin/sh \n")

    #writing the shell-script-commands for each *.ttl in the file_handles
    for f in fh:
        service_config["input"] = f
        logging.debug("ifh: %s <=> service_config[input]: %s" %(f,service_config["input"] ))
        fh_curl.write('\n%(service_file)s   '
                      '--service="%(service)s" '
                      '--input="%(input)s" '
                      '--format="%(format)s" '
                      '--output="%(input)s.log"'
                      % service_config
        )

    fh_curl.close()
    logger.debug("fh_curl: %s" % fh_curl.name)

    #running the just created shell script
    subprocess.call(["chmod", "+x", fh_curl.name])
    status = subprocess.call([fh_curl.name])
    logger.debug("status: %s" % status)

def get_timestamp():
    return "\"%s\"" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def init(working_directory):
    """
    initializing the base structure and the configuration properties
    """
    config_props["dir_wrk"] = working_directory
    config_props["dir_data"]  = os.path.join(config_props["dir_wrk"],"data/n3")
    mkdir(config_props["dir_data"])

    config_props["dir_stage"] = os.path.join(config_props["dir_wrk"],"stage")
    mkdir(config_props["dir_stage"])

    config_props["dir_bin"]  = os.path.join(config_props["dir_wrk"],"bin")
    service_config["service_file"] = os.path.join(config_props["dir_bin"],service_config["service_file"])

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def setConfigProperty(prop, val):
    """
    setting a config property
    """
    config_props[prop] = val

def usage():
    print "\nThis is the usage function\n"
    print 'Usage: ' + sys.argv[0] + ' i <--inputFile1> -w <--workingDir> -d <--delimiter> -l <--loglevel>'
    print "\t[*]\t-i|--inputFile\tname of the  inputFile, must be a csv-file,"
    print "\t\t\t\twith at least columns CitingEntity, CitedEntity, Motivation"
    print '\t[*]\t-w|--working_dir\tbase directory of the charme_annotator containing the referenced subfolders like bin, stage, data,  ...'
    print '\t[*]\t-d|--delimiter\tthe character used as a field-delimiter in the inputFile'
    print '\t []\t-l|--logLevel\tlogging level default=10 DEBUG=10 INFO=20 WARN=30 ERROR=40 CRITICAL=50'

def main(arguements):

    logging.info("called module with arguements:  %s" % arguements)

    try:
        opts, args = getopt.getopt(arguements, "i:w:d:l:h:", [ "inputFile=","workingDir=","delimiter=", "logLevel=", "help"])
        logger.debug("opts: %s" % opts)
        logger.debug("args: %s" % args)

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-w", "--workingDir"):
            logger.debug("--workingDir: %s" % arg)
            # initialize the base structure, references and global variables)S
            init(arg)
        elif opt in ("-i", "--inputFile"):
            logger.debug("--inputFile: %s" % arg)
            ifh=arg
        elif opt in ("-d", "--delimiter"):
            logger.debug("--delimiter: %s" % arg)
            setConfigProperty("delimiter", arg)
        elif opt in ("-l", "--logLevel"):
            logger.debug("--logLevel: %s" %arg)
            logger.setLevel(int(arg))

    logger.info("%s exists: %s" % (ifh, os.path.isfile(ifh)))
    logging.debug("config_props: %s" % config_props)

    if (os.path.isfile(ifh)):
        file_handles = csv2ttl(ifh, config_props["delimiter"])
        logger.debug ("annotation-file(s) to insert: %s" % file_handles)
        #writing a shell script for transferring the turtle-files to the charme_node
        curling(file_handles)
    else :
        logger.warn("failed to run due to missing inputFile: %s" % ifh)

if __name__ == '__main__':
    main(sys.argv[1:])