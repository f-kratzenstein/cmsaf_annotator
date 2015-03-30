#!/bin/sh

source ./CHARMeService.cfg

#setting the default values
CHARME_SERVER=${CHARME_NODE}
#fkratzen
OA_TOKEN=${CLIENT_ID}

#SERVICE:(search|suggest|advance_status)
SERVICE=search

#GRAPH:(submitted|retired|invalid)
GRAPH=submitted

#DOI_URI:   URI of the target DOI
#IDATA: input file
#ODATA: output file

#defining the exit codes
E_BADARGS=85

#overwriting the default values with the given arguements
for i in "$@"
do

case $i in
    -n=*|--node=*)
        CHARME_SERVER="${i#*=}"
        ;;
    -t=*|--token=*)
        OA_TOKEN="${i#*=}"
        ;;
    -u=*|--uri=*)
        DOI_URI="${i#*=}"
        ;;
    -s=*|--service=*)
        SERVICE="${i#*=}"
        ;;
    -g=*|--graph=*)
        GRAPH="${i#*=}"
        ;;
    -i=*|--input=*)
        IDATA="${i#*=}"
        ;;
    -o=*|--output=*)
        ODATA="${i#*=}"
        ;;
    -f=*|--format=*)
        FORMAT="${i#*=}"
        ;;
    *)
     echo "unknown arguement: ${i}"
esac

done

echo "run Service: ${SERVICE} on Graph:${GRAPH} @${CHARME_SERVER} as ${OA_TOKEN} for ${DOI_URI}"

if [ -z "${ODATA}" ];then
    echo "Error: missing arguement -o=|--output=: ${DOI_URI}"
    exit $E_BADARGS
fi


if [ "${SERVICE}" = "advance_status" ] || [ "${SERVICE}" = "insert/annotation" ]
then
    if [ -z "${IDATA}" ]
    then
        echo "Error: missing arguement -i=|--input=: ${IDATA}"
        exit $E_BADARGS
    fi

    if  [ -z "${FORMAT}" ]
    then
        echo "Error: missing or bad arguement -f=|--format=: ${FORMAT}"
        exit $E_BADARGS
    fi

    echo "do ${SERVICE}..."
    echo -X POST "${CHARME_SERVER}/${SERVICE}/" -d@${IDATA}  -H "Authorization: Token ${OA_TOKEN}"  -D ./tmp/header  -H "Content-Type: ${FORMAT}"
    curl -X POST "${CHARME_SERVER}/${SERVICE}/" -d@${IDATA}  -H "Authorization: Token ${OA_TOKEN}"  -D ./tmp/header  -H "Content-Type: ${FORMAT}" > ${ODATA}


else
    echo "do ${SERVICE}..."
    echo -X GET "${CHARME_SERVER}/${SERVICE}/atom?status=${GRAPH}&format=json-ld&q=*&target=${DOI_URI}&depth=1&count=25" -H "Authorization: Token ${OA_TOKEN}"
    curl -X GET "${CHARME_SERVER}/${SERVICE}/atom?status=${GRAPH}&format=json-ld&q=*&target=${DOI_URI}&depth=1&count=25" -H "Authorization: Token ${OA_TOKEN}" > ${ODATA}
fi

echo "...done!"

exit 0

