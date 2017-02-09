FROM fedora
MAINTAINER Clement Verna <cverna@tutanota.com>

RUN dnf install -y dnf-plugins-core && \
    dnf copr enable -y cverna/pagure-importer && \
    dnf install -y python3-pgimport

RUN adduser -m duser

ENV LC_ALL=en_GB.UTF-8
