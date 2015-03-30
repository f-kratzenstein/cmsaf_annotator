#!/bin/sh 
curl -H 'Accept: application/sparql-results+xml' --data-urlencode 'query@./data/1425399185.sparql' https://charme-test.cems.rl.ac.uk/sparql > ./data/1425399185_result.xml