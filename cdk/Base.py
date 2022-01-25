from typing_extensions import runtime
from webbrowser import get
from aws_cdk import (
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_s3,
    aws_dynamodb as _dynamo,
    aws_ssm as _ssm,
    aws_codecommit as _codecommit,
    aws_ecs as _ecs,
    aws_ec2 as _ec2,
    aws_ecs_patterns as _ecs_patterns,
    App, Stack, CfnOutput
    
)


from aws_cdk.aws_apigatewayv2_integrations_alpha import HttpLambdaIntegration
import aws_cdk.aws_apigatewayv2_alpha as _apigateway

class Base(Stack):

    def __init__(self, app: App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)
        
        vpc = _ec2.Vpc(self, "diy_dashboard_vpc")

        bucket = aws_s3.Bucket(
            self, "SourceBucket",
            removal_policy=RemovalPolicy.DESTROY
        )

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
        

        get_events = _lambda.Function(self, "diy_dashboard_get_events",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.handler',
            code= _lambda.Code.from_asset('lambdas\get_events'),
            layers=[requests_layer]
        )

        calendar_dynamodb.grant_read_write_data(get_events)


        api = _apigateway.HttpApi(self, "diy_dashboard_HttpApi", create_default_stage=False)

        api_stage = _apigateway.HttpStage(self, "Stage",
            http_api=api,
            stage_name="diy_dashboard_webhook"
        )

        api_invoke_url = _ssm.CfnParameter(self, 'api_invoke_url',
            type='String',
            value=api_stage.url
            )



        
        cluster = _ecs.Cluster(self, "diy_dashboard_fargate_cluster",
            vpc=vpc
        )

        load_balanced_ecs_service = _ecs_patterns.NetworkLoadBalancedFargateService(self, "diy_dashboard_service",
            cluster=cluster,
            memory_limit_mib=512,
            cpu=256,
            task_image_options=_ecs_patterns.NetworkLoadBalancedTaskImageOptions(
                image=_ecs.ContainerImage.from_asset(".")
            )

        )

        up_dynamodb.grant_read_write_data(load_balanced_ecs_service.task_definition.task_role)



        
        
        self.output_props = props.copy()
        self.output_props['lambda'] = get_events
        self.output_props['bucket'] = bucket

    @property
    def outputs(self):
        return self.output_props



