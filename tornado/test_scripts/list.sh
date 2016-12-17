#!/bin/sh

echo 'query TodoListQuery { todoList { todos { id text completed } } }' | http post http://localhost:4000/graphql content-type:application/graphql
