=====
Tasks
=====

Resources related to tasks.


CronJob
----------

The CronJob resource represents cron(8) to execute scheduled commands.

List resource
+++++++++++++

.. http:get:: /api/v1.0/tasks/cronjob/

   Returns a list of all cronjobs.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/tasks/cronjob/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "cron_command": "touch /tmp/xx",
                "cron_daymonth": "*",
                "cron_dayweek": "*",
                "cron_description": "",
                "cron_enabled": true,
                "cron_hour": "*",
                "cron_minute": "*",
                "cron_month": "1,2,3,4,6,7,8,9,10,11,12",
                "cron_stderr": false,
                "cron_stdout": true,
                "cron_user": "root",
                "id": 1
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/tasks/cronjob/

   Creates a new cronjob and returns the new cronjob object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/tasks/cronjob/ HTTP/1.1
      Content-Type: application/json

        {
                "cron_user": "root",
                "cron_command": "/data/myscript.sh",
                "cron_minute": "*/20",
                "cron_hour": "*",
                "cron_daymonth": "*",
                "cron_month": "*",
                "cron_dayweek": "*",
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "cron_command": "/data/myscript.sh",
                "cron_daymonth": "*",
                "cron_dayweek": "*",
                "cron_description": "",
                "cron_enabled": true,
                "cron_hour": "*",
                "cron_minute": "*/20",
                "cron_month": "*",
                "cron_stderr": false,
                "cron_stdout": true,
                "cron_user": "root",
                "id": 2
        }

   :json string cron_command: command to execute
   :json string cron_daymonth: days of the month to run
   :json string cron_dayweek: days of the week to run
   :json string cron_description: description of the job
   :json boolean cron_enabled: job enabled?
   :json string cron_hour: hours to run
   :json string cron_minute: minutes to run
   :json string cron_month: months to run
   :json string cron_user: user to run
   :json boolean cron_stderr: redirect stderr to /dev/null
   :json boolean cron_stdout: redirect stdout to /dev/null
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/tasks/cronjob/(int:id)/

   Update cronjob `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/tasks/cronjob/2/ HTTP/1.1
      Content-Type: application/json

        {
                "cron_enabled": false,
                "cron_stderr": true
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "cron_command": "/data/myscript.sh",
                "cron_daymonth": "*",
                "cron_dayweek": "*",
                "cron_description": "",
                "cron_enabled": false,
                "cron_hour": "*",
                "cron_minute": "*/20",
                "cron_month": "*",
                "cron_stderr": true,
                "cron_stdout": true,
                "cron_user": "root",
                "id": 2
        }

   :json string cron_command: command to execute
   :json string cron_daymonth: days of the month to run
   :json string cron_dayweek: days of the week to run
   :json string cron_description: description of the job
   :json boolean cron_enabled: job enabled?
   :json string cron_hour: hours to run
   :json string cron_minute: minutes to run
   :json string cron_month: months to run
   :json string cron_user: user to run
   :json boolean cron_stderr: redirect stderr to /dev/null
   :json boolean cron_stdout: redirect stdout to /dev/null
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/tasks/cronjob/(int:id)/

   Delete cronjob `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/tasks/cronjob/2/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Run
+++

.. http:post:: /api/v1.0/tasks/cronjob/(int:id)/run/

   Start cron job of `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/tasks/cronjob/1/run/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Cron job started.

   :resheader Content-Type: content type of the response
   :statuscode 202: no error


InitShutdown
------------

The InitShutdown resource represents Init and Shutdown scripts.

List resource
+++++++++++++

.. http:get:: /api/v1.0/tasks/initshutdown/

   Returns a list of all init shutdown scripts.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/tasks/initshutdown/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "id": 1
                "ini_type": "command",
                "ini_command": "rm /mnt/tank/temp*",
                "ini_when": "postinit"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/tasks/initshutdown/

   Creates a new initshutdown and returns the new initshutdown object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/tasks/initshutdown/ HTTP/1.1
      Content-Type: application/json

        {
                "ini_type": "command",
                "ini_command": "rm /mnt/tank/temp*",
                "ini_when": "postinit"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "id": 1,
                "ini_command": "rm /mnt/tank/temp*",
                "ini_script": null,
                "ini_type": "command",
                "ini_when": "postinit"
        }

   :json string ini_command: command to execute
   :json string ini_script: path to script to execute
   :json string ini_type: run a command ("command") or a script ("script")
   :json string ini_when: preinit, postinit, shutdown
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/tasks/initshutdown/(int:id)/

   Update initshutdown `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/tasks/initshutdown/1/ HTTP/1.1
      Content-Type: application/json

        {
                "ini_when": "preinit"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "id": 1,
                "ini_command": "rm /mnt/tank/temp*",
                "ini_script": null,
                "ini_type": "command",
                "ini_when": "preinit"
        }

   :json string ini_command: command to execute
   :json string ini_script: path to script to execute
   :json string ini_type: run a command ("command") or a script ("script")
   :json string ini_when: preinit, postinit, shutdown
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/tasks/initshutdown/(int:id)/

   Delete initshutdown `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/tasks/initshutdown/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Rsync
----------

The Rsync resource represents rsync(1) to execute scheduled commands.

List resource
+++++++++++++

.. http:get:: /api/v1.0/tasks/rsync/

   Returns a list of all rsyncs.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/tasks/rsync/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "rsync_user": "root",
                "rsync_minute": "*/20",
                "rsync_enabled": true,
                "rsync_daymonth": "*",
                "rsync_path": "/mnt/tank",
                "rsync_delete": false,
                "rsync_hour": "*",
                "id": 1,
                "rsync_extra": "",
                "rsync_archive": false,
                "rsync_compress": true,
                "rsync_dayweek": "*",
                "rsync_desc": "",
                "rsync_direction": "push",
                "rsync_times": true,
                "rsync_preserveattr": false,
                "rsync_remotehost": "testhost",
                "rsync_mode": "module",
                "rsync_remotemodule": "testmodule",
                "rsync_remotepath": "",
                "rsync_quiet": false,
                "rsync_recursive": true,
                "rsync_month": "*",
                "rsync_preserveperm": false,
                "rsync_remoteport": 22
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/tasks/rsync/

   Creates a new rsync and returns the new rsync object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/tasks/rsync/ HTTP/1.1
      Content-Type: application/json

        {
                "rsync_path": "/mnt/tank",
                "rsync_user": "root",
                "rsync_mode": "module",
                "rsync_remotemodule": "testmodule",
                "rsync_remotehost": "testhost",
                "rsync_direction": "push",
                "rsync_minute": "*/20",
                "rsync_hour": "*",
                "rsync_daymonth": "*",
                "rsync_month": "*",
                "rsync_dayweek": "*",
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "rsync_user": "root",
                "rsync_minute": "*/20",
                "rsync_enabled": true,
                "rsync_daymonth": "*",
                "rsync_path": "/mnt/tank",
                "rsync_delete": false,
                "rsync_hour": "*",
                "id": 1,
                "rsync_extra": "",
                "rsync_archive": false,
                "rsync_compress": true,
                "rsync_dayweek": "*",
                "rsync_desc": "",
                "rsync_direction": "push",
                "rsync_times": true,
                "rsync_preserveattr": false,
                "rsync_remotehost": "testhost",
                "rsync_mode": "module",
                "rsync_remotemodule": "testmodule",
                "rsync_remotepath": "",
                "rsync_quiet": false,
                "rsync_recursive": true,
                "rsync_month": "*",
                "rsync_preserveperm": false,
                "rsync_remoteport": 22
        }

   :json string rsync_path: path to rsync
   :json string rsync_user: user to run rsync(1)
   :json string rsync_mode: module, ssh
   :json string rsync_remotemodule: module of remote side
   :json string rsync_remotehost: host of remote side
   :json string rsync_remoteport: port of remote side
   :json string rsync_remotepath: path of remote side
   :json string rsync_direction: push, pull
   :json string rsync_minute: minutes to run
   :json string rsync_hour: hours to run
   :json string rsync_daymonth: days of month to run
   :json string rsync_month: months to run
   :json string rsync_dayweek: days of week to run
   :json boolean rsync_archive: archive mode
   :json boolean rsync_compress: compress the stream
   :json boolean rsync_times: preserve times
   :json boolean rsync_preserveattr: preserve file attributes
   :json boolean rsync_quiet: run quietly
   :json boolean rsync_recursive: recursive
   :json boolean rsync_preserveperm: preserve permissions
   :json string extra: extra arguments to rsync(1)
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/tasks/rsync/(int:id)/

   Update rsync `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/tasks/rsync/1/ HTTP/1.1
      Content-Type: application/json

        {
                "rsync_archive": true
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "rsync_user": "root",
                "rsync_minute": "*/20",
                "rsync_enabled": true,
                "rsync_daymonth": "*",
                "rsync_path": "/mnt/tank",
                "rsync_delete": false,
                "rsync_hour": "*",
                "id": 1,
                "rsync_extra": "",
                "rsync_archive": true,
                "rsync_compress": true,
                "rsync_dayweek": "*",
                "rsync_desc": "",
                "rsync_direction": "push",
                "rsync_times": true,
                "rsync_preserveattr": false,
                "rsync_remotehost": "testhost",
                "rsync_mode": "module",
                "rsync_remotemodule": "testmodule",
                "rsync_remotepath": "",
                "rsync_quiet": false,
                "rsync_recursive": true,
                "rsync_month": "*",
                "rsync_preserveperm": false,
                "rsync_remoteport": 22
        }

   :json string rsync_path: path to rsync
   :json string rsync_user: user to run rsync(1)
   :json string rsync_mode: module, ssh
   :json string rsync_remotemodule: module of remote side
   :json string rsync_remotehost: host of remote side
   :json string rsync_remoteport: port of remote side
   :json string rsync_remotepath: path of remote side
   :json string rsync_direction: push, pull
   :json string rsync_minute: minutes to run
   :json string rsync_hour: hours to run
   :json string rsync_daymonth: days of month to run
   :json string rsync_month: months to run
   :json string rsync_dayweek: days of week to run
   :json boolean rsync_archive: archive mode
   :json boolean rsync_compress: compress the stream
   :json boolean rsync_times: preserve times
   :json boolean rsync_preserveattr: preserve file attributes
   :json boolean rsync_quiet: run quietly
   :json boolean rsync_recursive: recursive
   :json boolean rsync_preserveperm: preserve permissions
   :json string extra: extra arguments to rsync(1)
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/tasks/rsync/(int:id)/

   Delete rsync `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/tasks/rsync/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Run
+++

.. http:post:: /api/v1.0/tasks/rsync/(int:id)/run/

   Start rsync job of `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/tasks/rsync/1/run/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Rsync job started.

   :resheader Content-Type: content type of the response
   :statuscode 202: no error


SMARTTest
----------

The SMARTTest resource represents schedule of SMART tests using smartd(8).

List resource
+++++++++++++

.. http:get:: /api/v1.0/tasks/smarttest/

   Returns a list of all smarttests.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/tasks/smarttest/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "smarttest_dayweek": "*",
                "smarttest_daymonth": "*",
                "smarttest_disks": [
                        2,
                        3
                ],
                "smarttest_month": "*",
                "smarttest_type": "L",
                "id": 1,
                "smarttest_hour": "*",
                "smarttest_desc": ""
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/tasks/smarttest/

   Creates a new smarttest and returns the new smarttest object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/tasks/smarttest/ HTTP/1.1
      Content-Type: application/json

        {
                "smarttest_disks": [2, 3],
                "smarttest_type": "L",
                "smarttest_hour": "*",
                "smarttest_daymonth": "*",
                "smarttest_month": "*",
                "smarttest_dayweek": "*",
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "smarttest_dayweek": "*",
                "smarttest_daymonth": "*",
                "smarttest_disks": [
                        2,
                        3
                ],
                "smarttest_month": "*",
                "smarttest_type": "L",
                "id": 1,
                "smarttest_hour": "*",
                "smarttest_desc": ""
        }

   :json string smarttest_dayweek: days of the week to run
   :json string smarttest_daymonth: days of the month to run
   :json string smarttest_hour: hours to run
   :json string smarttest_month: months to run
   :json string smarttest_disks: list of ids of "storage/disk" resource
   :json string smarttest_type: L (Long Self-Test), S (Short Self-Test), C (Conveyance Self-Test (ATA  only)), O (Offline Immediate Test (ATA only))
   :json string smarttest_desc: user description of the test
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/tasks/smarttest/(int:id)/

   Update smarttest `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/tasks/smarttest/1/ HTTP/1.1
      Content-Type: application/json

        {
                "smarttest_type": "S",
                "smarttest_disks": [2, 3]
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "smarttest_dayweek": "*",
                "smarttest_daymonth": "*",
                "smarttest_disks": [
                        2,
                        3
                ],
                "smarttest_month": "*",
                "smarttest_type": "L",
                "id": 1,
                "smarttest_hour": "*",
                "smarttest_desc": ""
        }

   :json string smarttest_dayweek: days of the week to run
   :json string smarttest_daymonth: days of the month to run
   :json string smarttest_hour: hours to run
   :json string smarttest_month: months to run
   :json string smarttest_disks: list of ids of "storage/disk" resource
   :json string smarttest_type: L (Long Self-Test), S (Short Self-Test), C (Conveyance Self-Test (ATA  only)), O (Offline Immediate Test (ATA only))
   :json string smarttest_desc: user description of the test
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/tasks/smarttest/(int:id)/

   Delete smarttest `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/tasks/smarttest/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error
