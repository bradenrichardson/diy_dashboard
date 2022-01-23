from typing_extensions import runtime
import json
from aws_cdk import (
    aws_apigatewayv2,
    core as cdk,
    aws_lambda as _lambda,
    aws_dynamodb as _dynamo,
    aws_ssm as _ssm,
    aws_codecommit as _codecommit,
    aws_codepipeline as _codepipeline,
    aws_codepipeline_actions as _actions_codepipeline,
    aws_s3 as _s3
    
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

        api.add_stage('webhook', auto_deploy=True)

        api.add_routes(
            path="/diy_dashboard_webhook",
            methods=[aws_apigatewayv2.HttpMethod.POST],
            integration=process_webhook_integration
        )

        api_invoke_url = _ssm.CfnParameter(self, 'api_invoke_url',
            type='string',
            value=api.url
            )

        repo = _codecommit.CfnRepository(self, 'diy_dashboard_repo',
            repository_name='diy_dashboard_repo')


        artifact_bucket = _s3.Bucket(self, 'artifact_store')
        
        source_output = _codepipeline.Artifact("SourceArtifact")



        # pipeline_source = _actions_codepipeline.CodeCommitSourceAction(
        #     action_name="Source",
        #     repository=repo,
        #     output=source_output,
        #     trigger=_actions_codepipeline.CodeCommitTrigger.POLL
        # )

        # pipeline_compute = _actions_codepipeline.LambdaInvokeAction(
        #     action_name="Lambda Compute",
        #     inputs=[source_output
        #     ],
        #     outputs=[
        #         _codepipeline.Artifact("Out1"),
        #         _codepipeline.Artifact("Out2")
        #     ],
        #     lambda_=diy_dashboard_compute
        # )

        # pipeline = _codepipeline.Pipeline(self, "diy_dashboard_pipeline",
        #     pipeline_name="diy_dashboard_pipeline"
        # )

        # source_stage = pipeline.add_stage(stage_name="Source",
        #     actions=[pipeline_source])

        # compute_stage = pipeline.add_stage(stage_name="Compute",
        #     actions=[pipeline_compute])



        print('\nGithub Clone URL: {}\n'.format(repo.attr_clone_url_http))
        

