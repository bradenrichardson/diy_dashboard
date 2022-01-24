from asyncio import tasks
from typing_extensions import runtime
import json
from webbrowser import get
from aws_cdk import (
    aws_apigatewayv2,
    core as cdk,
    aws_lambda as _lambda,
    aws_dynamodb as _dynamo,
    aws_ssm as _ssm,
    aws_codecommit as _codecommit,
    aws_codepipeline as _codepipeline,
    aws_codepipeline_actions as _actions_codepipeline,
    aws_s3 as _s3,
    aws_ecs as _ecs,
    aws_ec2 as _ec2,
    aws_ecs_patterns as _ecs_patterns
    
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
import pip

class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        vpc = _ec2.Vpc(self, "diy_dashboard_vpc")

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


        api = aws_apigatewayv2.HttpApi(self, "diy_dashboard_HttpApi", create_default_stage=False)

        api_stage = aws_apigatewayv2.HttpStage(self, "Stage",
            http_api=api,
            stage_name="diy_dashboard_webhook"
        )

        api_invoke_url = _ssm.CfnParameter(self, 'api_invoke_url',
            type='String',
            value=api_stage.url
            )

        repo = _codecommit.CfnRepository(self, 'diy_dashboard_repo',
            repository_name='diy_dashboard_repo')

        
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

        source_output = _codepipeline.Artifact()
        
        source_action = _actions_codepipeline.CodeCommitSourceAction(
            action_name="CodeCommit",
            repository=repo,
            output=source_output
        )


        compute_action = _actions_codepipeline.LambdaInvokeAction(
            action_name="Lambda",
            inputs=[source_output],
            outputs=[],
            lambda_=get_events
        )


        

        pipeline = _codepipeline.Pipeline(self, "diy_dasboard_pipeline",
            pipeline_name='diy_dashboard_pipeline',
            cross_account_keys=False)

        pipeline.node.add_dependency(get_events)

        source_stage = pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        



        compute_stage = pipeline.add_stage(
            stage_name="Compute",
            actions=[compute_action]
        )

        
    



        github_output = cdk.CfnOutput(self, 'Github Clone URL',
            value=repo.attr_clone_url_http,
            description='Clone this URL'
        )
            

