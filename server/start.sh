#!/bin/sh
uwsgi --ini /home/server/uwsgi.ini --daemonize /home/server.log
/bin/bash