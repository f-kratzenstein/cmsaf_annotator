#!/bin/bash
DOI_SERVER_URL="http://dx.doi.org/"
DOI_HANDLE=$1
OUTPUT=$2
#replace / with _
#RV=../stage/${DOI_HANDLE//\//_}.xml
echo "resolve doi: ${DOI_HANDLE} into ${RV}"
curl -LH "Accept: application/rdf+xml;q=1.0, application/citeproc+json;q=0.5" ${DOI_SERVER_URL}${DOI_HANDLE} > ${OUTPUT}
