import os
import shutil
import subprocess
from datetime import datetime

import grapejuice_packaging.metadata as metadata
from grapejuice_packaging.directory_stack import DirectoryStack
from grapejuice_packaging.packaging_platform import Platform

ARCHITECTURE = "amd64"
STANDARDS_VERSION = "3.9.6"
DEBHELPER_COMPAT = 10
VERSION = f"{metadata.package_version}"
PACKAGE_VERSION = f"{VERSION}_{ARCHITECTURE}"
PREFIX = "/usr/lib"
PYTHON_DIST_PACKAGES_DIR = f"{PREFIX}/python3/dist-packages"
MAINTAINER = f"{metadata.author_name} <{metadata.author_email}>"
PACKAGE_FILENAME = f"{metadata.package_name}_{PACKAGE_VERSION}.deb"
DEBIAN_SECTION = "python"
DEBIAN_PRIORITY = "optional"
DEBIAN_DISTRIBUTION = "unstable"
DEBIAN_URGENCY = "medium"

FIELD_SOURCE = ("Source", metadata.package_name)
FIELD_MAINTAINER = ("Maintainer", MAINTAINER)
FIELD_BUILD_DEPENDS = ("Build-Depends", ["debhelper", "python3", "python3-pip", "python3-virtualenv"])
FIELD_STANDARDS_VERSION = ("Standards-Version", STANDARDS_VERSION)
FIELD_ARCHITECTURE = ("Architecture", ARCHITECTURE)

DSC_FIELDS = [
    ("Format", "1.0"),
    FIELD_SOURCE,
    ("Binary", metadata.package_name),
    FIELD_ARCHITECTURE,
    ("Version", f"{PACKAGE_VERSION}"),
    FIELD_MAINTAINER,
    FIELD_STANDARDS_VERSION,
    FIELD_BUILD_DEPENDS,
    ("Package-List", [metadata.package_name, "deb", "python", "optional", f"arch={ARCHITECTURE}"])
]

CONTROL_FIELDS = [
    FIELD_SOURCE,
    ("Section", DEBIAN_SECTION),
    ("Priority", DEBIAN_PRIORITY),
    FIELD_MAINTAINER,
    FIELD_BUILD_DEPENDS,
    FIELD_STANDARDS_VERSION,
    None,
    ("Package", metadata.package_name),
    FIELD_ARCHITECTURE,
    ("Depends", [
        "python3 (>= 3.7~)",
        "python3-certifi",
        "python3-dbus",
        "python3-packaging",
        "python3-psutil",
        "python3-urllib3",
        "python3-wget",
        "python3-gi",
        "libcairo2",
        "libgirepository-1.0-1",
        "libgtk-3-0",
        "libgtk-3-bin",
        "libdbus-1-3"
    ]),
    ("Homepage", metadata.package_repository),
    ("Description", metadata.package_description + "\n Generated by grapejuice_packaging")
]

COPYRIGHT_FIELDS = [
    ("Format", "https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/"),
    ("Upstream-Name", metadata.project_name),
    ("Upstream-Contact", MAINTAINER),
    FIELD_SOURCE,
    None,
    ("Files", "*"),
    ("Copyright", f"2019-{datetime.now().year} {metadata.author_name}"),
    ("License", metadata.package_license)
]

RULES = """#!/usr/bin/make -f

%:
\tdh $@

override_dh_shlibdeps:
\ttrue
"""


def fields_to_string(fields):
    def process_field(field):
        if field is None:
            return ""

        assert isinstance(field, tuple) or isinstance(field, list)
        assert len(field) == 2

        key, value = field

        if isinstance(value, list):
            value = ", ".join(value)

        return f"{key}: {str(value)}"

    return "\n".join(list(map(process_field, fields)))


class DebianPlatform(Platform):
    def __init__(self):
        self._containment_dish = os.path.join("/", "tmp", "grapejuice-debian")
        self._directory_stack = DirectoryStack()

    @property
    def _package_root(self):
        return os.path.join(self._containment_dish, f"{metadata.package_name}_{PACKAGE_VERSION}")

    @property
    def _debian_directory(self):
        p = os.path.join(self._package_root, "debian")
        os.makedirs(p, exist_ok=True)
        return p

    @property
    def _packages_directory(self):
        p = os.path.join(self._package_root, "packages")
        os.makedirs(p, exist_ok=True)
        return p

    def _write_compat(self):
        with open(os.path.join(self._debian_directory, "compat"), "w+") as fp:
            fp.write(str(int(DEBHELPER_COMPAT)))

    def _write_install(self):
        lines = []
        for package_name in os.listdir(self._packages_directory):
            lines.append(f"packages/{package_name} {PYTHON_DIST_PACKAGES_DIR}\n")

        with open(os.path.join(self._debian_directory, "install"), "w+") as fp:
            fp.writelines(lines)

    def _write_control(self):
        with open(os.path.join(self._debian_directory, "control"), "w+") as fp:
            fp.write(fields_to_string(CONTROL_FIELDS))

    def _write_copyright(self):
        with open(os.path.join(self._debian_directory, "copyright"), "w+") as fp:
            fp.write(fields_to_string(COPYRIGHT_FIELDS))

    def _write_files_file(self):
        with open(os.path.join(self._debian_directory, "files"), "w+") as fp:
            fp.write(" ".join([PACKAGE_FILENAME, DEBIAN_SECTION, DEBIAN_PRIORITY]))

    def _write_rules(self):
        with open(os.path.join(self._debian_directory, "rules"), "w+") as fp:
            fp.write(RULES)

    def _write_changelog(self):
        lines = [f"{metadata.package_name} ({VERSION}) {DEBIAN_DISTRIBUTION}; urgency={DEBIAN_URGENCY}\n", "\n"]

        current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]) \
            .decode("UTF-8").strip()

        changelog = subprocess.check_output(["git", "shortlog", "master..." + current_branch]) \
            .decode("UTF - 8").strip().split("\n")

        for changelog_line in list(map(lambda s: "  * " + s, changelog)):
            lines.append(changelog_line + "\n")

        lines.append("\n")

        date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S") + " +0000"
        lines.append(f" -- {MAINTAINER}  {date_str}\n")

        with open(os.path.join(self._debian_directory, "changelog"), "w+") as fp:
            fp.writelines(lines)

    def _build_unsigned_package(self):
        self._directory_stack.pushd(self._package_root)
        subprocess.check_call(["debuild", "-uc", "-us"])
        self._directory_stack.popd()

    def before_package(self):
        super().before_package()

        if os.path.exists(self._containment_dish):
            shutil.rmtree(self._containment_dish)

        for wheel in Platform.list_wheels():
            shutil.copy(wheel, self._packages_directory)

        cwd = self._directory_stack.pushd(self._packages_directory)

        for file in os.listdir(cwd):
            subprocess.check_call(["unzip", file])
            os.remove(os.path.join(cwd, file))

        self._directory_stack.popd()

    def package(self):
        self._write_compat()
        self._write_install()
        self._write_control()
        self._write_copyright()
        self._write_files_file()
        self._write_rules()
        self._write_changelog()

        self._build_unsigned_package()
