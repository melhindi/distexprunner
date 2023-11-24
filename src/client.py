#!/usr/bin/env python3

import argparse
import logging
import sys

from distexprunner.experiment_client import ExperimentClient
from distexprunner.notification import Notifier, Slack
from distexprunner.outputs import LOG_LEVEL_CMD


__author__ = 'mjasny'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Distributed Experiment Runner Client Instance')
    parser.add_argument('-v', '--verbose', action="count",
                        default=0, help='-v WARN -vv INFO -vvv DEBUG')
    parser.add_argument('--resume', action='store_true',
                        help='Resume execution of experiments from last run')
    parser.add_argument('--slack-webhook', type=str,
                        help='Notify to slack when execution finishes')
    parser.add_argument('--no-progress', action='store_true',
                        default=False, help='Hide progressbar')
    parser.add_argument('--log', type=str, help='Log into file')
    parser.add_argument('experiment', nargs='+', type=str,
                        help='path to experiments, folders are searched recursively, order is important')
    args = parser.parse_args()

    logging_handlers = []
    logging_handlers.append(logging.StreamHandler(sys.stdout))

    if args.log:
        logging_handlers.append(logging.FileHandler(filename=args.log))

    if logging_handlers:
        logging.basicConfig(
            # [%(filename)s:%(lineno)d]:
            format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s\r',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=max(4 - args.verbose, 0) * 10,
            handlers=logging_handlers
        )
    else:
        logging.disable(LOG_LEVEL_CMD)

    if args.slack_webhook:
        notifier = Slack(args.slack_webhook)
    else:
        notifier = Notifier()

    client = ExperimentClient(
        experiments=args.experiment,
        resume=args.resume,
        notifier=notifier,
        progress=not args.no_progress,
    )
    client.start()
