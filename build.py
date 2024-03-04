#!/usr/bin/env python3

# build.py - Build packages in a Docker wrapper
#
# Part of the Jellyfin CI system
###############################################################################

from datetime import datetime
from email.utils import format_datetime, localtime
import os.path
from subprocess import run, PIPE
import sys
from yaml import load, SafeLoader

# Determine top level directory of this repository ("jellyfin-packaging")
revparse = run(["git", "rev-parse", "--show-toplevel"], stdout=PIPE)
repo_root_dir = revparse.stdout.decode().strip()

# Base Docker commands
docker_build_cmd = "docker build --progress=plain --no-cache"
docker_run_cmd = "docker run --rm"


def log(message):
    print(message, flush=True)


# Configuration loader
try:
    with open("build.yaml", encoding="utf-8") as fh:
        configurations = load(fh, Loader=SafeLoader)
except Exception as e:
    log(f"Error: Failed to find 'build.yaml' configuration: {e}")
    exit(1)


def build_package_deb(jellyfin_version, build_type, build_arch, build_version):
    """
    Build a .deb package (Debian or Ubuntu) within a Docker container that matches the requested distribution version
    """
    log(f"> Building an {build_arch} {build_type} .deb package...")
    log("")

    try:
        os_type = build_type if build_type in configurations.keys() else None
        if os_type is None:
            raise ValueError(
                f"{build_type} is not a valid OS type in {configurations.keys()}"
            )
        os_version = (
            configurations[build_type]["releases"][build_version]
            if build_version in configurations[build_type]["releases"].keys()
            else None
        )
        if os_version is None:
            raise ValueError(
                f"{build_version} is not a valid {build_type} version in {configurations[build_type]['releases'].keys()}"
            )
        PACKAGE_ARCH = (
            configurations[build_type]["archmaps"][build_arch]["PACKAGE_ARCH"]
            if build_arch in configurations[build_type]["archmaps"].keys()
            else None
        )
        if PACKAGE_ARCH is None:
            raise ValueError(
                f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}"
            )
    except Exception as e:
        log(f"Invalid/unsupported arguments: {e}")
        exit(1)

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Set the cross-gcc version
    crossgccvers = configurations[build_type]["cross-gcc"][build_version]

    # Prepare the debian changelog file
    changelog_src = f"{repo_root_dir}/debian/changelog.in"
    changelog_dst = f"{repo_root_dir}/debian/changelog"

    with open(changelog_src) as fh:
        changelog = fh.read()

    if "v" in jellyfin_version:
        comment = f"Jellyfin release {jellyfin_version}, see https://github.com/jellyfin/jellyfin/releases/{jellyfin_version} for details."
    else:
        comment = f"Jellyin unstable release {jellyfin_version}."
    jellyfin_version = jellyfin_version.replace("v", "")

    changelog = changelog.format(
        package_version=jellyfin_version,
        package_build=f"{build_type[:3]}{os_version.replace('.', '')}",
        release_comment=comment,
        release_date=format_datetime(localtime()),
    )

    with open(changelog_dst, "w") as fh:
        fh.write(changelog)

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}-{build_version}"

    # Build the dockerfile and packages
    os.system(
        f"{docker_build_cmd} --build-arg PACKAGE_TYPE={os_type} --build-arg PACKAGE_VERSION={os_version} --build-arg PACKAGE_ARCH={PACKAGE_ARCH} --build-arg GCC_VERSION={crossgccvers} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
    )
    os.system(
        f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --name {imagename} {imagename}"
    )


def build_package_rpm(jellyfin_version, build_type, build_arch, build_version):
    """
    Build a .rpm package (Fedora or CentOS) within a Docker container that matches the requested distribution version
    """
    log(f"> Building an {build_arch} {build_type} .rpm package...")
    log("")

    pass


def build_linux(jellyfin_version, build_type, build_arch, _build_version):
    """
    Build a portable Linux archive
    """
    log(f"> Building a portable {build_arch} Linux archive...")
    log("")

    try:
        PACKAGE_ARCH = (
            configurations[build_type]["archmaps"][build_arch]["PACKAGE_ARCH"]
            if build_arch in configurations[build_type]["archmaps"].keys()
            else None
        )
        if PACKAGE_ARCH is None:
            raise ValueError(
                f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}"
            )
        DOTNET_ARCH = configurations[build_type]["archmaps"][build_arch]["DOTNET_ARCH"]
    except Exception as e:
        log(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jellyfin_version = jellyfin_version.replace("v", "")

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(
        f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
    )
    os.system(
        f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env PACKAGE_ARCH={PACKAGE_ARCH} --env DOTNET_TYPE=linux --env DOTNET_ARCH={DOTNET_ARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}"
    )


def build_windows(jellyfin_version, build_type, _build_arch, _build_version):
    """
    Build a portable Windows archive
    """
    log(f"> Building a portable {build_arch} Windows archive...")
    log("")

    try:
        PACKAGE_ARCH = (
            configurations[build_type]["archmaps"][build_arch]["PACKAGE_ARCH"]
            if build_arch in configurations[build_type]["archmaps"].keys()
            else None
        )
        if PACKAGE_ARCH is None:
            raise ValueError(
                f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}"
            )
        DOTNET_ARCH = configurations[build_type]["archmaps"][build_arch]["DOTNET_ARCH"]
    except Exception as e:
        log(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jellyfin_version = jellyfin_version.replace("v", "")

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(
        f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
    )
    os.system(
        f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env PACKAGE_ARCH={PACKAGE_ARCH} --env DOTNET_TYPE=win --env DOTNET_ARCH={DOTNET_ARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}"
    )


def build_macos(jellyfin_version, build_type, build_arch, _build_version):
    """
    Build a portable MacOS archive
    """
    log(f"> Building a portable {build_arch} MacOS archive...")
    log("")

    try:
        PACKAGE_ARCH = (
            configurations[build_type]["archmaps"][build_arch]["PACKAGE_ARCH"]
            if build_arch in configurations[build_type]["archmaps"].keys()
            else None
        )
        if PACKAGE_ARCH is None:
            raise ValueError(
                f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}"
            )
        DOTNET_ARCH = configurations[build_type]["archmaps"][build_arch]["DOTNET_ARCH"]
    except Exception as e:
        log(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jellyfin_version = jellyfin_version.replace("v", "")

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(
        f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
    )
    os.system(
        f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env PACKAGE_ARCH={PACKAGE_ARCH} --env DOTNET_TYPE=osx --env DOTNET_ARCH={DOTNET_ARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}"
    )


def build_portable(jellyfin_version, build_type, _build_arch, _build_version):
    """
    Build a portable .NET archive
    """
    log("> Building a portable .NET archive...")
    log("")

    jellyfin_version = jellyfin_version.replace("v", "")

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = (
        f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_type}"
    )

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(
        f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
    )
    os.system(
        f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}"
    )


def build_docker(jellyfin_version, build_type, _build_arch, _build_version):
    """
    Build Docker images for all architectures and combining manifests
    """
    log("> Building Docker images...")
    log("")

    # We build all architectures simultaneously to push a single tag, so no conditional checks
    architectures = configurations["docker"]["archmaps"].keys()

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Determine if this is a "latest"-type image (v in jellyfin_version) or not
    if "v" in jellyfin_version:
        is_latest = True
        is_unstable = False
        version_suffix = True
    else:
        is_latest = False
        is_unstable = True
        version_suffix = False

    jellyfin_version = jellyfin_version.replace("v", "")

    # Set today's date in a convenient format for use as an image suffix
    date = datetime.now().strftime("%Y%m%d-%H%M%S")

    images = list()
    images_ghcr = list()
    for _build_arch in architectures:
        log(f">> Building Docker image for {_build_arch}...")
        log("")

        # Get our ARCH variables from the archmaps
        PACKAGE_ARCH = configurations["docker"]["archmaps"][_build_arch]["PACKAGE_ARCH"]
        DOTNET_ARCH = configurations["docker"]["archmaps"][_build_arch]["DOTNET_ARCH"]
        QEMU_ARCH = configurations["docker"]["archmaps"][_build_arch]["QEMU_ARCH"]
        IMAGE_ARCH = configurations["docker"]["archmaps"][_build_arch]["IMAGE_ARCH"]

        # Use a unique docker image name for consistency
        if version_suffix:
            imagename = f"{configurations['docker']['imagename']}:{jellyfin_version}-{_build_arch}.{date}"
        else:
            imagename = f"{configurations['docker']['imagename']}:{jellyfin_version}-{_build_arch}"

        # Clean up any existing qemu static image
        log(
            f">>> {docker_run_cmd} --privileged multiarch/qemu-user-static:register --reset"
        )
        os.system(
            f"{docker_run_cmd} --privileged multiarch/qemu-user-static:register --reset"
        )
        log("")

        # Build the dockerfile
        log(
            f">>> {docker_build_cmd} --build-arg PACKAGE_ARCH={PACKAGE_ARCH} --build-arg DOTNET_ARCH={DOTNET_ARCH} --build-arg QEMU_ARCH={QEMU_ARCH} --build-arg IMAGE_ARCH={IMAGE_ARCH} --build-arg JELLYFIN_VERSION={jellyfin_version} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
        )
        os.system(
            f"{docker_build_cmd} --build-arg PACKAGE_ARCH={PACKAGE_ARCH} --build-arg DOTNET_ARCH={DOTNET_ARCH} --build-arg QEMU_ARCH={QEMU_ARCH} --build-arg IMAGE_ARCH={IMAGE_ARCH} --build-arg JELLYFIN_VERSION={jellyfin_version} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}"
        )
        images.append(imagename)

        os.system(f"docker image tag {imagename} ghcr.io/{imagename}")
        images_ghcr.append(f"ghcr.io/{imagename}")

        log("")

    # Log in to docker hub
    os.system("docker login 2>&1")

    # Push the images to DockerHub
    for image in images:
        log(f">>> Pushing image {image} to DockerHub")
        log(f">>>> docker push {image} 2>&1")
        os.system(f"docker push {image} 2>&1")

    # Push the images to GHCR
    for image in ghcr_images:
        log(f">>> Pushing image {image} to GHCR")
        log(f">>>> docker push {image} 2>&1")
        os.system(f"docker push {image} 2>&1")

    # Build the manifests
    log(">> Building Docker manifests...")
    manifests = list()

    if version_suffix:
        log(">>> Building dated version manifest...")
        log(
            f">>>> docker manifest create {configurations['docker']['imagename']}:{jellyfin_version}.{date} {' '.join(images)}"
        )
        os.system(
            f"docker manifest create docker.io/{configurations['docker']['imagename']}:{jellyfin_version}.{date} {' '.join(images)}"
        )
        os.system(
            f"docker manifest create ghcr.io/{configurations['docker']['imagename']}:{jellyfin_version}.{date} {' '.join(images_ghcr)}"
        )
        manifests.append(
            f"{configurations['docker']['imagename']}:{jellyfin_version}.{date}"
        )

    log(">>> Building version manifest...")
    log(
        f">>>> docker manifest create {configurations['docker']['imagename']}:{jellyfin_version} {' '.join(images)}"
    )
    os.system(
        f"docker manifest create docker.io/{configurations['docker']['imagename']}:{jellyfin_version} {' '.join(images)}"
    )
    os.system(
        f"docker manifest create ghcr.io/{configurations['docker']['imagename']}:{jellyfin_version} {' '.join(images_ghcr)}"
    )
    manifests.append(f"{configurations['docker']['imagename']}:{jellyfin_version}")

    if is_latest:
        log(">>> Building latest manifest...")
        log(
            f">>>> docker manifest create {configurations['docker']['imagename']}:latest {' '.join(images)}"
        )
        os.system(
            f"docker manifest create docker.io/{configurations['docker']['imagename']}:latest {' '.join(images)}"
        )
        os.system(
            f"docker manifest create ghcr.io/{configurations['docker']['imagename']}:latest {' '.join(images_ghcr)}"
        )
        manifests.append(f"{configurations['docker']['imagename']}:latest")
    elif is_unstable:
        log(">>> Building unstable manifest...")
        log(
            f">>>> docker manifest create {configurations['docker']['imagename']}:unstable {' '.join(images)}"
        )
        os.system(
            f"docker manifest create docker.io/{configurations['docker']['imagename']}:unstable {' '.join(images)}"
        )
        os.system(
            f"docker manifest create ghcr.io/{configurations['docker']['imagename']}:unstable {' '.join(images_ghcr)}"
        )
        manifests.append(f"{configurations['docker']['imagename']}:unstable")

    # Push the images and manifests to DockerHub (we are already logged in from GH Actions)
    for manifest in manifests:
        log(f">>> Pushing manifest {manifest} to DockerHub")
        log(f">>>> docker manifest push --purge docker.io/{manifest} 2>&1")
        os.system(f"docker manifest push --purge docker.io/{manifest} 2>&1")

    # Push the images and manifests to GHCR (we are already logged in from GH Actions)
    for manifest in manifests:
        log(f">>> Pushing manifest {manifest} to GHCR")
        log(f">>>> docker manifest push --purge ghcr.io/{manifest} 2>&1")
        os.system(f"docker manifest push --purge ghcr.io/{manifest} 2>&1")


def usage():
    """
    Print usage information on error
    """
    log(f"{sys.argv[0]} JELLYFIN_VERSION BUILD_TYPE [BUILD_ARCH] [BUILD_VERSION]")
    log("  JELLYFIN_VERSION: The Jellyfin version being built")
    log("    * Stable releases should be tag names with a 'v' e.g. v10.9.0")
    log(
        "    * Unstable releases should be 'master' or a date-to-the-hour version e.g. 2024021600"
    )
    log("  BUILD_TYPE: The type of build to execute")
    log(f"    * Valid options are: {', '.join(configurations.keys())}")
    log("  BUILD_ARCH: The CPU architecture of the build")
    log("    * Valid options are: <empty> [portable/docker only], amd64, arm64, armhf")
    log("  BUILD_VERSION: A valid OS distribution version (.deb/.rpm build types only)")


# Define a map of possible build functions from the YAML configuration
function_definitions = {
    "build_package_deb": build_package_deb,
    "build_package_rpm": build_package_rpm,
    "build_portable": build_portable,
    "build_linux": build_linux,
    "build_windows": build_windows,
    "build_macos": build_macos,
    "build_portable": build_portable,
    "build_docker": build_docker,
}

try:
    jellyfin_version = sys.argv[1]
    build_type = sys.argv[2]
except IndexError:
    log("Error: Missing required arguments ('JELLYFIN_VERSION' and/or 'BUILD_TYPE')")
    log("")
    usage()
    exit(1)

if build_type not in configurations.keys():
    log(f"Error: The specified build type '{build_type}' is not valid")
    log("")
    usage()
    exit(1)

try:
    if configurations[build_type]["build_function"] not in function_definitions.keys():
        raise ValueError
except Exception:
    log(
        f"Error: The specified valid build type '{build_type}' does not define a valid build function"
    )
    log(
        "This is a misconfiguration of the YAML or the build script; please report a bug!"
    )
    exit(1)

# Optional argument (only required for some build functions)
try:
    build_arch = sys.argv[3]
except IndexError:
    build_arch = None

# Optional argument (only required for some build functions)
try:
    build_version = sys.argv[4]
except IndexError:
    build_version = None

# Autocorrect "master" to a dated version string
if jellyfin_version == "master":
    jellyfin_version = datetime.now().strftime("%Y%m%d%H")
    log(f"NOTE: Autocorrecting 'master' version to {jellyfin_version}")

# Launch the builder function
function_definitions[configurations[build_type]["build_function"]](
    jellyfin_version, build_type, build_arch, build_version
)
