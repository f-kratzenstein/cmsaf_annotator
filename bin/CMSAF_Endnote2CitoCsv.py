__author__ = 'f-kratzenstein'

import libxml2
import logging
import sys
import os
import getopt
import csv

logging.basicConfig(format='[%(name)s].[%(levelname)s].[%(asctime)s]: %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%Z',
                    level=logging.DEBUG)
logger = logging.getLogger(sys.argv[0].rpartition("/")[2].replace(".py",""))

#List of xpaths we need in order to retrieve the information of interest
xpaths = {
    "count"                     :   "count(/xml/records/record[electronic-resource-num]/titles)",
    "records"                   :   "/xml/records/record[electronic-resource-num]",
    "rec-number"                :   "rec-number",
    "CitingEntityTitle"         :   "titles/title",
    "CitingEntitySubTitle"      :   "titles/secondary-title",
    "CitingEntityType"          :   "ref-type/@name",
    "CitingEntity"              :   "electronic-resource-num",
    "CitedEntity"               :   "reviewed-item"
}

#Definition of the csv field names and order
csv_fields = ["CitingEntity",
              "CitationEvent",
              "CitedEntity",
              "Motivation",
              "CitingEntityTitle",
              "CitingEntitySubTitle"]

#a simple  cito2csv record-structure
endnote2cito_rec = {
    "CitingEntity"          :   "http://dx.doi.org/{0}",
    "CitedEntity"           :   "{0}",
    "CitationEvent"         :   "citeAsDatasource",
    "Motivation"            :   "linking",
    "CitingEntityTitle"     :   "{0}",
    "CitingEntitySubTitle"  :   "{0}"
}

#a simple list of cito2csv records
endnote2cito_arr = []


def parse(ifh):
    #parsing the input file and transferring the xml infos into the simple cito2csv record-structure
    #populating the list of cito2csv records
    res = libxml2.parseFile(ifh)
    xp = res.xpathNewContext()

    logger.debug("xpaths[count]: %s" % xp.xpathEval(xpaths["count"]))

    xrecords = xp.xpathEval(xpaths["records"])
    #use only the csv_fieldnames to populate the list of records
    fnames = set(xpaths.keys()).intersection(set(csv_fields))

    for xrecord in xrecords:
        #init record
        rec = endnote2cito_rec.copy()
        try:
            for fname in fnames:
                #populate the record by using the xpaths to retrieve the content of interest
                rec[fname] = rec[fname].format(xrecord.xpathEval(xpaths[fname])[0]\
                    .getContent().replace('\t','')\
                    .replace('  ','')\
                    .replace('\n',' ')\
                    .replace('http://dx.doi.org/','')\
                    .strip())
            endnote2cito_arr.append(rec)
        except IndexError:
            logger.error("failed on record with rec-number: %s"
                         % xrecord.xpathEval(xpaths["rec-number"])[0].getContent()
            )

    logger.debug("endnote2cito_arr: %s" % endnote2cito_arr)
    xp.xpathFreeContext()


def write2csv(ofh, recs):
    #writing out the list cito2csv records to a csv-file
    with open(ofh, "wb") as csvfile:
        citowriter = csv.DictWriter(csvfile,
                                    fieldnames=csv_fields,
                                    quoting=csv.QUOTE_ALL,
                                    delimiter=";",
                                    extrasaction="ignore")
        citowriter.writeheader()
        citowriter.writerows(recs)

def usage():
    print "\nThis is the usage function\n"
    print 'Usage: ' + sys.argv[0] + ' -i -o -l -h'
    print '[*]\t-i|--inputFile\t name/path of endNote.xml file to handle'
    print '[*]\t-o|--outputFile\t name/path of the csv-file to create '
    print '[]\t-l|--logLevel\t logging level default=10 DEBUG=10 INFO=20 WARN=30 ERROR=40 CRITICAL=50'
    print '[]\t-h|--help\tdisplaying this usage info'

def main(arguements):

    logging.info("called module with arguements:  %s" % arguements)

    try:
        opts, args = getopt.getopt(arguements, "i:o:l:h:", [ "inputFile=", "outputFile=", "logLevel=","help="])
        logger.debug("opts: %s" % opts)
        logger.debug("args: %s" % args)

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(1)
        elif opt in ("-i", "--inputFile"):
            logger.debug("--inputFile: %s" %arg)
            ifh=arg
        elif opt in ("-o", "--outputFile"):
            logger.debug("--outputFile: %s" %arg)
            ofh=arg
        elif opt in ("-l", "--logLevel"):
            logger.debug("--logLevel: %s" %arg)
            logger.setLevel(int(arg))

    logger.debug("%s exists: %s" % (ifh, os.path.isfile(ifh)))

    parse(ifh)
    write2csv(ofh, endnote2cito_arr)

if __name__ == '__main__':
    main(sys.argv[1:])