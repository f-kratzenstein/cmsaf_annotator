#!/bin/sh

usage() {
cat <<EOM
   Usage of $(basename $0) :
   [] -n=|--node=     CHARMe Node to connect to (provided through ./CHARMeService.cfg)
   [] -t=|--token=    OA_TOKEN Authentication token to connect to the CHARMe Node  (provided through ./CHARMeService.cfg)
   [*] -u=|--uri=      URI of the DOI
   []  -s=|--service=  the service to call at CHARMe Node [search*|suggest|advance_status|insert/annoation]
   []  -g=|--graph=    the graph at the CHARMe Node to run the service against [submitted*|retired|invalid]
   []  -i=|--input=    filename with data for the services [advance_status|insert/annoation]
   [*]  -o=|--output=  filename to store the response of the server to
   []  -f=|--format=   encoding format of the input data

EOM
    exit 0
}

#reading the default values
source ./CHARMeService.cfg

#setting the default values
CHARME_SERVER=${CHARME_NODE}
#fkratzen
OA_TOKEN=${TOKEN}

#SERVICE:(search|suggest|advance_status)
SERVICE=search

#GRAPH:(submitted|retired|invalid)
GRAPH=submitted

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
    -h|--help)
        usage
        ;;
    *)
     echo "unknown arguement: ${i}"
     usage
esac

done

echo "run Service: ${SERVICE} on Graph:${GRAPH} @${CHARME_SERVER} as ${OA_TOKEN} for ${DOI_URI}"

if [ -z "${ODATA}" ];then
    echo "Error: missing arguement -o=|--output=: ${DOI_URI}"
    usage
    exit $E_BADARGS
fi


if [ "${SERVICE}" = "advance_status" ] || [ "${SERVICE}" = "insert/annotation" ]
then
    if [ -z "${IDATA}" ]
    then
        echo "Error: missing arguement -i=|--input=: ${IDATA}"
        usage
        exit $E_BADARGS
    fi

    if  [ -z "${FORMAT}" ]
    then
        echo "Error: missing or bad arguement -f=|--format=: ${FORMAT}"
        usage
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