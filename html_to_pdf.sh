mkdir -p docs/pdf_sources;
cd docs/pdf_sources;

for job_path in */Zach_Allen_Resume.html;
do
	job_name=$(dirname "$job_path");
	url="http://alex:32180/pdf_sources/$job_path";
	pdf_target="$job_name/Zach_Allen_Resume.pdf";
	echo "Converting '$url' to pdf @'$pdf_target'";
	google-chrome --headless --run-all-compositor-stages-before-draw --print-to-pdf="$pdf_target" "$url" && echo -e "Written";
	echo "";
done


# echo "Converting 'http://alex:32180/pdf_sources/index.html' to pdf @'index.pdf'";
# google-chrome --headless --run-all-compositor-stages-before-draw --print-to-pdf="index.pdf" "http://alex:32180/pdf_sources/index.html" && echo -e "Written";
# echo "";
