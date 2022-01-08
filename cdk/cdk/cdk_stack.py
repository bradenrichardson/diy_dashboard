from typing_extensions import runtime
from aws_cdk import (
    aws_apigatewayv2,
    core as cdk,
    aws_lambda as _lambda,
    aws_dynamodb as _dynamo,
    aws_iam as _iam,
    aws_s3 as _s3,
    aws_athena as _athena,
    aws_sam as _sam
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration


# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core




class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        dynamodb = _dynamo.Table(self, 'cdk_test',
            partition_key=_dynamo.Attribute(name='TransactionID', type=_dynamo.AttributeType.STRING) 
        )

        requests_layer = _lambda.LayerVersion(self, 'requests_layer',
            code=_lambda.Code.from_asset('layers\_requests'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            compatible_architectures=[_lambda.Architecture.X86_64],
            description='A layer to send API requests'
        )
        
        process_webhook = _lambda.Function(self, 'process_webhook', 
            runtime=_lambda.Runtime.PYTHON_3_9, 
            handler='lambda_function.handler',
            code= _lambda.Code.from_asset('lambdas\process_webhook'),
            layers=[requests_layer]
            )
        
        provision_user = _lambda.Function(self, "provision_user",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.handler',
            code= _lambda.Code.from_asset('lambdas\provision_user'),
            layers=[requests_layer]
        )

        get_events = _lambda.Function(self, "get_events",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.handler',
            code= _lambda.Code.from_asset('lambdas\get_events'),
            layers=[requests_layer]
        )

        dynamodb.grant_read_write_data(process_webhook)

        dynamodb.grant_read_write_data(provision_user)

        dynamodb.grant_read_write_data(get_events)

        process_webhook_integration = HttpLambdaIntegration("Process Webhook Integration", process_webhook)

        api = aws_apigatewayv2.HttpApi(self, "HttpApi")

        api.add_routes(
            path="/webhook",
            methods=[aws_apigatewayv2.HttpMethod.POST],
            integration=process_webhook_integration
        )

