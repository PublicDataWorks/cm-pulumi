from pulumi import Output
import json
import constants


def construct_bucket_object_policy(bucket_id):
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyIncorrectEncryptionHeader",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_id}/*",
                    "Condition": {
                        "StringNotEquals": {
                            "s3:x-amz-server-side-encryption": constants.ENCRYPTION
                        }
                    },
                },
                {
                    "Sid": "DenyUnEncryptedObjectUploads",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_id}/*",
                    "Condition": {"Null": {"s3:x-amz-server-side-encryption": "true"}},
                },
                {
                    "Sid": "DenyUnSecureCommunications",
                    "Effect": "Deny",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:*",
                    "Resource": f"arn:aws:s3:::{bucket_id}/*",
                    "Condition": {"Bool": {"aws:SecureTransport": "false"}},
                },
            ],
        }
    )


def construct_bucket_access_policy_all_buckets(bucket_arns):
    policy = Output.concat('{"Version": "2012-10-17", "Statement": [')
    first = True
    for bucket_name in bucket_arns:
        if not first:
            policy = Output.concat(policy, ", ")
        policy = Output.concat(
            policy,
            construct_allow_listing_bucket_policy(
                bucket_name, bucket_arns[bucket_name]
            ),
        )
        policy = Output.concat(policy, ", ")
        policy = Output.concat(
            policy,
            construct_allow_crud_bucket_policy(bucket_name, bucket_arns[bucket_name]),
        )
        first = False

    policy = Output.concat(policy, "]}")
    return policy


def construct_allow_listing_bucket_policy(bucket_name, bucket_arn):
    return Output.concat(
        '{"Sid": "AllowListingBucket',
        bucket_name,
        '", "Effect": "Allow", "Action": ["s3:ListBucket", "s3:GetBucketLocation"], "Resource": "',
        bucket_arn,
        '" }',
    )


def construct_allow_crud_bucket_policy(bucket_name, bucket_arn):
    return Output.concat(
        '{"Sid": "AllowBucketContentCRUD',
        bucket_name,
        '", "Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObjectAcl", "s3:GetObject", "s3:DeleteObject", "s3:PutObjectAcl"], "Resource": "',
        bucket_arn,
        '" }',
    )
