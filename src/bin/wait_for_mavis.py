#! /usr/bin/env python3

import argparse
import os
import smtplib
import sys
from email.mime.text import MIMEText
from glob import glob
from shutil import copyfile
from time import sleep, strftime

def get_parser():
    """Construct the parser for command-line arguments"""
    desc = 'wait_for_mavis: Wait for completion of Mavis workflow and copy results to the given directory'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--dest', metavar='DIR', required=True, help='Destination directory for results')
    parser.add_argument('--email', metavar='EMAILS', help='Comma-separated list of email addresses, to notify on completion. Optional.')
    parser.add_argument('--id', metavar='ID', dest='cromwell_id', required=True, help='Cromwell job ID')
    parser.add_argument('--interval', type=int, default=1800, metavar='INT', help='Interval between checks (in seconds)')
    parser.add_argument('--max', type=int, default=146, metavar='INT', dest='max_count', help='Maximum number of checks') # rougly 146 counts of 30 minutes is 72 hours
    parser.add_argument('--source', metavar='DIR', required=True, help='Source directory for results; contains output for given Cromwell job ID')
    return parser

def main(args):
    """Main method to wait and copy results"""
    if not (os.path.isdir(args.dest) and os.access(args.dest, os.W_OK)):
        print("Invalid destination directory: {0}".format(args.dest), file=sys.stderr)
        sys.exit(1)
    zip_dir = os.path.join(args.source, args.cromwell_id, 'call-zipResults', 'execution')
    rc_path = os.path.join(zip_dir, 'rc')
    counter = 0
    message = "Mavis results for {0}: ".format(zip_dir)
    status_ok = True
    while True:
        counter += 1
        time_str = strftime("%Y-%m-%d_%H:%M:%S_%Z")
        if os.path.exists(rc_path):
            print("{0}: Found {1}".format(time_str, rc_path), file=sys.stderr)
            with open(rc_path) as rc_file:
                rc = int(rc_file.read().strip())
                if rc == 0:
                    message += "Workflow completed with return code 0"
                else:
                    message += "Workflow error with return code {0}".format(rc)
                    status_ok = False
                print("{0}: {1}".format(time_str, message), file=sys.stderr)
            break
        elif counter >= args.max_count:
            message += "Wait script exited after timeout"
            print("{0}: {1}".format(time_str, message), file=sys.stderr)
            status_ok = False
            break
        else:
            print("{0}: Still waiting for {1}".format(time_str, rc_path), file=sys.stderr)
            sys.stderr.flush() # force output to print to the waitlog
            sleep(args.interval)
    if status_ok:
        results = glob(zip_dir+"/*_mavis-output.zip")
        if len(results)!=1:
            error = "Error: Expected exactly 1 .zip file, found {0}".format(len(results))
            print(error, file=sys.stderr)
            message += "\n{0}".format(error)
            status_ok = False
        else:
            result = results.pop()
            dest_path = os.path.join(args.dest, os.path.basename(result))
            copyfile(result, dest_path)
    if args.email:
        send_email(args.email, message, args.cromwell_id, status_ok)
    if not status_ok:
        sys.exit(1)

def send_email(recipients, text, cromwell_id, status_ok):
    """Send a notification email to given recipients"""
    if status_ok:
        subject = 'Mavis success for {0}'.format(cromwell_id)
    else:
        subject = 'Mavis failure for {0}'.format(cromwell_id)
    msg = MIMEText(text)
    sender = 'mavis_wait_script@example.com'
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipients
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, [recipients], msg.as_string())
    s.quit()

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        main(parser.parse_args())
