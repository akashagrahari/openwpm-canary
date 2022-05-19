rm forms_*;
rm pages.json*;
rm scripts.json_*;
echo "Deleted forms, scripts and pages old files"
rm log.txt;
echo "Deleted log file";
# rm error_sites*;
# echo "Deleted error sites file";
cd datadir; 
rm crawl-data.sqlite ; 
rm forms.sqlite ;
echo "Deleted databases from previous runs"
