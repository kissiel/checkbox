# This file is part of Checkbox.
#
# Copyright 2012-2014 Canonical Ltd.
# Written by:
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
:mod:`plainbox.impl.template` -- template unit
==============================================
"""

import logging
import itertools

from plainbox.i18n import gettext as _
from plainbox.impl.resource import ExpressionFailedError
from plainbox.impl.resource import Resource
from plainbox.impl.resource import ResourceProgram
from plainbox.impl.resource import ResourceProgramError
from plainbox.impl.resource import parse_imports_stmt
from plainbox.impl.secure.origin import Origin
from plainbox.impl.unit import Unit
from plainbox.impl.unit import all_units
from plainbox.impl.unit.job import JobDefinition
from plainbox.impl.validation import Problem
from plainbox.impl.validation import ValidationError


__all__ = ['TemplateUnitValidator', 'TemplateUnit']


logger = logging.getLogger("plainbox.unit.template")


class TemplateUnitValidator:
    """
    Validator for template unit
    """

    @classmethod
    def validate(cls, template, strict=False, deprecated=False):
        """
        Validate the specified job template

        :param strict:
            Enforce strict validation. Non-conforming jobs will be rejected.
            This is off by default to ensure that non-critical errors don't
            prevent jobs from running.
        :param deprecated:
            Enforce deprecation validation. Jobs having deprecated fields will
            be rejected. This is off by default to allow backwards compatible
            jobs to be used without any changes.
        """
        # All templates need the template-resource field
        if template.template_resource is None:
            raise ValidationError(
                template.fields.template_resource, Problem.missing)
        # All templates need a valid (or empty) template filter
        try:
            template.get_filter_program()
        except (ResourceProgramError, SyntaxError) as exc:
            raise ValidationError(
                template.fields.template_filter, Problem.wrong,
                hint=str(exc))
        # All templates should use the resource object correctly. This is
        # verified by the code below. It generally means that fields should or
        # should not use variability induced by the resource object data.
        accessed_parameters = template.get_accessed_parameters(force=True)
        # The unit field must be constant.
        if ('unit' in accessed_parameters
                and len(accessed_parameters['unit']) != 0):
            raise ValidationError(template.fields.id, Problem.variable)
        # Now that we know it's constant we can look up the unit it is supposed
        # to instantiate.
        try:
            unit_cls = template.get_target_unit_cls()
        except LookupError:
            raise ValidationError(template.fields.unit, Problem.wrong)
        # Let's look at the template constraints for the unit
        for field, constraint in unit_cls.Meta.template_constraints.items():
            assert constraint in ('vary', 'const')
            if constraint == 'vary':
                if (field in accessed_parameters
                        and len(accessed_parameters[field]) == 0):
                    raise ValidationError(field, Problem.constant)
            elif constraint == 'const':
                if (field in accessed_parameters
                        and len(accessed_parameters[field]) != 0):
                    raise ValidationError(field, Problem.variable)
        # Lastly an example unit generated with a fake resource should still be
        resource = cls._get_fake_resource(accessed_parameters)
        unit = template.instantiate_one(resource, unit_cls_hint=unit_cls)
        return unit.validate(strict=strict, deprecated=deprecated)

    @classmethod
    def _get_fake_resource(cls, accessed_parameters):
        return Resource({
            key: key.upper()
            for key in set(itertools.chain(*accessed_parameters.values()))
        })


class TemplateUnit(Unit):
    """
    Template that can instantiate zero or more additional units.

    Templates are a generalized replacement to the ``local job`` system from
    Checkbox.  Instead of running a job definition that prints additional job
    definitions, a static template is provided. PlainBox has all the visibility
    of each of the fields in the template and can perform validation and other
    analysis without having to run any external commands.

    To instantiate a template a resource object must be provided. This adds a
    natural dependency from each template unit to a resource job definition
    unit. Actual instantiation allows PlainBox to create additional unit
    instance for each resource eligible record. Eligible records are either all
    records or a subset of records that cause the filter program to evaluate to
    True. The filter program uses the familiar resource program syntax
    available to normal job definitions.

    :attr _filter_program:
        Cached ResourceProgram computed (once) and returned by
        :meth:`get_filter_program()`
    """

    def __init__(self, data, origin=None, provider=None, raw_data=None):
        """
        Initialize a new TemplateUnit instance.

        :param data:
            Normalized data that makes up this job template
        :param origin:
            An (optional) Origin object. If omitted a fake origin object is
            created. Normally the origin object should be obtained from the
            RFC822Record object.
        :param provider:
            An (optional) Provider1 object. If omitted it defaults to None but
            the actual job template is not suitable for execution. All job
            templates are expected to have a provider.
        :param controller:
            An (optional) session state controller. If omitted a checkbox
            session state controller is implicitly used. The controller defines
            how this job influences the session it executes in.
        :param raw_data:
            An (optional) raw version of data, without whitespace
            normalization. If omitted then raw_data is assumed to be data.

        .. note::
            You should almost always use :meth:`from_rfc822_record()` instead.
        """
        if origin is None:
            origin = Origin.get_caller_origin()
        super().__init__(data, raw_data, origin, provider)
        self._filter_program = None

    def __str__(self):
        return "{} <~ {}".format(self.id, self.resource_id)

    class fields(JobDefinition.fields):
        """
        Symbols for each field that a TemplateUnit can have
        """
        template_unit = 'template-unit'
        template_resource = 'template-resource'
        template_filter = 'template-filter'
        template_imports = 'template-imports'

    def get_unit_type(self):
        return _("template")

    @property
    def partial_id(self):
        """
        Identifier of this job, without the provider name

        This field should not be used anymore, except for display
        """
        return self.get_record_value('id', '?')

    @property
    def id(self):
        if self._provider:
            return "{}::{}".format(self._provider.namespace, self.partial_id)
        else:
            return self.partial_id

    @property
    def resource_partial_id(self):
        """
        name of the referenced resource object
        """
        text = self.template_resource
        if text is not None and "::" in text:
            return text.split("::", 1)[1]
        return text

    @property
    def resource_namespace(self):
        """
        namespace of the referenced resource object
        """
        text = self.template_resource
        if text is not None and "::" in text:
            return text.split("::", 1)[0]
        elif self._provider is not None:
            return self._provider.namespace

    @property
    def resource_id(self):
        """
        fully qualified identifier of the resource object
        """
        resource_partial_id = self.resource_partial_id
        if resource_partial_id is None:
            return None
        imports = self.get_imported_jobs()
        assert imports is not None
        for imported_resource_id, imported_alias in imports:
            if imported_alias == resource_partial_id:
                return imported_resource_id
        resource_namespace = self.resource_namespace
        if resource_namespace is None:
            return resource_partial_id
        else:
            return "{}::{}".format(resource_namespace, resource_partial_id)

    @property
    def template_resource(self):
        """
        value of the 'template-resource' field
        """
        return self.get_record_value('template-resource')

    @property
    def template_filter(self):
        """
        value of the 'template-filter' field

        This attribute stores the text of a resource program (optional) that
        select a subset of available resource objects.  If you wish to access
        the actual resource program call :meth:`get_filter_program()`. In both
        cases the value can be None.
        """
        return self.get_record_value('template-filter')

    @property
    def template_imports(self):
        """
        value of the 'template-imports' field

        This attribute stores the text of a resource import that is specific
        to the template itself. In other words, it allows the template
        to access resources from any namespace.
        """
        return self.get_record_value('template-imports')

    @property
    def template_unit(self):
        """
        value of the 'template-unit' field

        This attribute stores the name of the unit that this template intends
        to instantiate. It defaults to 'unit' for backwards compatibility and
        simplicity.
        """
        return self.get_record_value('template-unit', 'job')

    def get_imported_jobs(self):
        """
        Parse the 'imports' line and compute the imported symbols.

        Return generator for a sequence of pairs (job_id, identifier) that
        describe the imported job identifiers from arbitrary namespace.

        The syntax of each imports line is:

        IMPORT_STMT ::  "from" <NAMESPACE> "import" <PARTIAL_ID>
                      | "from" <NAMESPACE> "import" <PARTIAL_ID>
                         AS <IDENTIFIER>
        """
        imports = self.template_imports or ""
        return parse_imports_stmt(imports)

    def get_filter_program(self):
        """
        Get filter program compiled from the template-filter field

        :returns:
            ResourceProgram created out of the text of the template-filter
            field.
        """
        if self.template_filter is not None and self._filter_program is None:
            self._filter_program = ResourceProgram(
                self.template_filter, self.resource_namespace,
                self.get_imported_jobs())
        return self._filter_program

    def get_target_unit_cls(self):
        """
        Get the Unit subclass that implements the instantiated unit

        :returns:
            A subclass of Unit the template will try to instantiate. If there
            is no ``template-unit`` field in the template then a ``job``
            template is assumed.

        .. note::
            Typically this will return a JobDefinition class but it's not the
            only possible value.
        """
        all_units.load()
        unit_cls = all_units.get_by_name(self.template_unit).plugin_object
        assert isinstance(unit_cls, type)
        assert issubclass(unit_cls, Unit)
        return unit_cls

    def instantiate_all(self, resource_list):
        """
        Instantiate a list of job definitions by creating one from each
        non-filtered out resource records.

        :param resource_list:
            A list of resource objects with the correct name
            (:meth:`template_resource`)
        :returns:
            A list of new Unit (or subclass) objects.
        """
        unit_cls = self.get_target_unit_cls()
        return [
            self.instantiate_one(resource, unit_cls_hint=unit_cls)
            for resource in resource_list
            if self.should_instantiate(resource)
        ]

    def instantiate_one(self, resource, unit_cls_hint=None):
        """
        Instantiate a single job out of a resource and this template.

        :param resource:
            A Resource object to provide template data
        :returns:
            A new JobDefinition created out of the template and resource data.
        :raises AttributeError:
            If the template referenced a value not defined by the resource
            object.

        Fields starting with the string 'template-' are discarded. All other
        fields are interpolated by attributes from the resource object.
        References to missing resource attributes cause the process to fail.
        """
        # Look up the unit we're instantiating
        if unit_cls_hint is not None:
            unit_cls = unit_cls_hint
        else:
            unit_cls = self.get_target_unit_cls()
        assert unit_cls is not None
        # Filter out template- data fields as they are not relevant to the
        # target unit.
        data = {
            key: value for key, value in self._data.items()
            if not key.startswith('template-')
        }
        raw_data = {
            key: value for key, value in self._raw_data.items()
            if not key.startswith('template-')
        }
        # Override the value of the 'unit' field from 'template-unit' field
        data['unit'] = raw_data['unit'] = self.template_unit
        # XXX: extract raw dictionary from the resource object, there is no
        # normal API for that due to the way resource objects work.
        parameters = object.__getattribute__(resource, '_data')
        # Instantiate the class using the instantiation API
        return unit_cls.instantiate_template(
            data, raw_data, self.origin, self.provider, parameters)

    def should_instantiate(self, resource):
        """
        Check if a job should be instantiated for a specific resource.

        :param resource:
            A Resource object to check
        :returns:
            True if a job should be instantiated for the resource object

        Determine if a job instance should be created using the specific
        resource object. This is the case if there is no filter or if the
        specified resource object would make the filter program evaluate to
        True.
        """
        program = self.get_filter_program()
        if program is None:
            return True
        try:
            # NOTE: this is a little tricky. The interface for
            # evaluate_or_raise() is {str: List[Resource]} but we are being
            # called with Resource. The reason for that is that we wish to get
            # per-resource answer not an aggregate 'yes' or 'no'.
            return program.evaluate_or_raise({
                self.resource_id: [resource]
            })
        except ExpressionFailedError:
            return False

    def validate(self, **validation_kwargs):
        """
        Validate this job definition template

        :param validation_kwargs:
            Keyword arguments to pass to the
            :meth:`TemplateUnitValidator.validate()`
        :raises ValidationError:
            If the template has any problems that make it unsuitable for
            execution.
        """
        super().validate()
        return TemplateUnitValidator.validate(self, **validation_kwargs)
