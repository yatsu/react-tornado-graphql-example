#!/bin/sh

echo \
'{
    "command": "ls"
}' | http post http://localhost:4000/command content-type:application/json
# | jq -Mc
