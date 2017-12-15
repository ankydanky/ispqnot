#! /usr/bin/python
# coding: utf-8

"""
BSD 3-Clause License

Copyright (c) 2017, ND.K
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import unicode_literals, print_function

import os
import sys
import re
import subprocess
import socket

try:
    import pymysql
except ImportError:
    print("pymysql not installed.")
    sys.exit(1)

try:
    import mailer
except ImportError:
    print("mailer not installed.")
    sys.exit(1)


config = {

    # demo mode, set to False to launch script for production
    "demo": False,

    # set email for demo sending, all email gets send to this address, warning email flood possible!
    "demoemail": "testmail@testdomain.test",

    # set database host
    "host": "127.0.0.1",

    # set database user and password
    "user": "<ispconfig>",
    "pass": "<password>",

    # set database name
    "database": "<db_ispconfig>",

    # set notification threshold
    "threshold": 95,

    # set fqdn for email sender, leave it to auto to autodetect
    "emailhostname": "auto",

    # send all notifications as a BCC, set it to None to disable
    "emailbcc": None

}

smtp = {

    # set smtp host
    "host": "127.0.0.1",

    # set login for smtp host, leave both to None for not logging in
    "user": None,
    "pass": None,

    # set smtp port
    "port": 587,

    # set it to True or False for TLS usage
    "tls": True

}


class QuotaNotifier(object):

    def __init__(self):
        self.db = pymysql.connect(
            host=config['host'],
            user=config['user'],
            password=config['pass'],
            database=config['database'],
            charset="utf8"
        )
        self.cur = self.db.cursor(pymysql.cursors.DictCursor)
        self.mailusers = []
    
    def _readAllMailUsers(self):
        qry = self.cur.execute(
            """SELECT email, name, maildir, quota
            FROM mail_user
            WHERE access='y'
                AND (
                    disableimap='n'
                    OR disablepop3='n'
                )
            ORDER BY name ASC"""
        )
        self.mailusers = self.cur.fetchall()
    
    def _getUsage(self, path):
        proc = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        stdout, sterr = proc.communicate()
        return int(stdout.split()[0])

    def _isOverThreshold(self, sys_quota, db_quota):
        if sys_quota >= ((db_quota / 100) * config['threshold']):
            return True
        return False

    def _unitformat(self, size):
        size = float(size)
        return round(size/1024**2, 2)
    
    def _filterOverQuota(self):
        for email in list(self.mailusers):
            db_quota = email['quota']
            sys_quota = self._getUsage(email['maildir'])
            if not self._isOverThreshold(sys_quota, db_quota):
                self.mailusers.remove(email)
            else:
                sys_quota = self._unitformat(sys_quota)
                db_quota = self._unitformat(db_quota)
                print("Found %s over threshold: %s MB/%s MB" % (email['email'], sys_quota, db_quota))
    
    def _notify(self):
        if len(self.mailusers) == 0:
            return
        subj = "Your mailbox has reached a quota threshold"
        body = (
            "I am sorry to inform you that your email account for:\n\n"
            "%s\n\n"
            "has reached a usage of over %s%%. Please take actions before your inbox gets full.\n\n"
            "Sincerely, your email server."
        )
        emailhostname = config['emailhostname']
        msg = mailer.Message()
        msg.Subject = subj
        msg.charset = "utf-8"
        if config['emailbcc']:
            msg.BCC = config['emailbcc']
        mail = mailer.Mailer()
        mail.host = smtp['host']
        mail.use_tls = smtp['tls']
        mail.port = smtp['port']
        if smtp['user'] and smtp['pass']:
            mail.login(smtp['user'], smtp['pass'])
        print("Notifying above listed users...")
        for email in self.mailusers:
            if emailhostname == "auto" or emailhostname is None:
                emailhostname = email['email'].split("@")[1]
            msg.Body = body % (email['email'], config['threshold'])
            msg.From = "quota-notification@%s" % emailhostname
            if config['demo']:
                msg.To = config['demoemail']
            else:
                msg.To = email['email']
            mail.send(msg)
    
    def run(self):
        self._readAllMailUsers()
        self._filterOverQuota()
        self._notify()


if __name__ == "__main__":
    try:
        if config['demo']:
            print("WARNING, running in DEMO mode.")
        app = QuotaNotifier()
        app.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("Script aborted by user.")
        sys.exit(1)
