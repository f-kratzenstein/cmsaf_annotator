import logging
import sys
import os
import getopt
import subprocess

import datetime
import time

import libxml2
import libxslt

import webbrowser

logging.basicConfig(format='[%(name)s].[%(levelname)s].[%(asctime)s]: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%Z', level=logging.INFO)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))

configs = {
    "tokenizer"         : ";",
    "assigner"          : "=",
    "timestamp"         : time.mktime(datetime.datetime.now().timetuple()).__trunc__(),
    "charme_uri"        : "https://charme-test.cems.rl.ac.uk/sparql",
    "xslt.overview"     : "./tmpl/charme_sparql_overview.xsl",
    "dir.output"        : "./data",
    "dir.templates"     : "./tmpl"
}

#list of available params in the sparql query templates with their default values;
params = {
    "timestamp_from" : (datetime.datetime.now() - datetime.timedelta(28)).isoformat() ,
    "timestamp_until" :(datetime.datetime.now() - datetime.timedelta(0)).isoformat() ,
}

xslt_params = {
    "timestamp_from" : "'{0}'".format(params["timestamp_from"]),
    "timestamp_until" :  "'{0}'".format(params["timestamp_until"]),
}

status = 0
#setting the logging level
def setLogging(logLevel=logging.INFO):
   logger.setLevel(logLevel)
   logger.debug("logLevel set to {0}".format(logLevel))

def setParams(p) :
    global params
    for pair in p.split(configs["tokenizer"]):
        token = pair.split(configs["assigner"])
        params[token[0]] =  (datetime.datetime.now() - datetime.timedelta(int(token[1]))).isoformat()

    logger.info("params set to: %s" % params)

#adressing the sparql query
def finegrain_query(filename, parameters):
    s=open(filename).read()
    f=open("{0}/{1}.sparql".format(configs["dir.output"],configs["timestamp"]), 'w')

    for k,v in parameters.items():
        if "&{0};".format(k)  in s:
                logger.debug("Changing &{0}; to {1}!".format(k,v))
                s=s.replace("&{0};".format(k), v)

        else:
                logger.debug ("No occurances of {0} found.".format(k))
    f.write(s)
    f.flush()
    f.close()
    return f

def curl(queryFile):
    global status
    rfh = "{0}/{1}_result.xml".format(configs["dir.output"], configs["timestamp"])

    fh_curl = open("curl_charme_sparql.sh", "w+")
    fh_curl.write("#!/bin/sh \n")
    fh_curl.write("curl -H 'Accept: application/sparql-results+xml' --data-urlencode 'query@{0}' {1} > {2}".format(
        queryFile.name,configs["charme_uri"],rfh
    ))
    fh_curl.close()
    logger.debug("fh_curl: {0}".format(fh_curl.name))
    subprocess.call(["chmod", "+x", fh_curl.name])

    if os.path.isfile(fh_curl.name):
        status = subprocess.call(["./{0}".format(fh_curl.name)])

    else :
        status = -1

    logger.info("status: {0}".format(status))
    return rfh

def transform(resultFile,styleSheet):
    logger.debug("running the xslt ....")
    rfh =  rfh = "{0}/{1}_result.html".format(configs["dir.output"], configs["timestamp"])

    styleSheet = libxml2.parseFile(configs["xslt.overview"])
    style = libxslt.parseStylesheetDoc(styleSheet)

    doc = libxml2.parseFile(resultFile)
    #result = style.applyStylesheet(doc, None)
    result = style.applyStylesheet(doc, xslt_params)
    style.saveResultToFilename(rfh, result, 0)
    style.freeStylesheet()
    doc.freeDoc()
    result.freeDoc()

    return rfh

def display(htmlFile):
    logger.debug("try to open {0} with firefox...".format(htmlFile))
    try:

        #controller = webbrowser.get('w3w')
        #controller.open(htmlFile)
        webbrowser.open(htmlFile)
    except webbrowser.Error:
        logger.error( "it seems no webbrowser available, please try to open {0} manually.".format(htmlFile))
    except:
        raise


def usage():
  print "\nThis is the usage function\n"
  print 'Usage: '+sys.argv[0]+' -q -p -h'
  print '\n '
  print '[*]\t-q|--queryTemplate\tsparql template file containing the constraints to run the query e.g. ./tmpl/charme_sparql_overview'
  print '[]\t-p|--params\t\tstring with param=value; e.g. "timestamp_from=int;timestamp_until=int"'
  print '\t\t\t\twith timestamp_until < timestamp_from as the timestamp is calculated as datetime.now() - int(days)'
  print '[]\t-l|--loglevel\t\tlogging level default=logging.INFO (DEBUG=10 INFO=20 WARN=30 ERROR=40 CRITICAL=50)'
  print '\n '
  print 'e.g. pyhthon CHARMeSparqler.py -q ./tmpl/charme_sparql_overview -p "timestamp_from=21;timestamp_until=0"'

def main(args):

    logger.info("called module with arguements:  %s" % args)

    try:
        opts, args = getopt.getopt(args, "q: p: l:", [ "queryTemplate=","params=","loglevel="])
        logger.debug("opts: %s" % opts)
        logger.debug("args: %s" % args)

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                sys.exit(1)
            elif opt in ("-q", "--queryTemplate"):
                logger.debug("--queryTemplate: %s" %arg)
                ifh= arg
            elif opt in ("-p", "--params"):
                logger.debug("--params: %s" %arg)
                setParams(arg)
            elif opt in ("-l", "--loglevel"):
                logger.debug("--logLevel: %s" %arg)
                logger.setLevel(int(arg))

        if (ifh ==""):
            logger.warn("missing input param: inputFile")
            usage()
            sys.exit(2)

        qfh = finegrain_query(ifh,params)
        rfh = curl(qfh)
        logger.info("sparql query result file: {0}".format(rfh))

        ofh = transform(rfh,configs["xslt.overview"])
        logger.info("xslt transformation result file: {0}".format(ofh))

        display(ofh)

    except getopt.GetoptError:
        usage()
        sys.exit(2)

if __name__ == '__main__':
    main(sys.argv[1:])

