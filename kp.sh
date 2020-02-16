#!/bin/bash

args="$@"

current_venv=$VIRTUAL_ENV

[ -z "$KP_VIRTUAL_ENV" ] && echo "Error: Missing KP_VIRTUAL_ENV (path to kpcli virtual env directory)" && exit ||

  . $KP_VIRTUAL_ENV/bin/activate

  python /Users/becky/projects/kpcli/kp.py $args

  . $current_venv/bin/activate
