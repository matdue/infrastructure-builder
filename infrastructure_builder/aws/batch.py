import logging
import re
from datetime import datetime, timezone, timedelta
from functools import cached_property
from time import sleep

import boto3

from infrastructure_builder.aws.exceptions import BuilderError
from infrastructure_builder.aws.service_base import ServiceBase


class Batch(ServiceBase):
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        return self.session.client("batch", region_name=self.region)

    def submit_job(self, job_name: str, job_queue: str, job_definition: str,
                   timeout=15, wait_until_completed=True) -> str:
        """
        Submits an AWS Batch Job.

        :param job_name: The name of the job.
        :param job_queue: The queue where the job will be put into.
        :param job_definition: The definition of the job.
        :param timeout: The maximum time to wait for the job to finish (in minutes). If the job takes more time, an
            BuilderError exception will be raised. The job will continue to run, it will not be aborted!
        :param wait_until_completed: If False, this method will return immediately after submit, else will wait until
            the job has finished or the timeout has been reached.
        :return: Job ID
        """
        submitted_job = self.client.submit_job(jobName=job_name, jobQueue=job_queue, jobDefinition=job_definition)
        job_id = submitted_job["jobId"]
        if not wait_until_completed:
            return job_id

        logging.info(f"Job {job_id} submitted, now waiting until completed.")
        last_job_status = None
        start = datetime.now(timezone.utc) - timedelta(seconds=30)
        end = start + timedelta(minutes=timeout)
        while True:
            if datetime.now(timezone.utc) > end:
                raise BuilderError("Timeout")

            job_description = self.client.describe_jobs(jobs=[job_id])["jobs"][0]
            job_status = job_description["status"]
            if job_status != last_job_status:
                last_job_status = job_status
                logging.info(f"Job status: {job_status}")
            if job_status in ["SUCCEEDED", "FAILED"]:
                break

            sleep(5)

        logging.info(f"Job status reason: {job_description['statusReason']}")

        # https://eu-central-1.console.aws.amazon.com/batch/v2/home?region=eu-central-1#jobs/detail/6b6da9eb-5eb8-431e-9d9b-2dc69185f883
        aws_region = re.match(r"arn:aws:batch:(.*?):.*", job_description["jobQueue"]).group(1)
        url = f"https://{aws_region}.console.aws.amazon.com/batch/v2/home?region={aws_region}#jobs/detail/{job_id}"
        logging.info(f"Job details in AWS console: {url}")

        return job_id
