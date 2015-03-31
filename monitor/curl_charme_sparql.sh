#!/bin/sh 
curl -H 'Accept: application/sparql-results+xml' --data-urlencode 'query@../monitor/data/1427796488.sparql' https://charme.cems.rl.ac.uk/sparql > ../monitor/data/1427796488_result.xml