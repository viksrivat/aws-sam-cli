"""Parses SAM given a template"""
import logging

from samcli.commands.local.lib.cfn_base_api_provider import CfnBaseApiProvider

LOG = logging.getLogger(__name__)


class CfnApiProvider(CfnBaseApiProvider):
    APIGATEWAY_RESTAPI = "AWS::ApiGateway::RestApi"
    APIGATEWAY_STAGE = "AWS::ApiGateway::Stage"
    TYPES = [
        APIGATEWAY_RESTAPI,
        APIGATEWAY_STAGE
    ]

    def extract_resources(self, resources, collector, api, cwd=None):
        """
        Extract the Route Object from a given resource and adds it to the RouteCollector.

        Parameters
        ----------
        resources: dict
            The dictionary containing the different resources within the template

        collector: samcli.commands.local.lib.route_collector.RouteCollector
            Instance of the API collector that where we will save the API information

        api: samcli.commands.local.lib.provider.Api
            Instance of the Api which will save all the api configurations
        cwd : str
            Optional working directory with respect to which we will resolve relative path to Swagger file

        Return
        -------
        Returns a list of routes
        """
        for logical_id, resource in resources.items():
            resource_type = resource.get(CfnBaseApiProvider.RESOURCE_TYPE)
            if resource_type == CfnApiProvider.APIGATEWAY_RESTAPI:
                self._extract_cloud_formation_route(logical_id, resource, collector, api=api, cwd=cwd)

            if resource_type == CfnApiProvider.APIGATEWAY_STAGE:
                self._extract_cloud_formation_stage(resource, api)

        all_routes = []
        for _, routes in collector:
            all_routes.extend(routes)
        return all_routes

    def _extract_cloud_formation_route(self, logical_id, api_resource, collector, api, cwd=None):
        """
        Extract APIs from AWS::ApiGateway::RestApi resource by reading and parsing Swagger documents. The result is
        added to the collector.

        Parameters
        ----------
        logical_id : str
            Logical ID of the resource

        api_resource : dict
            Resource definition, including its properties

        collector : ApiCollector
            Instance of the API collector that where we will save the API information
        """
        properties = api_resource.get("Properties", {})
        body = properties.get("Body")
        body_s3_location = properties.get("BodyS3Location")
        binary_media = properties.get("BinaryMediaTypes", [])

        if not body and not body_s3_location:
            # Swagger is not found anywhere.
            LOG.debug("Skipping resource '%s'. Swagger document not found in Body and BodyS3Location",
                      logical_id)
            return
        self.extract_swagger_route(logical_id, body, body_s3_location, binary_media, collector, api, cwd)

    @staticmethod
    def _extract_cloud_formation_stage(stage_resource, api):
        """
        Extract the stage from AWS::ApiGateway::Stage resource by reading and adds it to the collector.
        Parameters
       ----------
        stage_resource : dict
            Stage Resource definition, including its properties
        api: samcli.commands.local.lib.provider.Api
            Resource definition, including its properties
        """
        properties = stage_resource.get("Properties", {})
        stage_name = properties.get("StageName")
        stage_variables = properties.get("Variables")
        logical_id = properties.get("RestApiId")
        if logical_id:
            api.stage_name = stage_name
            api.stage_variables = stage_variables