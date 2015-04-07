#!/bin/sh
WORK_DIR=~/Workspaces/DWD/CHARMe/WP6/WP6Git/cmsaf_annotator
cd ${WORK_DIR}/bin
./CHARMeService.sh   --service="insert/annotation" --input="../test/technical_report.ttl" --format="text/turtle" --output="../test/technical_report.ttl.log"