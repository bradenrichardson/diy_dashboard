from typing_extensions import runtime
import json
from aws_cdk import (
    aws_apigatewayv2,
    core as cdk,
    aws_lambda as _lambda,
    aws_dynamodb as _dynamo,
    aws_iam as _iam,
    aws_s3 as _s3,
    aws_athena as _athena,
    aws_sam as _sam,
    aws_secretsmanager as _secrets
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration



class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        up_dynamodb = _dynamo.Table(self, 'diy_dashboard_up',
            partition_key=_dynamo.Attribute(name='TransactionID', type=_dynamo.AttributeType.STRING) 
        )

        calendar_dynamodb = _dynamo.Table(self, 'diy_dashboard_calendar',
            partition_key=_dynamo.Attribute(name='id', type=_dynamo.AttributeType.STRING)
        )


        requests_layer = _lambda.LayerVersion(self, 'requests_layer',
            code=_lambda.Code.from_asset('layers\_requests'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            compatible_architectures=[_lambda.Architecture.X86_64],
            description='A layer to send API requests'
        )
        
        diy_dashboard_compute = _lambda.Function(self, "diy_dashboard_compute",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.handler',
            code= _lambda.Code.from_asset('lambdas\diy_dashboard_compute'),
            layers=[requests_layer]
        )

        get_events = _lambda.Function(self, "diy_dashboard_get_events",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.handler',
            code= _lambda.Code.from_asset('lambdas\get_events'),
            layers=[requests_layer]
        )


        up_dynamodb.grant_read_write_data(diy_dashboard_compute)

        calendar_dynamodb.grant_read_write_data(get_events)

        process_webhook_integration = HttpLambdaIntegration("Process Webhook Integration", diy_dashboard_compute)

        api = aws_apigatewayv2.HttpApi(self, "diy_dashboard_HttpApi")

        api.add_routes(
            path="/diy_dashboard_webhook",
            methods=[aws_apigatewayv2.HttpMethod.POST],
            integration=process_webhook_integration
        )

        with open('./secrets.json', 'r') as secrets:
            data = json.load(secrets)
            for key in data:
                _secrets.CfnSecret(self, key, secret_string=data[key])

