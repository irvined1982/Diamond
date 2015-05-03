# coding=utf-8

"""
Send metrics to a [SQS](http://aws.amazon.com/sqs) queue.

- enable it in `diamond.conf` :

`    handlers = diamond.handler.sqs.SQSHandler
`

"""
import boto.sqs
import json
import logging

from Handler import Handler
from boto.sqs.message import RawMessage
from boto.exception import SQSError


class SQSHandler(Handler):
    """
    Implements the abstract Handler class, sending data to an SQS queue
    """
    RETRY = 3

    def __init__(self, config=None):
        """
        Create a new instance of the TSDBHandler class
        """
        # Initialize Handler
        Handler.__init__(self, config)

        # Initialize Data
        self.socket = None

        # Initialize Options
        self.aws_region = self.config['aws_region']
        self.aws_access_key = self.config['aws_access_key']
        self.aws_secret_key = self.config['aws_secret_key']
        self.aws_queue_name = self.config['aws_queue_name']

        self._conn = boto.sqs.connect_to_region(
            self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )

        # Try to find the queue.
        self._queue = None
        for q in self._conn.get_all_queues(prefix=self.aws_queue_name):
            if q.name == self.aws_queue_name:
                self._queue = q
                break

        if self._queue is None:
            logging.error("Queue: %s not found" % self.aws_queue_name)

    def get_default_config_help(self):
        """
        Returns the help text for the configuration options for this handler
        """
        config = super(SQSHandler, self).get_default_config_help()

        config.update({
            'aws_region': '',
            'aws_access_key': '',
            'aws_secret_key': '',
            'aws_queue_name': '',
        })

        return config

    def get_default_config(self):
        """
        Return the default config for the handler
        """
        config = super(SQSHandler, self).get_default_config()

        config.update({
            'aws_region': '',
            'aws_access_key': '',
            'aws_secret_key': '',
            'aws_queue_name': '',
        })
        return config

    def process(self, metric):
        """
        Process a metric by sending it to SQS
        """
        metric = {
            'metric': str(metric.getMetricPath()),
            'timestamp': int(metric.timestamp),
            'value': float(metric.value),
            'tags': {
                'precision': str(metric.precision),
                'host': str(metric.host),
                'ttl': str(metric.ttl),
            }
        }

        m = RawMessage()
        m.set_body(json.dumps(metric))
        if self._queue is not None:
            try:
                self._queue.write(m)
            except SQSError as e:
                logging.warn("Unable to log message: %s" % e)
