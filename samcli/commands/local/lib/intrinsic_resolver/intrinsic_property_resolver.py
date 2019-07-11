"""
Process and simplifies CloudFormation intrinsic properties such as FN::* and Ref
"""
import logging

import base64
import re

from six import string_types

from samcli.commands.local.lib.intrinsic_resolver.invalid_intrinsic_exception import InvalidIntrinsicException, \
    verify_intrinsic_type_list, verify_non_null, verify_intrinsic_type_int, verify_in_bounds, \
    verify_number_arguments, verify_intrinsic_type_str, verify_intrinsic_type_dict, verify_intrinsic_type_bool, \
    verify_all_list_intrinsic_type, InvalidSymbolException

LOG = logging.getLogger(__name__)


class IntrinsicResolver(object):
    AWS_INCLUDE = "AWS::Include"
    SUPPORTED_MACRO_TRANSFORMATIONS = [AWS_INCLUDE]
    _REGEX_SUB_FUNCTION = r'\$\{(.*?)\}'

    FN_JOIN = "Fn::Join"
    FN_SPLIT = "Fn::Split"
    FN_SUB = "Fn::Sub"
    FN_SELECT = "Fn::Select"
    FN_BASE64 = "Fn::Base64"
    FN_FIND_IN_MAP = "Fn::FindInMap"
    FN_TRANSFORM = "Fn::Transform"
    FN_GET_AZS = "Fn::GetAZs"
    REF = "Ref"
    FN_GET_ATT = "Fn::GetAtt"
    FN_IMPORT_VALUE = "Fn::ImportValue"

    SUPPORTED_INTRINSIC_FUNCTIONS = [
        FN_JOIN,
        FN_SPLIT,
        FN_SUB,
        FN_SELECT,
        FN_BASE64,
        FN_FIND_IN_MAP,
        FN_TRANSFORM,
        FN_GET_AZS,
        REF,
        FN_GET_ATT,
        FN_IMPORT_VALUE
    ]

    FN_AND = "Fn::And"
    FN_OR = "Fn::Or"
    FN_IF = "Fn::If"
    FN_EQUALS = "Fn::Equals"
    FN_NOT = "Fn::Not"

    CONDITIONAL_PROPERTIES = [
        FN_AND,
        FN_OR,
        FN_IF,
        FN_EQUALS,
        FN_NOT
    ]

    def __init__(self, symbol_resolver,
                 template=None,
                 resources=None,
                 mappings=None,
                 parameters=None,
                 conditions=None):
        """
        Initializes the Intrinsic Property class. Customers can pass in their own ref_resolver or attribute_resolver
        to customize the behavior of ref resolution. This can also be done by extending the definition.

        When created the class can either process a template or the individual attributes. The more information given
        the easier resolution will be.

        In the future, for items like Fn::ImportValue multiple templates can be provided
        into the function.
        Parameters
        -----------
        symbol_resolver: IntrinsicsSymbolTable
            This is a required property that is the crux of the intrinsics resolver. It acts as a mapping between
            resource_type and object to the Ref, Arn, etc.
        template: dict
            A dictionary containing all the resources and the attributes of the CloudFormation template.
            Customers can pass in the template or the individual properties like resources, mapping, parameters,
            conditions.
        resources: dict
            Dictionary containing the CloudFormation resources
        mappings: dict
            Dictionary containing the CloudFormation mappings. This is used in the Fn::FindInMap section
        parameters: dict
            Dictionary containing the CloudFormation parameters. This is used in the Ref section
        conditions: dict
            Dictionary containing the CloudFormation conditions. This is used in the Boolean Intrinsics section
        """
        self.template = template or {}
        self.resources = resources or self.template.get("Resources", {})
        self.mapping = mappings or self.template.get("Mappings", {})
        self.parameters = parameters or self.template.get("Parameters", {})
        self.conditions = conditions or self.template.get("Conditions", {})

        self.symbol_resolver = symbol_resolver
        self.symbol_resolver.resources = self.resources
        self.symbol_resolver.parameters = self.parameters

        self.intrinsic_key_function_map = {
            IntrinsicResolver.FN_JOIN: self.handle_fn_join,
            IntrinsicResolver.FN_SPLIT: self.handle_fn_split,
            IntrinsicResolver.FN_SUB: self.handle_fn_sub,
            IntrinsicResolver.FN_SELECT: self.handle_fn_select,
            IntrinsicResolver.FN_BASE64: self.handle_fn_base64,
            IntrinsicResolver.FN_FIND_IN_MAP: self.handle_find_in_map,
            IntrinsicResolver.FN_TRANSFORM: self.handle_fn_transform,
            IntrinsicResolver.FN_GET_AZS: self.handle_fn_get_azs,
            IntrinsicResolver.REF: self.handle_fn_ref,
            IntrinsicResolver.FN_GET_ATT: self.handle_fn_getatt,
            IntrinsicResolver.FN_IMPORT_VALUE: self.handle_fn_import_value
        }

        self.conditional_key_function_map = {
            IntrinsicResolver.FN_AND: self.handle_fn_and,
            IntrinsicResolver.FN_OR: self.handle_fn_or,
            IntrinsicResolver.FN_IF: self.handle_fn_if,
            IntrinsicResolver.FN_EQUALS: self.handle_fn_equals,
            IntrinsicResolver.FN_NOT: self.handle_fn_not
        }

    def intrinsic_property_resolver(self, intrinsic, parent_function="template"):
        """
        This resolves the intrinsic of the format
        {
            intrinsic: dict
        } by calling the function with the relevant intrinsic function resolver.

        This also supports returning a string, list, boolean, int since they may be intermediate steps in the recursion
        process. No transformations are done on these.

        By default this will just return the item if non of the types match. This is because of the function
        resolve_all_attributes which will recreate the resources by processing every aspect of resource.

        Parameters
        ----------
        intrinsic: dict, str, list, bool, int
            This is an intrinsic property or an intermediate step
        parent_function: str
            In case there is a missing property, this is used to figure out where the property resolved is missing.

        Return
        ---------
        The simplified version of the intrinsic function. This could be a list,str,dict depending on the format required
        """
        if intrinsic is None:
            raise InvalidIntrinsicException("Missing Intrinsic property in {}".format(parent_function))

        if any(isinstance(intrinsic, object_type) for object_type in [string_types, list, bool, int]):
            return intrinsic

        if intrinsic == {}:
            return intrinsic

        if not isinstance(intrinsic, dict):
            raise InvalidIntrinsicException(
                "Invalid Intrinsic type. It is not a int, list, str, or dict {}".format(intrinsic))

        keys = list(intrinsic.keys())
        key = keys[0]

        if key in self.intrinsic_key_function_map:
            intrinsic_value = intrinsic.get(key)
            return self.intrinsic_key_function_map.get(key)(intrinsic_value)
        elif key in self.conditional_key_function_map:
            intrinsic_value = intrinsic.get(key)
            return self.conditional_key_function_map.get(key)(intrinsic_value)
        # In this case, it is a dictionary that doesn't directly contain an intrinsic resolver and must be
        # re-parsed to resolve.
        sanitized_dict = {}
        for key, val in intrinsic.items():
            sanitized_key = self.intrinsic_property_resolver(key, parent_function=parent_function)
            sanitized_val = self.intrinsic_property_resolver(val, parent_function=parent_function)
            verify_intrinsic_type_str(sanitized_key,
                                      message="The keys of the dictionary {} in {} must all resolve to a string"
                                      .format(sanitized_key, parent_function))
            sanitized_dict[sanitized_key] = sanitized_val
        return sanitized_dict

    def resolve_template(self, ignore_errors=False):
        """
        This will parse through every entry in a CloudFormation template and resolve them based on the symbol_resolver.
        Customers can optionally ignore resource errors and default to whatever the resource provides.

        Return
        -------
        A resolved template with all references possible simplified
        """
        processed_template = {}
        for key, val in self.resources.items():
            processed_key = self.symbol_resolver.get_translation(key, IntrinsicResolver.REF) or key
            try:
                processed_resource = self.intrinsic_property_resolver(val)
                processed_template[processed_key] = processed_resource
            except (InvalidIntrinsicException, InvalidSymbolException) as e:
                resource_type = val.get("Type", "")
                if ignore_errors:
                    LOG.error("Unable to process properties of %s.%s", key, resource_type)
                    processed_template[key] = val
                else:
                    raise InvalidIntrinsicException(
                        "Exception with property of {}.{}".format(key, resource_type) + ": " + str(e.args))
        return processed_template

    def handle_fn_join(self, intrinsic_value):
        """
        { "Fn::Join" : [ "delimiter", [ comma-delimited list of values ] ] }
        This function will join the items in the list together based on the string using the python join.

        This intrinsic function will resolve all the objects within the function's value and check their type.

        Parameter
        ----------
        intrinsic_value: list, dict
            This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_JOIN)

        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_JOIN)

        delimiter = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_JOIN)

        verify_intrinsic_type_str(delimiter, IntrinsicResolver.FN_JOIN, position_in_list="first")

        value_list = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_JOIN)

        verify_intrinsic_type_list(value_list, IntrinsicResolver.FN_JOIN,
                                   message="The list of values in {} after the "
                                           "delimiter must be a list".format(IntrinsicResolver.FN_JOIN))

        sanitized_value_list = [self.intrinsic_property_resolver(item, parent_function=IntrinsicResolver.FN_JOIN) for
                                item in value_list]
        verify_all_list_intrinsic_type(sanitized_value_list, verification_func=verify_intrinsic_type_str,
                                       property_type=IntrinsicResolver.FN_JOIN)

        return delimiter.join(sanitized_value_list)

    def handle_fn_split(self, intrinsic_value):
        """
        { "Fn::Split" : [ "delimiter", "source string" ] }
        This function will then split the source_string based on the delimiter

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
            This is the value of the object inside the Fn::Split intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_SPLIT)

        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_SPLIT)

        delimiter = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_SPLIT)

        verify_intrinsic_type_str(delimiter, IntrinsicResolver.FN_SPLIT, position_in_list="first")

        source_string = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_SPLIT)

        verify_intrinsic_type_str(source_string, IntrinsicResolver.FN_SPLIT, position_in_list="second")

        return source_string.split(delimiter)

    def handle_fn_base64(self, intrinsic_value):
        """
        { "Fn::Base64" : valueToEncode }
        This intrinsic function will then base64 encode the string using python's base64.

        This function will resolve all the intrinsic properties in valueToEncode
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Base64 intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        data = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_BASE64)

        verify_intrinsic_type_str(data, IntrinsicResolver.FN_BASE64)
        # Encoding then decoding is required to return a string of the data
        return base64.b64encode(data.encode()).decode()

    def handle_fn_select(self, intrinsic_value):
        """
        { "Fn::Select" : [ index, listOfObjects ] }
        It will select the item in the listOfObjects using python's base64.
        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Select intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_SELECT)

        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_SELECT)

        index = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_SELECT)

        verify_intrinsic_type_int(index, IntrinsicResolver.FN_SELECT)

        list_of_objects = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_SELECT)
        verify_intrinsic_type_list(list_of_objects, IntrinsicResolver.FN_SELECT)

        sanitized_objects = [self.intrinsic_property_resolver(item, parent_function=IntrinsicResolver.FN_SELECT) for
                             item in
                             list_of_objects]

        verify_in_bounds(index=index, objects=sanitized_objects, property_type=IntrinsicResolver.FN_SELECT)

        return sanitized_objects[index]

    def handle_find_in_map(self, intrinsic_value):
        """
        { "Fn::FindInMap" : [ "MapName", "TopLevelKey", "SecondLevelKey"] } This function will then lookup the
        specified dictionary in the Mappings dictionary as mappings[map_name][top_level_key][second_level_key].

        This intrinsic function will resolve all the objects within the function's value and check their type.

        The format of the Mappings dictionary is:
        "Mappings": {
            "map_name": {
                "top_level_key": {
                    "second_level_key": "value"
                    }
                }
            }
        }
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::FindInMap intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_FIND_IN_MAP)

        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_FIND_IN_MAP)

        verify_number_arguments(arguments, num=3, property_type=IntrinsicResolver.FN_FIND_IN_MAP)

        map_name = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_FIND_IN_MAP)
        top_level_key = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_FIND_IN_MAP)
        second_level_key = self.intrinsic_property_resolver(arguments[2],
                                                            parent_function=IntrinsicResolver.FN_FIND_IN_MAP)

        verify_intrinsic_type_str(map_name, IntrinsicResolver.FN_FIND_IN_MAP, position_in_list="first")
        verify_intrinsic_type_str(top_level_key, IntrinsicResolver.FN_FIND_IN_MAP, position_in_list="second")
        verify_intrinsic_type_str(second_level_key, IntrinsicResolver.FN_FIND_IN_MAP, position_in_list="third")

        map_value = self.mapping.get(map_name)
        verify_intrinsic_type_dict(map_value, IntrinsicResolver.FN_FIND_IN_MAP, position_in_list="first",
                                   message="The MapName is missing in the Mappings dictionary in Fn::FindInMap  for {}"
                                   .format(map_name))

        top_level_value = map_value.get(top_level_key)
        verify_intrinsic_type_dict(top_level_value, IntrinsicResolver.FN_FIND_IN_MAP,
                                   message="The TopLevelKey is missing in the Mappings dictionary in Fn::FindInMap "
                                           "for {}".format(top_level_key))

        second_level_value = top_level_value.get(second_level_key)
        verify_intrinsic_type_str(second_level_value, IntrinsicResolver.FN_FIND_IN_MAP,
                                  message="The SecondLevelKey is missing in the Mappings dictionary in Fn::FindInMap  "
                                          "for {}".format(second_level_key))

        return second_level_value

    def handle_fn_get_azs(self, intrinsic_value):
        """
        { "Fn::GetAZs" : "" }
        { "Fn::GetAZs" : { "Ref" : "AWS::Region" } }
        { "Fn::GetAZs" : "us-east-1" }
        This intrinsic function will get the availability zones specified for the specified region. This is usually used
        with {"Ref": "AWS::Region"}. If it is an empty string, it will get the default region.

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::GetAZs intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        intrinsic_value = self.intrinsic_property_resolver(intrinsic_value,
                                                           parent_function=IntrinsicResolver.FN_GET_AZS)
        verify_intrinsic_type_str(intrinsic_value, IntrinsicResolver.FN_GET_AZS)

        if intrinsic_value == "":
            intrinsic_value = self.symbol_resolver.DEFAULT_REGION

        if intrinsic_value not in self.symbol_resolver.REGIONS:
            raise InvalidIntrinsicException(
                "Invalid region string passed in to {}".format(IntrinsicResolver.FN_GET_AZS))

        return self.symbol_resolver.REGIONS.get(intrinsic_value)

    def handle_fn_transform(self, intrinsic_value):
        """
        { "Fn::Transform" : { "Name" : macro name, "Parameters" : {key : value, ... } } }
        This intrinsic function will transform the data with the body provided

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Transform intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        macro_name = intrinsic_value.get("Name")
        name = self.intrinsic_property_resolver(macro_name, parent_function=IntrinsicResolver.FN_TRANSFORM)

        if name not in IntrinsicResolver.SUPPORTED_MACRO_TRANSFORMATIONS:
            raise InvalidIntrinsicException(
                "The type {} is not currently supported in {}".format(name, IntrinsicResolver.FN_TRANSFORM))

        if name == IntrinsicResolver.AWS_INCLUDE:
            parameters = intrinsic_value.get("Parameters")
            verify_intrinsic_type_dict(parameters, IntrinsicResolver.FN_TRANSFORM,
                                       message=" Fn::Transform requires parameters section")

            location = self.intrinsic_property_resolver(parameters.get("Location"))
            return location

    def handle_fn_import_value(self, intrinsic_value):
        """
        { "Fn::ImportValue" : sharedValueToImport }
        This intrinsic function requires handling multiple stacks, which is not currently supported by SAM-CLI.
        Thus, it will thrown an exception.

        Return
        -------
        An InvalidIntrinsicException
        """
        raise InvalidIntrinsicException("Fn::ImportValue is currently not supported by IntrinsicResolver")

    def handle_fn_getatt(self, intrinsic_value):
        """
        { "Fn::GetAtt" : [ "logicalNameOfResource", "attributeName" ] }
        This intrinsic function gets the attribute for logical_resource specified. Each attribute might have a different
        functionality depending on the type.

        This intrinsic function will resolve all the objects within the function's value and check their type.
        This calls the symbol resolver in order to resolve the relevant attribute.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::GetAtt intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_GET_ATT)
        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_GET_ATT)
        verify_number_arguments(arguments, IntrinsicResolver.FN_GET_ATT, num=2)

        logical_id = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_GET_ATT)
        resource_type = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_GET_ATT)

        verify_intrinsic_type_str(logical_id, IntrinsicResolver.FN_GET_ATT)
        verify_intrinsic_type_str(resource_type, IntrinsicResolver.FN_GET_ATT)

        return self.symbol_resolver.resolve_symbols(logical_id, resource_type)

    def handle_fn_ref(self, intrinsic_value):
        """
        {"Ref": "Logical ID"}
        This intrinsic function gets the reference to a certain attribute. Some Ref's have different functionality with
        different resource types.

        This intrinsic function will resolve all the objects within the function's value and check their type.
        This calls the symbol resolver in order to resolve the relevant attribute.
        Parameter
        ----------
        intrinsic_value: str
           This is the value of the object inside the Ref intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.REF)
        verify_intrinsic_type_str(arguments, IntrinsicResolver.REF)

        return self.symbol_resolver.resolve_symbols(arguments, IntrinsicResolver.REF)

    def handle_fn_sub(self, intrinsic_value):
        """
        { "Fn::Sub" : [ String, { Var1Name: Var1Value, Var2Name: Var2Value } ] } or { "Fn::Sub" : String }
        This intrinsic function will substitute the variables specified in the list into the string provided. The string
        will also parse out pseudo properties and anything of the form ${}.

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        A string with the resolved attributes
        """

        def resolve_sub_attribute(intrinsic_item, symbol_resolver):
            if "." in intrinsic_item:
                (logical_id, attribute_type) = intrinsic_item.rsplit('.', 1)
            else:
                (logical_id, attribute_type) = intrinsic_item, IntrinsicResolver.REF
            return symbol_resolver.resolve_symbols(logical_id, attribute_type, ignore_errors=True)

        if isinstance(intrinsic_value, string_types):
            intrinsic_value = [intrinsic_value, {}]

        verify_intrinsic_type_list(intrinsic_value, IntrinsicResolver.FN_SUB,
                                   message="The arguments to a Fn::Sub must be a list or a string")

        verify_number_arguments(intrinsic_value, IntrinsicResolver.FN_SUB, num=2)

        sub_str = self.intrinsic_property_resolver(intrinsic_value[0], parent_function=IntrinsicResolver.FN_SUB)
        verify_intrinsic_type_str(sub_str, IntrinsicResolver.FN_SUB, position_in_list="first")

        variables = intrinsic_value[1]
        verify_intrinsic_type_dict(variables, IntrinsicResolver.FN_SUB, position_in_list="second")

        sanitized_variables = self.intrinsic_property_resolver(variables, parent_function=IntrinsicResolver.FN_SUB)

        subable_props = re.findall(string=sub_str, pattern=IntrinsicResolver._REGEX_SUB_FUNCTION)
        for sub_item in subable_props:
            sanitized_item = sanitized_variables[sub_item] if sub_item in sanitized_variables else sub_item
            result = resolve_sub_attribute(sanitized_item, self.symbol_resolver)
            sub_str = re.sub(pattern=r"\$\{" + sub_item + r"\}", string=sub_str, repl=result)
        return sub_str

    def handle_fn_if(self, intrinsic_value):
        """
        {"Fn::If": [condition_name, value_if_true, value_if_false]}
        This intrinsic function will evaluate the condition from the Conditions dictionary and then return value_if_true
        or value_if_false depending on the value.

        The Conditions dictionary will have the following format:
        {
            "Conditions": {
                "condition_name": True/False or "{Intrinsic Function}"
            }
        }

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        This will return value_if_true and value_if_false depending on how the condition is evaluated
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_IF)
        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_IF)
        verify_number_arguments(arguments, IntrinsicResolver.FN_IF, num=3)

        condition_name = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_IF)
        verify_intrinsic_type_str(condition_name, IntrinsicResolver.FN_IF)

        value_if_true = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_IF)
        value_if_false = self.intrinsic_property_resolver(arguments[2], parent_function=IntrinsicResolver.FN_IF)

        condition = self.conditions.get(condition_name)
        verify_intrinsic_type_dict(condition, IntrinsicResolver.FN_IF,
                                   message="The condition is missing in the Conditions dictionary for {}".format(
                                       IntrinsicResolver.FN_IF))

        condition_evaluated = self.intrinsic_property_resolver(condition, parent_function=IntrinsicResolver.FN_IF)
        verify_intrinsic_type_bool(condition_evaluated, IntrinsicResolver.FN_IF,
                                   message="The result of {} must evaluate to bool".format(IntrinsicResolver.FN_IF))

        return value_if_true if condition_evaluated else value_if_false

    def handle_fn_equals(self, intrinsic_value):
        """
        {"Fn::Equals" : ["value_1", "value_2"]}
        This intrinsic function will verify that both items in the intrinsic function are equal after resolving them.

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        A boolean depending on if both arguments is equal
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_EQUALS)
        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_EQUALS)
        verify_number_arguments(arguments, IntrinsicResolver.FN_EQUALS, num=2)

        value_1 = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_EQUALS)
        value_2 = self.intrinsic_property_resolver(arguments[1], parent_function=IntrinsicResolver.FN_EQUALS)
        return value_1 == value_2

    def handle_fn_not(self, intrinsic_value):
        """
        {"Fn::Not": [{condition}]}
        This intrinsic function will negate the evaluation of the condition specified.

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        A boolean that is the opposite of the condition evaluated
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_NOT)
        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_NOT)
        verify_number_arguments(arguments, IntrinsicResolver.FN_NOT, num=1)
        argument_sanitised = self.intrinsic_property_resolver(arguments[0], parent_function=IntrinsicResolver.FN_NOT)
        if isinstance(argument_sanitised, dict) and "Condition" in arguments[0]:
            condition_name = argument_sanitised.get("Condition")
            verify_intrinsic_type_str(condition_name, IntrinsicResolver.FN_NOT)

            condition = self.conditions.get(condition_name)
            verify_non_null(condition, IntrinsicResolver.FN_NOT, position_in_list="first")

            argument_sanitised = self.intrinsic_property_resolver(condition, parent_function=IntrinsicResolver.FN_NOT)

        verify_intrinsic_type_bool(argument_sanitised, IntrinsicResolver.FN_NOT,
                                   message="The result of {} must evaluate to bool".format(
                                       IntrinsicResolver.FN_NOT))
        return not argument_sanitised

    def handle_fn_and(self, intrinsic_value):
        """
        {"Fn::And": [{condition}, {...}]}
        This intrinsic checks that every item in the list evaluates to a boolean. The items in the list can either
        be of the format {Condition: condition_name} which finds and evaluates the Conditions dictionary of another
        intrinsic function.

        The Conditions dictionary will have the following format:
        {
            "Conditions": {
                "condition_name": True/False or "{Intrinsic Function}"
            }
        }

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        A boolean depending on if all of the properties in Fn::And evaluate to True
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_AND)
        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_AND)

        for i, argument in enumerate(arguments):
            if isinstance(argument, dict) and "Condition" in argument:
                condition_name = argument.get("Condition")
                verify_intrinsic_type_str(condition_name, IntrinsicResolver.FN_AND)

                condition = self.conditions.get(condition_name)
                verify_non_null(condition, IntrinsicResolver.FN_AND, position_in_list="{} th".format(str(i)))

                condition_evaluated = self.intrinsic_property_resolver(condition,
                                                                       parent_function=IntrinsicResolver.FN_AND)
                verify_intrinsic_type_bool(condition_evaluated, IntrinsicResolver.FN_AND)

                if not condition_evaluated:
                    return False
            else:
                condition = self.intrinsic_property_resolver(argument, parent_function=IntrinsicResolver.FN_AND)
                verify_intrinsic_type_bool(condition, IntrinsicResolver.FN_AND)

                if not condition:
                    return False

        return True

    def handle_fn_or(self, intrinsic_value):
        """
        {"Fn::Or": [{condition}, {...}]}
        This intrinsic checks that a single item in the list evaluates to a boolean. The items in the list can either
        be of the format {Condition: condition_name} which finds and evaluates the Conditions dictionary of another
        intrinsic function.

        The Conditions dictionary will have the following format:
        {
            "Conditions": {
                "condition_name": True/False or "{Intrinsic Function}"
            }
        }

        This intrinsic function will resolve all the objects within the function's value and check their type.
        Parameter
        ----------
        intrinsic_value: list, dict
           This is the value of the object inside the Fn::Join intrinsic function property

        Return
        -------
        A boolean depending on if any of the properties in Fn::And evaluate to True
        """
        arguments = self.intrinsic_property_resolver(intrinsic_value, parent_function=IntrinsicResolver.FN_OR)
        verify_intrinsic_type_list(arguments, IntrinsicResolver.FN_OR)

        for i, argument in enumerate(arguments):
            if isinstance(argument, dict) and "Condition" in argument:
                condition_name = argument.get("Condition")
                verify_intrinsic_type_str(condition_name, IntrinsicResolver.FN_OR)

                condition = self.conditions.get(condition_name)
                verify_non_null(condition, IntrinsicResolver.FN_OR, position_in_list="{} th".format(str(i)))

                condition_evaluated = self.intrinsic_property_resolver(condition,
                                                                       parent_function=IntrinsicResolver.FN_OR)
                verify_intrinsic_type_bool(condition_evaluated, IntrinsicResolver.FN_OR)

                if condition_evaluated:
                    return True
            else:
                condition = self.intrinsic_property_resolver(argument, parent_function=IntrinsicResolver.FN_OR)
                verify_intrinsic_type_bool(condition, IntrinsicResolver.FN_OR)

                if condition:
                    return True

        return False
