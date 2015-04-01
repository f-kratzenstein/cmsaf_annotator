__author__ = 'fkratzen'

import logging
import sys
import getopt
import subprocess
import shutil

import rdflib
import rdflib.plugins.sparql as sparql
import os
import libxml2
import libxslt


logging.basicConfig(format='[%(name)s].[%(levelname)s].[%(asctime)s]: %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%Z',
                    level=logging.DEBUG)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))


configs = {
    "cmsaf.wui.doi.dir" :   "/cmsaf/cmsaf-ops2/CMSAF_QM/png/doi",
    "xpath.cmsaf_doc"   :   "/datacite:resource/datacite:cmsaf_documentations/datacite:cmsaf_documentation",
    "charme.local.vocab":   "../skos/CHARMe_vocab.xml",
    "charme.doi.dir"    :   "../doi",
    "charme.doi.xslt"   :   "../doi/xslt/cmsaf_doi2html.xsl",
    "charme.uri.vocab"  :   'https://charme.cems.rl.ac.uk/vocab',
    "sparql.query"      :   """
                            select distinct ?s ?o
                            where {
                            ?s ?p0 ?o .
                            }
                            """,
    "sparql.binding.prefLabel"  : rdflib.URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"),
    # "sparql.binding.rdfLabel"   : rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
    "sparql.binding.rdfLabel": rdflib.URIRef("http://www.w3.org/2004/02/skos/core#notation"),
}

#List of namespaces/prefixes we have to use
namespaces = {
    "datacite"   :   "http://datacite.org/schema/kernel-{0}",
    "xsl": "http://www.w3.org/1999/XSL/Transform",
    "default": "http://www.w3.org/1999/xhtml",

}

datacite_xsd_version = 3

def setLogging(logLevel=logging.INFO):
    logger.setLevel(int(logLevel))

def curl(skos):
    """
    download the vocabulary/skos

    Keywords arguements:
    skos    --  uri of the remote skos to download
    """
    fh_curl = open("curl_charme_vocab.sh", "w+")
    fh_curl.write("#!/bin/sh \n")
    fh_curl.write("curl -X GET '%s' -H 'Accept: application/rdf+xml' > %s " % (configs["charme.uri.vocab"], skos))
    fh_curl.close()
    logger.debug("fh_curl: %s" % fh_curl.name)
    subprocess.call(["chmod", "+x", fh_curl.name])

    if os.path.isfile(fh_curl.name):
        status = subprocess.call(["./%s" % fh_curl.name])

    else :
        status = -1

    logger.debug("status: %s" % status)
    return status


def initGraph(skos = configs["charme.local.vocab"]):
    """
    initialize the rdf-graph we need to use

    Keywords arguements:

    skos        --  filename of the rdf-graph we want to use
    """

    if not os.path.isfile(skos):
        #download the skos
        curl(skos)

    graph = rdflib.Graph()
    graph.parse(skos)
    logger.debug("charme_vocab: %s \n" % graph.serialize())

    return graph

def initFileHandle(ifh):
    """
    copies the inputFile to the doi-folder

    Keywords arguements:

    ifh        --  file we want to copy
    """

    shutil.copy(ifh,configs["charme.doi.dir"])
    fh = os.path.join(configs["charme.doi.dir"],os.path.basename(ifh))

    if os.path.isfile(fh):
        return fh
    else :
        logger.error("failed to copy inputFile %s to local dir %s!" % (ifh,configs["charme.doi.dir"]))
        sys.exit(2)


def queryGraph(g, q , b):
    """querying the graph by using a sparql query statement.

    Keyword arguments:
    g -- the graph to query
    q -- the sparql query to run against the graph
    b -- bindings to use

    Keyword return:
    rdf resultset of the query
    """
    pq = sparql.prepareQuery(q)
    rdf = g.query(q, initBindings = b)
    return rdf


def findMatchingUri(graph, descr):
    """finding the matching uri in the graph for a given description
    Keyword arguements:

    graph   -- graph hosting the skos to search in
    descr   -- a cmsaf_documentation@description to match with

    Keyword return:
    matching label as string
    """

    rv=""
    rdf = queryGraph(graph, configs["sparql.query"], {'p0' : configs["sparql.binding.prefLabel"]} )
    #loop through the preferredLabels
    for triplet in rdf:
        if descr.find(str(triplet[1])) < 0:
            continue
        else:
            logger.debug("matched label: %s with @id: %s" % (triplet[1], triplet[0]))
            rv = triplet[0]
            break

    if len(rv) == 0:
        logger.debug("run extra loop")
        lrs = queryGraph(graph, configs["sparql.query"], {'p0' : configs["sparql.binding.rdfLabel"]} )

        #loop through the other labels
        for lr in lrs:
            if descr.find(str(lr[1])) < 0:
                continue
            else:
                logger.debug("matched label: %s with @id: %s" % (lr[1], lr[0]))
                rv = lr[0]
                break

    return rv

def addDocTypeRdfUriAttr(ifh, graph):
    """editing the doi.xml by adding a docTypeRdfUri attribute
    Keyword arguements:

    ifh     -- the cmsaf_doi.xml file to be edited
    graph   -- skos with referring labels

    Keyword return:
    """

    res = libxml2.parseFile(ifh)
    logger.debug("xml-content: %s \n" % res.serialize())

    xp = res.xpathNewContext()
    for namespace in namespaces:
        xp.xpathRegisterNs(namespace, namespaces[namespace])

    cmsaf_docs = xp.xpathEval(configs["xpath.cmsaf_doc"])

    for doc in cmsaf_docs:
        descr = doc.xpathEval("string(@description)")
        logger.debug("attribute(description): %s" % descr)

        doc.setProp("docTypeRdfUri", findMatchingUri(graph,descr))

    logger.debug("xml-content modified: %s \n" % res.serialize())

    fh = open(ifh,"w+")
    fh.write(res.serialize())

def transform(doi_xml, xslt):
    logger.debug("running the xslt ....")
    rfh = doi_xml.replace('.xml','.html')

    styleSheet = libxml2.parseFile(xslt)
    styleSheet.getRootElement().newNs(namespaces["datacite"], "datacite")

    style = libxslt.parseStylesheetDoc(styleSheet)

    doc = libxml2.parseFile(doi_xml)
    result = style.applyStylesheet(doc, None)
    style.saveResultToFilename(rfh, result, 0)
    style.freeStylesheet()
    doc.freeDoc()
    result.freeDoc()

    return rfh

def usage():
  print "\nThis is the usage function\n"
  print 'Usage: ' + sys.argv[0] + ' -i -l -h -d'
  print '\t[*]\t-i|--inputFile\ta cmsaf_wui_doi.xml file to be processed/transformed '
  print '\t[]\t-d|--datacite_version\tversion of the datacite-xml-schema; default 3'
  print '\t[]\t-l|--loglevel\tlogging level default=logging.INFO (DEBUG=10 INFO=20 WARN=30 ERROR=40 CRITICAL=50)'
  print '\t[]\t-h|--help\tdisplaying this usage info'

def main(args):

    logger.debug("called module with arguements:  %s" % args)
    try:
        opts, args = getopt.getopt(args, "i:d:l:h:", ["inputFile=", "datacite_version", "loglevel=", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit(1)
            elif opt in ("-i", "--inputFile"):
                logger.debug("--inputFile: %s" %arg)
                ifh= arg
            elif opt in ("-d", "--datacite_version"):
                logger.debug("--datacite_version: %s" % arg)
                global datacite_xsd_version
                datacite_xsd_version = arg
            elif opt in ("-l", "--loglevel"):
                logger.debug("--loglevel: %s" %arg)
                logger.setLevel(int(arg))

    namespaces["datacite"]=namespaces["datacite"].format(datacite_xsd_version)

    if (ifh ==""):
        logger.warn("missing input param: inputFile")
        usage()
        sys.exit(2)

    if os.path.isfile(ifh):

        fh = initFileHandle(ifh)
        graph = initGraph()
        addDocTypeRdfUriAttr(fh,graph)
        transform(fh, configs["charme.doi.xslt"])

    else :
        logger.warn("missing input: inputFile")
        usage()
        sys.exit(2)

    logger.debug("basename: %s" % os.path.basename(ifh))

if __name__ == '__main__':
    main(sys.argv[1:])
