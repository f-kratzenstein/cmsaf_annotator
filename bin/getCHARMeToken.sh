#!/bin/bash

usage(){
cat <<EOM
Usage of $(basename $0) :
   refreshing the Authentication token to connect to the CHARMe Node in the ./CHARMeService.cfg

   [*] -u=|--username=    registered user at the CHARMe Node configured in ./CHARMeService.cfg
   [*] -p=|--password=    password of the user

EOM
exit 0
}

source CHARMeService.cfg

charme_node=${CHARME_NODE}
client_id=${CMSAF_CLIENT_ID}

#overwriting the default values with the given arguements
for i in "$@"
do

case $i in
    -u=*|--username=*)
        username="${i#*=}"
        ;;
    -p=*|--password=*)
        password="${i#*=}"
        ;;
    -h|--help)
        usage
        ;;
    *)
     echo "unknown arguement: ${i}"
     usage
esac

done

if [ -z "${username}" ] || [ -z "${password}" ]; then
    echo "Error: missing arguement"
    usage
fi

mkdir ./tmp
cd ./tmp
rm cookies.txt header

echo "curl '${charme_node}/accounts/login/' -c cookies.txt -b cookies.txt > /dev/null"
curl "${charme_node}/accounts/login/" -c cookies.txt -b cookies.txt > /dev/null
export csrftoken=`grep csrftoken cookies.txt | awk '{print $7}'`;
echo "csrftoken: ${csrftoken}"
echo "curl -X POST '${charme_node}/accounts/login/' -c cookies.txt -b cookies.txt -d 'username=${username}&password=${password}&a=1&csrfmiddlewaretoken=$csrftoken'  -H 'Referer: ${charme_node}/accounts/login/' > /dev/null"
curl -X POST "${charme_node}/accounts/login/" -c cookies.txt -b cookies.txt -d "username=${username}&password=${password}&a=1&csrfmiddlewaretoken=$csrftoken"  -H "Referer: ${charme_node}/accounts/login/" > /dev/null
unset password

echo 'curl -X GET "${charme_node}/oauth2/authorize?client_id=${client_id}&response_type=token" -c cookies.txt -b cookies.txt -D header -L  > /dev/null'
curl -X GET "${charme_node}/oauth2/authorize?client_id=${client_id}&response_type=token" -c cookies.txt -b cookies.txt -D header -L  > /dev/null
access_token=`grep access_token header | cut -d'=' -f2 | cut -d'&' -f1`;
echo "oa_token: ${access_token} for charme_node: ${CHARME_NODE}"
sed -i -e "s/^TOKEN=[A-Za-z0-9]*$/TOKEN=${access_token}/" ../CHARMeService.cfg

expires_in=`grep expires_in header  | cut -d'=' -f4 | cut -d'&' -f1`
echo "expires in: ${expires_in}"

expires_at=$(date --date="${expires_in} second" +%s)
echo "expires_at: ${expires_at} | $(date --date="${expires_in} second" +%F)"
sed -i -e "s/^EXPIRES_AT=[0-9]*$/EXPIRES_AT=${expires_at}/" ../CHARMeService.cfg
cd ..

exit