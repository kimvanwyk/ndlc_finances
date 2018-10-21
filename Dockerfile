FROM kimvanwyk/kppe

LABEL name=kimvanwyk/ndlc_finance_report
MAINTAINER kimvanwyk

USER root
RUN add-apt-repository -y ppa:deadsnakes/ppa \
&& apt-get update && apt-get -y install \
    python3.6 python3-pip \
&& apt-get autoremove \
&& rm -rf /var/lib/apt/lists/*

RUN rm /usr/bin/python3 \
&& ln -s /usr/bin/python3.6 /usr/bin/python3 \
&& chmod ugo+rwx /templates

USER appuser
COPY src/ /app
COPY report_requirements.txt /app
COPY exec.sh /app
WORKDIR /app

RUN pip3 install -r /app/report_requirements.txt

ENV LANG C.UTF-8

ENTRYPOINT ["/bin/bash", "/app/exec.sh"]
# , "python3.6", "kppe.py", "build", "--abbreviations-dir", "/abbreviations", "--templates-dir", "/templates", "--images-dir", "/images", "--ref-tags-dir", "/ref_tags", "no_frills_latex", "markup.txt;"date +%y%m%d
# ENTRYPOINT ["python3.6 build_report.py; python3.6 kppe.py build --abbreviations-dir /abbreviations --templates-dir /templates --images-dir /images --ref-tags-dir /ref_tags no_frills_latex markup.txt;"]
