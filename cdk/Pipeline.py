from asyncore import poll
from os import pipe
from aws_cdk import (
    aws_codepipeline,
    aws_codepipeline_actions,
    aws_codecommit,
    App, Stack
)


class Pipeline(Stack):
    def __init__(self, app: App, id: str, props, **kwargs) -> None:
        super().__init__(app, id, **kwargs)
        

        source_output = aws_codepipeline.Artifact(artifact_name="Source")

        repo = aws_codecommit.Repository(self, 'diy_dashboard_repo',
            repository_name='diy_dashboard_repo',
            code=aws_codecommit.Code.from_directory('repo', "master"))

        pipeline = aws_codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name = "diy_dashboard_pipeline",
            artifact_bucket=props['bucket'],
            stages=[
                aws_codepipeline.StageProps(
                    stage_name='Source',
                    actions=[
                        aws_codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit",
                            repository=repo,
                            output=source_output,
                            trigger=aws_codepipeline_actions.CodeCommitTrigger.EVENTS
                        )
                    ]
                ),
                aws_codepipeline.StageProps(
                    stage_name="Compute",
                    actions=[
                        aws_codepipeline_actions.LambdaInvokeAction(
                            action_name="Lambda",
                            inputs=[source_output],
                            outputs=[],
                            lambda_=props['lambda']
                        )
                    ]
                )
            ]
        )

        # github_output = CfnOutput(self, 'Github Clone URL',
        #     value=repo.attr_clone_url_http,
        #     description='Clone this URL'
        # )