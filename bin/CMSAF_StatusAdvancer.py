__author__ = 'f-kratzenstein'

import sys
import logging
import os
import getopt
import subprocess
import errno

import libxml2


logging.basicConfig(format='[%(levelname)s].[%(asctime)s]: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%Z', level=logging.DEBUG)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))

#List of namespace we need to register in order to parse and query the atom feed
namespaces = {
    "atom": "http://www.w3.org/2005/Atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/"
}

#List of xpaths we need in order to retrieve the information of interest from the atom feed
xpaths = {
    "annotation_id": "/atom:feed/atom:entry/atom:id/text()"
}

#List of CHARMeService call parameter
service_config = {
    "service_file"  : "CHARMeService.sh" ,
    "service"       : "advance_status" ,
    "input"         : "" ,
    "format"        : "application/json+ld",
    "output"        : "" ,
}

#template for the command
template_json = "{\"annotation\" : \"%s\" , \"toState\" : \"%s\"} \n"

#List of directories to use
dirs        = dict()

#List of json file to push to the server
file_handles = []


def xml2json(ifh, toState):
    logger.debug("xml2json(%s)..." % ifh)
    res = libxml2.parseFile(ifh)
    xp = res.xpathNewContext()

    for namespace in namespaces:
        xp.xpathRegisterNs(namespace, namespaces[namespace])

    logger.debug("xpaths[annotation_id]: %s" % xpaths["annotation_id"])
    annotations = xp.xpathEval(xpaths["annotation_id"])

    for annotation_id in annotations:
        logger.debug("annotation: %s" % annotation_id.__str__().rpartition("/")[2]);
        json = open(os.path.join(dirs["stage_dir"], ("advance_status_%s.json" %  annotation_id.__str__().rpartition("/")[2])), "w+")

        logger.debug("write to: %s" % json.name)
        json.write(template_json % (annotation_id.__str__(), toState ))
        json.close()
        file_handles.append(json.name)

def curling(fh):
    fh_curl = open(os.path.join(dirs["stage_dir"],"curling.sh"),"w+")
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

def init(arg):
    #global dirs
    dirs["wrk_dir"]     = arg
    dirs["bin_dir"]     = os.path.join(dirs["wrk_dir"],"bin")
    dirs["stage_dir"]     = os.path.join(dirs["wrk_dir"],"stage")
    mkdir(dirs["stage_dir"])
    logger.debug("dirs: %s" % dirs)
    service_config["service_file"] = os.path.join(dirs["bin_dir"],service_config["service_file"])

def usage():
    print "\nThis is the usage function\n"
    print 'Usage: ' + sys.argv[0] + '-w <--working-dir> -i <--inputFile1> -s <--toState>'
    print "\n\t[*]\t-i|--inputFile\t\tname of the resides in the preconfigured stage_dir"
    print "\t\t\t\t\tthe inputFile must be a CHARMe AtomFeed.xml, which <entry><id>-tags defines the annotations to advance"
    print '\t[*]\t-w|--working_dir\tbase directory of the charme_annotator containing the referenced subfolders like bin, doi ...'
    print '\t[*]\t-s|--toState\t\tthe status to advance the annotation(s) to (submitted|stable|invalid|retired)'
    print '\t[]\t-l|--logLevel\t\tlogger.level default=10 (DEBUG=10 INFO=20 WARN=30 ERROR=40 CRITICAL=50)'
    print '\t[]\t-h|--help\t\tdisplaying this usage info'


def main(arguements):

    logger.debug("called module with arguements:  %s" % arguements)

    try:
        opts, args = getopt.getopt(arguements, "w:i:s:l:h:", ["working_dir=", "inputFile=", "toState=", "logLevel","help"])
        logger.debug("opts: %s" % opts)
        logger.debug("args: %s" % args)

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--inputFile"):
            logger.debug("--inputFile: %s" % arg)
            inputFile = arg
        elif opt in ("-w", "--working_dir"):
            init(arg)
        elif opt in ("-s", "--toState"):
            logger.debug("--toState: %s" % arg)
            toState = arg
        elif opt in ("-l", "--logLevel"):
            logger.debug("--logLevel: %s" %arg)
            logger.setLevel(int(arg))
            
    file_handle = os.path.join(dirs["stage_dir"], inputFile)

    #creating the json-files
    xml2json(file_handle, toState)

    logger.debug ("annotation-file(s) to insert: %s" % file_handles)
    #writing a shell script for transferring the json-files to the charme_node
    curling(file_handles)

if __name__ == '__main__':
    main(sys.argv[1:])
