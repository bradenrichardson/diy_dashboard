import os
from aws_cdk import App, Environment


from Base import Base
from Pipeline import Pipeline

props = {'namespace': 'diy-dashboard-test'}
app = App()

# stack for ecr, bucket, codebuild
base = Base(app, f"{props['namespace']}-base", props, env=Environment(account="007576465237", region="ap-southeast-2"))

# pipeline stack
pipeline = Pipeline(app, f"{props['namespace']}-pipeline", base.outputs, env=Environment(account="007576465237", region="ap-southeast-2"))

pipeline.add_dependency(base)

app.synth()