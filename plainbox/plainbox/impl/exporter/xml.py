# This file is part of Checkbox.
#
# Copyright 2013 Canonical Ltd.
# Written by:
#   Sylvain Pineau <sylvain.pineau@canonical.com>
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.

#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`plainbox.impl.exporter.xml`
=================================

XML exporter for :term:`certification website`

.. warning::
    THIS MODULE DOES NOT HAVE A STABLE PUBLIC API
"""

from base64 import standard_b64decode
from collections import OrderedDict
from datetime import datetime
from io import BytesIO
import logging

from lxml import etree as ET
from pkg_resources import resource_filename

from plainbox import __version__ as version
from plainbox.abc import IJobResult
from plainbox.impl.exporter import SessionStateExporterBase


logger = logging.getLogger("plainbox.exporter.xml")


class XMLValidator:
    """
    A validator for documents produced by XMLSessionStateExporter
    """

    def __init__(self):
        """
        Initialize a new XMLValidator

        :raises ImportError: when lxml is not installed
        """
        schema_path = resource_filename(
            "plainbox", "data/report/hardware-1_0.rng")
        self._validator = ET.RelaxNG(file=schema_path)

    def validate_text(self, text):
        """
        Validate the given text

        :param text: text to validate
        """
        element = ET.fromstring(text)
        return self.validate_element(element)

    def validate_element(self, element):
        """
        Validate the given element

        :param element: lxml.etree.ElementTree.Element to validate
        :returns: True, if the document is valid
        """
        return self._validator.validate(element)


class XMLSessionStateExporter(SessionStateExporterBase):
    """
    Session state exporter creating XML documents

    The following resource jobs are needed to validate sections of this report:
        * 2013.com.canonical.certification::package   (Optional)
        * 2013.com.canonical.certification::uname     (Optional)
        * 2013.com.canonical.certification::lsb       (Mandatory)
        * 2013.com.canonical.certification::cpuinfo   (Mandatory)
        * 2013.com.canonical.certification::dpkg      (Mandatory)

    The Hardware sections includes the content of the following attachments:
        * 2013.com.canonical.certification::dmi_attachment
        * 2013.com.canonical.certification::sysfs_attachment
        * 2013.com.canonical.certification::udev_attachment
    """

    NS = '2013.com.canonical.certification::'

    OPTION_CLIENT_NAME = 'client-name'
    SUPPORTED_OPTION_LIST = (OPTION_CLIENT_NAME, )

    # These are the job statuses allowed by the checkbox parser.
    # This is a limitation of the certification website, so we
    # have to accomodate that here.
    _ALLOWED_STATUS = [
        "none",
        IJobResult.OUTCOME_PASS,
        IJobResult.OUTCOME_FAIL,
        IJobResult.OUTCOME_SKIP]

    # This describes mappings from all possible plainbox job statuses
    # to one of the allowed statuses listed above.
    _STATUS_MAP = {
        "none": "none",
        IJobResult.OUTCOME_NONE: "none",
        IJobResult.OUTCOME_PASS: IJobResult.OUTCOME_PASS,
        IJobResult.OUTCOME_FAIL: IJobResult.OUTCOME_FAIL,
        IJobResult.OUTCOME_SKIP: IJobResult.OUTCOME_SKIP,
        IJobResult.OUTCOME_UNDECIDED: "none",
        IJobResult.OUTCOME_NOT_IMPLEMENTED: IJobResult.OUTCOME_SKIP,
        IJobResult.OUTCOME_NOT_SUPPORTED: IJobResult.OUTCOME_SKIP}

    def __init__(self, option_list=None, system_id=None, timestamp=None,
                 client_version=None, client_name='plainbox'):
        """
        Initialize a new XMLSessionStateExporter with given arguments.

        This exporter is special-purpose so it differs a little from what other
        exporters do. It does not support any options (it still uses options to
        initialize some of the internal state) but instead has three arguments
        that should be provided in actual situation.

        :param system_id:
            An anonymous system identifier sent to the :term:`certification
            website`. This is currently ill-defined and is a legacy of
            :term:`CheckBox` design.

        :param timestamp:
            A timestamp that is embedded in the produced XML.
            Defaults to current data and time.

        :param client_version:
            The version of the exporter to report. Defaults to the version of
            :term:`PlainBox`.

        :param client_name:
            The name of the exporter to report. Defaults to "plainbox".
        """
        # Super-call with empty option list
        super(XMLSessionStateExporter, self).__init__((option_list))
        # All the "options" are simply a required configuration element and are
        # not optional in any way. There is no way to opt-out.
        xml_options = (SessionStateExporterBase.OPTION_WITH_IO_LOG,
                       SessionStateExporterBase.OPTION_FLATTEN_IO_LOG,
                       SessionStateExporterBase.OPTION_WITH_JOB_DEFS,
                       SessionStateExporterBase.OPTION_WITH_RESOURCE_MAP,
                       SessionStateExporterBase.OPTION_WITH_COMMENTS,
                       SessionStateExporterBase.OPTION_WITH_ATTACHMENTS)
        for option in xml_options:
                self.set_option_value(option)

        # Generate a dummy system hash if needed
        if system_id is None:
            # FIXME: Compute an real system_id for submission to
            # Launchpad Note: Using DMI data won't work on arm platforms
            system_id = ""
        self._system_id = system_id
        # Generate a timestamp if needed
        if timestamp is None:
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        self._timestamp = timestamp
        # Use current version unless told otherwise
        if client_version is None:
            client_version = "{}.{}.{}".format(*version[:3])
        self._client_version = client_version
        # Remember client name
        self._client_name = client_name
        # If a client name was specified as an option, prefer that.
        if self.get_option_value('client-name'):
            self._client_name = self.get_option_value('client-name')

    def dump(self, data, stream):
        """
        Public method to dump the XML report to a stream
        """
        root = self.get_root_element(data)
        # XXX: this is pretty terrible but I have not found another
        # way of getting around the problem.
        #
        # Problem: lxml.etree.ElementTree().write() does not support
        # encoding="unicode" as xml.etree.ElementTree().write() does.
        # This special value for encoding indicates that no encoding should be
        # performed and that original strings should be returned.
        # Apparently lxml does not support that and always returns bytes.
        #
        # Workaround: transcode via UTF-8
        with BytesIO() as helper_stream:
            ET.ElementTree(root).write(
                helper_stream, xml_declaration=True, encoding="UTF-8",
                pretty_print=True)
            stream.write(helper_stream.getvalue())

    def get_root_element(self, data):
        """
        Get the XML element of the document exported from the given data
        """
        root = ET.Element("system", attrib={"version": "1.0"})
        self._add_context(root, data)
        self._add_hardware(root, data)
        self._add_questions(root, data)
        self._add_software(root, data)
        self._add_summary(root, data)
        return root

    def _add_context(self, element, data):
        """
        Add the context section of the XML report
        """
        context = ET.SubElement(element, "context")
        for job_id in data["attachment_map"]:
            # The following attachments are used by the hardware section
            if job_id in ['{}dmi_attachment'.format(self.NS),
                          '{}sysfs_attachment'.format(self.NS),
                          '{}udev_attachment'.format(self.NS)]:
                continue
            # The only allowed attribute is the job command
            # But to be used safely backslash continuation characters have
            # to be removed.
            # The new certification website displays the job name instead.
            # So send what it expects.
            info = ET.SubElement(
                context, "info", attrib={
                    "command": job_id[len(self.NS):]
                    if job_id.startswith(self.NS) else job_id
                }
            )
            # Special case of plain text attachments, they are sent without any
            # base64 encoding, this may change if we add the MIME type to the
            # list of attributes
            content = ""
            try:
                content = standard_b64decode(
                    data["attachment_map"][job_id].encode()).decode("UTF-8")
            except UnicodeDecodeError:
                content = data["attachment_map"][job_id]
            finally:
                info.text = content

    def get_resource(self, data, partial_id):
        """
        Get resource with the specified partial_id

        :param data:
            data obtained from get_session_data_subset()
        :param partial_id:
            partial identifier of the resuorce job
        :returns:
            List of resource objects or None. Does not return empty lists.
        """
        resource_id = '{}{}'.format(self.NS, partial_id)
        resource = data["resource_map"].get(resource_id)
        if resource:
            return resource

    def _add_hardware(self, element, data):
        """
        Add the hardware section of the XML report
        """
        def as_text(attachment):
            return standard_b64decode(
                data["attachment_map"][attachment].encode()
            ).decode("ASCII", "ignore")
        hardware = ET.SubElement(element, "hardware")
        # Attach the content of "dmi_attachment"
        dmi = ET.SubElement(hardware, "dmi")
        if "{}dmi_attachment".format(self.NS) in data["attachment_map"]:
            dmi.text = as_text("{}dmi_attachment".format(self.NS))
        # Attach the content of "sysfs_attachment"
        sysfs_attributes = ET.SubElement(hardware, "sysfs-attributes")
        if "{}sysfs_attachment".format(self.NS) in data["attachment_map"]:
            sysfs_attributes.text = as_text(
                "{}sysfs_attachment".format(self.NS))
        # Attach the content of "udev_attachment"
        udev = ET.SubElement(hardware, "udev")
        if "{}udev_attachment".format(self.NS) in data["attachment_map"]:
            udev.text = as_text("{}udev_attachment".format(self.NS))
        cpuinfo_data = self.get_resource(data, "cpuinfo")
        if cpuinfo_data is not None:
            processors = ET.SubElement(hardware, "processors")
            try:
                count = int(cpuinfo_data[0].get('count', '0'))
            except ValueError:
                count = 0
            for i in range(count):
                processor = ET.SubElement(
                    processors, "processor",
                    attrib=OrderedDict((
                        ("id", str(i)),
                        ("name", str(i)))))
                for key, value in sorted(cpuinfo_data[0].items()):
                    cpu_property = ET.SubElement(
                        processor, "property",
                        attrib=OrderedDict((
                            ("name", key),
                            ("type", "str"))))
                    cpu_property.text = value

    def _add_answer_choices(self, element):
        """
        Helper writing the answer_choices sections of the XML report
        Every question element must have this group of values.
        """
        answer_choices = ET.SubElement(element, "answer_choices")
        for status in self._ALLOWED_STATUS:
            value = ET.SubElement(
                answer_choices, "value", attrib={"type": "str"})
            value.text = status

    def _add_questions(self, element, data):
        """
        Add the questions section of the XML report, using the result map
        """
        questions = ET.SubElement(element, "questions")
        for job_id, job_data in data["result_map"].items():
            # Resource jobs are managed in the hardware/software/summary
            # sections and regular attachments are listed in the context
            # element (but dmi, sysfs-attributes and udev are part of the
            # hardware section).
            if job_data["plugin"] in ("resource", "local", "attachment"):
                continue
            question = ET.SubElement(
                questions, "question", attrib={
                    "name": job_id[len(self.NS):]
                    if job_id.startswith(self.NS) else job_id
                }
            )
            answer = ET.SubElement(
                question, "answer", attrib={"type": "multiple_choice"})
            if job_data["outcome"]:
                answer.text = self._STATUS_MAP[job_data["outcome"]]
            else:
                answer.text = self._ALL_STATUS[0]
            self._add_answer_choices(question)
            comment = ET.SubElement(question, "comment")
            if "comments" in job_data and job_data["comments"]:
                comment.text = job_data["comments"]
            elif job_data["io_log"]:
                comment.text = standard_b64decode(
                    job_data["io_log"].encode()).decode('UTF-8')
            else:
                comment.text = ""

    def _add_software(self, element, data):
        """
        Add the software section of the XML report
        """
        software = ET.SubElement(element, "software")
        lsb_data = self.get_resource(data, "lsb")
        if lsb_data is not None:
            lsbrelease = ET.SubElement(software, "lsbrelease")
            for key, value in lsb_data[0].items():
                lsb_property = ET.SubElement(
                    lsbrelease, "property",
                    attrib=OrderedDict((
                        ("name", key),
                        ("type", "str"))))
                lsb_property.text = value
        package_data = self.get_resource(data, "package")
        if package_data is not None:
            packages = ET.SubElement(software, "packages")
            for index, package_dict in enumerate(package_data):
                package = ET.SubElement(
                    packages, "package", attrib=OrderedDict((
                        ("id", str(index)),
                        ("name", package_dict["name"]))))
                for key, value in package_dict.items():
                    if key == "name":
                        continue
                    package_property = ET.SubElement(
                        package, "property", attrib=OrderedDict((
                            ("name", key),
                            ("type", "str"))))
                    package_property.text = value
        requirements_data = self.get_resource(data, "requirements")
        if requirements_data is not None:
            requirements = ET.SubElement(software, "requirements")
            for index, requirements_dict in enumerate(requirements_data):
                requirement = ET.SubElement(
                    requirements, "requirement", attrib=OrderedDict((
                        ("id", str(index)),
                        ("name", requirements_dict["name"]))))
                for key, value in requirements_dict.items():
                    if key == "name":
                        continue
                    requirements_property = ET.SubElement(
                        requirement, "property", attrib=OrderedDict((
                            ("name", key),
                            ("type", "str"))))
                    requirements_property.text = value

    def _add_summary(self, element, data):
        """
        Add the summary section of the XML report
        """
        summary = ET.SubElement(element, "summary")
        # Insert client identifier
        ET.SubElement(
            summary, "client", attrib=OrderedDict((
                ("name", self._client_name),
                ("version", self._client_version))))
        # Insert the generation timestamp
        ET.SubElement(
            summary, "date_created", attrib={"value": self._timestamp})
        # Dump some data from 'dpkg' resource
        dpkg_data = self.get_resource(data, "dpkg")
        if dpkg_data is not None:
            ET.SubElement(
                summary, "architecture", attrib={
                    "value": dpkg_data[0]["architecture"]})
        # Dump some data from 'lsb' resource
        lsb_data = self.get_resource(data, "lsb")
        if lsb_data is not None:
            ET.SubElement(
                summary, "distribution", attrib={
                    "value": lsb_data[0]["distributor_id"]})
            ET.SubElement(
                summary, "distroseries", attrib={
                    "value": lsb_data[0]["release"]})
        # Dump some data from 'uname' resource
        uname_data = self.get_resource(data, "uname")
        if uname_data is not None:
            ET.SubElement(
                summary, "kernel-release", attrib={
                    "value": uname_data[0]["release"]})
        # NOTE: this element is a legacy from the previous certification
        # website. It is retained for compatibility.
        ET.SubElement(
            summary, "private", attrib={"value": "False"})
        # NOTE: as above, legacy compatibility
        ET.SubElement(
            summary, "contactable", attrib={"value": "False"})
        # NOTE: as above, legacy compatibility
        ET.SubElement(
            summary, "live_cd", attrib={"value": "False"})
        # Insert the system identifier string
        ET.SubElement(
            summary, "system_id", attrib={"value": self._system_id})
