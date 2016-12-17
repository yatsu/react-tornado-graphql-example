#!/bin/sh

echo \
'{
    "query": "mutation toggleTodo($id: String!) { toggleTodo(id: $id) { completed __typename } }",
    "variables": {"id": "2"},
    "operationName": "toggleTodo"
}' | http post http://localhost:4000/graphql content-type:application/json
# | jq -Mc
