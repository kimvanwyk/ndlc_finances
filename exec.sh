cd /app
python3.6 build_report.py &&
python3.6 kppe.py build --abbreviations-dir /abbreviations --templates-dir /app/templates --images-dir /images --ref-tags-dir /ref_tags no_frills_latex markup.txt &&
rm -rf /app/markup.txt &&
mv -f /app/markup.pdf /io/`date +%y%m%d`_ndlc_finance_report.pdf
