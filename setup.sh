rm canary/forms/forms_*;
# rm canary/pages.json*;
rm canary/scripts.json_*;
echo "Deleted forms, scripts and pages old files"
rm log.txt;
echo "Deleted log file";
# rm error_sites*;
# echo "Deleted error sites file";
cd datadir; 
rm crawl-data.sqlite ; 
rm forms.sqlite ;
echo "Deleted databases from previous runs"
