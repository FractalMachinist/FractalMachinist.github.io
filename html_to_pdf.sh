mkdir docs/pdf_sources;
cd docs/pdf_sources;

for job_name in *
do
	url="http://alex:32180/pdf_sources/$job_name/to_pdf.html";
	pdf_target="$job_name/Zach_Allen_Resume.pdf";
	echo "Converting '$url' to pdf @'$pdf_target'";
	google-chrome --headless --run-all-compositor-stages-before-draw --print-to-pdf="$pdf_target" "$url" && echo -e "Written\n";# && sleep 1;
	# sleep 1;
	# exit 1;
done
