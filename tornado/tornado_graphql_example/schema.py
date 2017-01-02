# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from collections import namedtuple, OrderedDict
import json
from graphql import (
    GraphQLField, GraphQLNonNull, GraphQLArgument,
    GraphQLObjectType, GraphQLList, GraphQLBoolean, GraphQLString,
    GraphQLSchema
)


Todo = namedtuple('Todo', 'id text completed')

TodoList = namedtuple('TodoList', 'todos')

TodoType = GraphQLObjectType(
    name='Todo',
    fields=lambda: {
        'id': GraphQLField(
            GraphQLNonNull(GraphQLString),
        ),
        'text': GraphQLField(
            GraphQLString
        ),
        'completed': GraphQLField(
            GraphQLBoolean
        )
    }
)

TodoListType = GraphQLObjectType(
    name='TodoList',
    fields=lambda: {
        'todos': GraphQLField(
            GraphQLList(TodoType),
            resolver=lambda todo_list, *_: get_todos(todo_list),
        )
    }
)


todo_data = OrderedDict({
    '1': Todo(id='1', text='Make America Great Again', completed=False),
    '2': Todo(id='2', text='Quit TPP', completed=False)
})


def get_todo_list(opts):
    return TodoList(todos=todo_data.keys())


def get_todo(id, opts):
    return todo_data.get(id)


def get_todos(todo_list, opts):
    return map(get_todo, todo_list.todos)


def add_todo(text, opts):
    todo = Todo(id=str(len(todo_data) + 1), text=text, completed=False)
    todo_data[todo.id] = todo
    print('add_todo', text)
    for sock in opts['sockets']:
        subscriptions = opts['subscriptions'].get(sock, [])
        if 'todos' in subscriptions:
            print('write_message', subscriptions['todos'])
            sock.write_message(json.dumps({
                'type': 'subscription_data',
                'id': subscriptions['todos'],
                'payload': {
                    'data': {
                        'id': todo.id,
                        'text': todo.text,
                        'completed': todo.completed
                    }
                }
            }))
    return todo


def toggle_todo(id, opts):
    cur_todo = todo_data[id]
    todo = Todo(id=id, text=cur_todo.text, completed=not cur_todo.completed)
    todo_data[id] = todo
    return todo


def query_root(opts):
    return GraphQLObjectType(
        name='Query',
        fields=lambda: {
            'todoList': GraphQLField(
                TodoListType,
                resolver=lambda root, args, *_:
                    get_todo_list(opts=opts),
            )
        }
    )


def mutation_root(opts):
    return GraphQLObjectType(
        name='Mutation',
        fields=lambda: {
            'addTodo': GraphQLField(
                TodoType,
                args={
                    'text': GraphQLArgument(GraphQLString)
                },
                resolver=lambda root, args, *_:
                    add_todo(args.get('text'), opts=opts)
            ),
            'toggleTodo': GraphQLField(
                TodoType,
                args={
                    'id': GraphQLArgument(GraphQLString)
                },
                resolver=lambda root, args, *_:
                    toggle_todo(args.get('id'), opts=opts)
            )
        }
    )


def schema(opts):
    return GraphQLSchema(query_root(opts), mutation_root(opts))
