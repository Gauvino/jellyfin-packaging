# Docker build arguments
ARG DOTNET_VERSION=8.0
ARG NODEJS_VERSION=20
# Default to 12, but set externally by the `build.py` script
ARG GCC_VERSION=12

ARG PACKAGE_TYPE
ARG PACKAGE_VERSION
ARG PACKAGE_ARCH

FROM ${PACKAGE_TYPE}:${PACKAGE_VERSION}

ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist
ARG DOTNET_VERSION
ARG NODEJS_VERSION
ARG PACKAGE_TYPE
ARG PACKAGE_VERSION
ARG PACKAGE_ARCH
ARG GCC_VERSION

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV DEB_BUILD_OPTIONS=noddebs
ENV TYPE=${PACKAGE_TYPE}
ENV VERSION=${PACKAGE_VERSION}
ENV ARCH=${PACKAGE_ARCH}

FROM fedora:39

# Docker build arguments
ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV IS_DOCKER=YES

# Prepare Fedora environment
RUN dnf update -yq \
 && dnf install -yq \
    @buildsys-build rpmdevtools git \
    dnf-plugins-core libcurl-devel fontconfig-devel \
    freetype-devel openssl-devel glibc-devel \
    libicu-devel systemd wget make \
 && dnf clean all \
 && rm -rf /var/cache/dnf

# Install DotNET SDK
RUN wget -q https://download.visualstudio.microsoft.com/download/pr/85bcc525-4e9c-471e-9c1d-96259aa1a315/930833ef34f66fe9ee2643b0ba21621a/dotnet-sdk-8.0.201-linux-x64.tar.gz -O dotnet-sdk.tar.gz \
 && mkdir -p dotnet-sdk \
 && tar -xzf dotnet-sdk.tar.gz -C dotnet-sdk \
 && ln -s $( pwd )/dotnet-sdk/dotnet /usr/bin/dotnet

# Create symlinks and directories
RUN ln -sf ${SOURCE_DIR}/deployment/build.fedora.amd64 /build.sh \
 && mkdir -p ${SOURCE_DIR}/SPECS \
 && ln -s ${SOURCE_DIR}/fedora/jellyfin.spec ${SOURCE_DIR}/SPECS/jellyfin.spec \
 && mkdir -p ${SOURCE_DIR}/SOURCES \
 && ln -s ${SOURCE_DIR}/fedora ${SOURCE_DIR}/SOURCES

VOLUME ${SOURCE_DIR}/

VOLUME ${ARTIFACT_DIR}/

ENTRYPOINT ["/build.sh"]

FROM quay.io/centos/centos:stream9

# Docker build arguments
ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV IS_DOCKER=YES

# Prepare CentOS environment
RUN dnf update -yq \
 && dnf install -yq \
    @buildsys-build rpmdevtools git \
    dnf-plugins-core libcurl-devel fontconfig-devel \
    freetype-devel openssl-devel glibc-devel \
    libicu-devel systemd wget make \
 && dnf clean all \
 && rm -rf /var/cache/dnf

# Install DotNET SDK
RUN wget -q https://download.visualstudio.microsoft.com/download/pr/85bcc525-4e9c-471e-9c1d-96259aa1a315/930833ef34f66fe9ee2643b0ba21621a/dotnet-sdk-8.0.201-linux-x64.tar.gz -O dotnet-sdk.tar.gz \
 && mkdir -p dotnet-sdk \
 && tar -xzf dotnet-sdk.tar.gz -C dotnet-sdk \
 && ln -s $( pwd )/dotnet-sdk/dotnet /usr/bin/dotnet

# Create symlinks and directories
RUN ln -sf ${SOURCE_DIR}/deployment/build.centos.amd64 /build.sh \
 && mkdir -p ${SOURCE_DIR}/SPECS \
 && ln -s ${SOURCE_DIR}/fedora/jellyfin.spec ${SOURCE_DIR}/SPECS/jellyfin.spec \
 && mkdir -p ${SOURCE_DIR}/SOURCES \
 && ln -s ${SOURCE_DIR}/fedora ${SOURCE_DIR}/SOURCES

VOLUME ${SOURCE_DIR}/

VOLUME ${ARTIFACT_DIR}/

ENTRYPOINT ["/build.sh"]