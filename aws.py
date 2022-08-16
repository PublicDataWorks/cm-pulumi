from pulumi_aws import s3, iam, apigatewayv2
import constants
from policies import (
    construct_bucket_object_policy,
    construct_bucket_access_policy_all_buckets,
)


def setup_s3_buckets():
    bucket_names = {
        "s3Bucket": "noipm-playground",
        "officerBucket": "nopd-officers-playground",
        "complainantLettersBucket": "noipm-complainant-letters-playground",
        "referralLettersBucket": "noipm-referral-letters-playground",
    }
    bucket_ids = {}
    bucket_arns = {}

    for bucket_key in bucket_names:
        # Create an AWS resource (S3 Bucket)
        bucket = s3.Bucket(
            bucket_names[bucket_key],
            acl="private",
            server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
                rule=s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm=constants.ENCRYPTION
                    )
                )
            ),
        )
        bucket_ids[bucket_key] = bucket.id
        bucket_arns[bucket_key] = bucket.arn

    export_bucket = s3.Bucket(
        "noipm-exports-playground",
        acl="private",
        server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
            rule=s3.BucketServerSideEncryptionConfigurationRuleArgs(
                apply_server_side_encryption_by_default=s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm=constants.ENCRYPTION
                )
            )
        ),
        lifecycle_rules=[
            s3.BucketLifecycleRuleArgs(
                abort_incomplete_multipart_upload_days=0,
                enabled=True,
                id="Delete old exports",
                tags={},
                expiration=s3.BucketLifecycleRuleExpirationArgs(
                    days=1, expired_object_delete_marker=False
                ),
                noncurrent_version_expiration=s3.BucketLifecycleRuleNoncurrentVersionExpirationArgs(
                    days=1
                ),
            )
        ],
    )
    bucket_ids["exportsBucket"] = export_bucket.id
    bucket_arns["exportsBucket"] = export_bucket.arn

    signatures_folder = s3.BucketObjectv2(
        "signatures",
        bucket=bucket_ids["s3Bucket"],
        key="signatures/",
        source="/dev/null",
        server_side_encryption=constants.ENCRYPTION,
    )

    letter_images_folder = s3.BucketObjectv2(
        "letter-images",
        bucket=bucket_ids["s3Bucket"],
        key="letter-images/",
        source="/dev/null",
        server_side_encryption=constants.ENCRYPTION,
    )

    for bucket_key in bucket_ids:
        policy_name = bucket_key + "-bucketPolicy"
        bucket_policy = s3.BucketPolicy(
            policy_name,
            bucket=bucket_ids[bucket_key],
            policy=bucket_ids[bucket_key].apply(construct_bucket_object_policy),
        )

    bucket_access_policy = iam.Policy(
        "bucket_access_policy",
        name="noipm-playground-bucket-access",
        description="A policy to allow bucket listing and CRUD on bucket contents",
        policy=construct_bucket_access_policy_all_buckets(bucket_arns),
    )

    bucket_access_policy_attachment = iam.PolicyAttachment(
        "attach_policy",
        name="playground-policy-group-attachment",
        policy_arn=bucket_access_policy.arn,
        groups=["developer"],
        roles=[],
    )

    env_user = iam.User("env_user", name="noipm-playground")
    env_user_access_key = iam.AccessKey("env_user_access_key", user=env_user.name)
    env_user_group = iam.UserGroupMembership(
        "env_user_group", user=env_user.name, groups=["developer"]
    )

    return bucket_ids


def setup_api_gateway(target):
    return apigatewayv2.Api(
        "api_gateway",
        name="noipm-playground-http-api",
        protocol_type="HTTP",
        target=target,
        cors_configuration=apigatewayv2.ApiCorsConfigurationArgs(
            allow_origins=[target],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
            max_age=7200,
        ),
    )
