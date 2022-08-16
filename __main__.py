"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import secretsmanager
from aws import setup_s3_buckets, setup_api_gateway
from heroku import setup_heroku_resources

bucket_ids = setup_s3_buckets()
secrets = secretsmanager.get_secret_version("playground/Env/Config")
app = setup_heroku_resources(secrets)
target = pulumi.Output.concat("https://", app.heroku_hostname)
api_gateway = setup_api_gateway(target)

pulumi.export("bucket_names", bucket_ids)
pulumi.export("api-hostname", api_gateway.api_endpoint)
pulumi.export("heroku-hostname", app.heroku_hostname)
