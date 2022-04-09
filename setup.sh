rm forms_*;
rm pages.json*;
rm scripts.json_*;
echo "Deleted forms, scripts and pages old files"
cd datadir; 
rm crawl-data.sqlite ; 
rm forms.sqlite ;
echo "Deleted databases from previous runs"
