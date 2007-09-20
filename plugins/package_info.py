import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning)

from hwtest.plugin import Plugin
from hwtest.report_helpers import createElement, createTypedElement

from apt.cache import Cache


class Package(object):

    def __init__(self, apt_package):
        self._apt_package = apt_package

    @property
    def properties(self):
        package = self._apt_package
        return {
            "name": package.name,
            "priority": package.priority,
            "section": package.section,
            "source": package.sourcePackageName,
            "version": package.installedVersion,
            "installed_size": package.installedSize,
            "size": package.packageSize,
            "summary": package.summary}


class PackageManager(object):

    def __init__(self):
        self._cache = Cache()

    def get_packages(self):
        packages = []
        for apt_package in self._cache:
            if apt_package.isInstalled:
                package = Package(apt_package)
                packages.append(package)

        return packages

class PackageInfo(Plugin):

    def __init__(self, package_manager=None):
        super(PackageInfo, self).__init__()
        self._package_manager = package_manager or PackageManager()

    def register(self, manager):
        self._manager = manager
        self._manager.reactor.call_on("gather_information", self.gather_information)
        self._manager.reactor.call_on("run", self.run)

    def gather_information(self):
        report = self._manager.report
        content = self._package_info
        packages = createElement(report, 'packages', report.root)
        for package in content:
            name = package['name']
            del package['name']
            createTypedElement(report, 'package', packages, name, package,
                               True)

    def run(self):
        self._package_info = []

        for package in self._package_manager.get_packages():
            properties = package.properties
            self._package_info.append(properties)


factory = PackageInfo
