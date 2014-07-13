if [ "$1" ]
then
	F=$1
else
	F=*/*.pdf
	rm -rf csv svg
fi

mkdir -p csv svg
for i in $F; do echo $i; time python scraper.py $i >$(echo $i |sed s/pdf/csv/g); done


