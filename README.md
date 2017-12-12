# ISPqnot
Quota notification mailer for ISPConfig3

Simple script for notifying your ISPConfig server email users that they are almost over quota.

Requirements:

 - Mailer (-> pip install mailer)
 - PyMySQL (-> pip install pymysql)

Configuration options:

**General config options are (config dictionary):**

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


**SMTP config (smtp dictionary):**

    # set smtp host
    "host": "127.0.0.1",

    # set login for smtp host, leave both to None for not logging in
    "user": None,
    "pass": None,

    # set smtp port
    "port": 587,

    # set it to True or False for TLS usage
    "tls": True
  
