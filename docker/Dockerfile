FROM registry.dpi.inpe.br/brazildatacube/geo:0.2

ADD . /app

WORKDIR /app

RUN pip3 install pip --upgrade && \
    pip install wheel openpyxl xmltodict statsmodels sklearn && \
    pip install -e .[tests,docs]
