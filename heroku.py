import json
import re
from pulumi_heroku import (
    HerokuApp,
    HerokuAppOrganizationArgs,
    HerokuAddon,
    HerokuAppConfigAssociation,
)


def setup_heroku_resources(secrets):
    app = HerokuApp(
        "app",
        name="noipm-playground",
        region="us",
        organization=HerokuAppOrganizationArgs(name="noipm"),
        sensitive_config_vars=json.loads(secrets.secret_string),
    )

    postgres = HerokuAddon(
        "postgres_addon",
        app=app.name,
        plan="heroku-postgresql:hobby-dev",
        name="noipm-playground-postgres-addon",
    )

    scheduler = HerokuAddon(
        "scheduler_addon",
        app=app.name,
        plan="scheduler:standard",
        name="noipm-playground-scheduler-addon",
    )

    redis = HerokuAddon(
        "redis_addon",
        app=app.name,
        plan="rediscloud:30",
        name="noipm-playground-redis-addon",
    )

    papertrail = HerokuAddon(
        "papertrail_addon",
        app=app.name,
        plan="papertrail:choklad",
        name="noipm-playground-papertrail-addon",
    )

    db_vars = postgres.config_var_values.apply(get_database_vars)

    db_details = HerokuAppConfigAssociation(
        "database_details",
        app_id=app.id,
        sensitive_vars=db_vars,
    )

    return app


def get_database_vars(config_vars):
    db_match = re.search(
        r"://(\w+):(\w+)@([\w\-.]+):\d+/(\w+)", config_vars["DATABASE_URL"]
    )

    return {
        "DATABASE_USERNAME": db_match.group(1),
        "DATABASE_PASS": db_match.group(2),
        "DATABASE_HOST": db_match.group(3),
        "DATABASE_NAME": db_match.group(4),
    }
