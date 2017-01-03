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
    fields={
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


todo_data = OrderedDict({
    '1': Todo(id='1', text='Make America Great Again', completed=False),
    '2': Todo(id='2', text='Quit TPP', completed=False)
})


class QueryRoot(GraphQLObjectType):

    def __init__(self):
        super(QueryRoot, self).__init__(
            name='Query',
            fields={
                'todoList': GraphQLField(
                    GraphQLObjectType(
                        name='TodoList',
                        fields={
                            'todos': GraphQLField(
                                GraphQLList(TodoType),
                                resolver=self.get_todos
                            )
                        }
                    ),
                    resolver=self.get_todo_ids
                )
            }
        )

    def get_todo_ids(self, source, args, context, info):
        return todo_data.keys()

    def get_todos(self, source, args, context, info):
        return [todo_data[todo_id] for todo_id in source]


class MutationRoot(GraphQLObjectType):

    def __init__(self, sockets, subscriptions):
        super(MutationRoot, self).__init__(
            name='Mutation',
            fields={
                'addTodo': GraphQLField(
                    TodoType,
                    args={'text': GraphQLArgument(GraphQLString)},
                    resolver=self.add_todo
                ),
                'toggleTodo': GraphQLField(
                    TodoType,
                    args={'id': GraphQLArgument(GraphQLString)},
                    resolver=self.toggle_todo
                )
            }
        )
        self.sockets = sockets
        self.subscriptions = subscriptions

    def add_todo(self, source, args, context, info):
        text = args.get('text')
        todo = Todo(id=str(len(todo_data) + 1), text=text, completed=False)
        todo_data[todo.id] = todo
        self.send_notif('todos', {
            'id': todo.id,
            'text': todo.text,
            'completed': todo.completed
        })
        return todo

    def toggle_todo(self, source, args, context, info):
        todo_id = args.get('id')
        cur_todo = todo_data[todo_id]
        todo = Todo(id=todo_id, text=cur_todo.text,
                    completed=not cur_todo.completed)
        todo_data[todo_id] = todo
        return todo

    def send_notif(self, name, data):
        for sock in self.sockets:
            subscriptions = self.subscriptions.get(sock, {})
            subid = subscriptions.get(name)
            if subid is not None:
                sock.write_message(json.dumps({
                    'type': 'subscription_data',
                    'id': subid,
                    'payload': {
                        'data': data
                    }
                }))


def schema(sockets, subscriptions):
    return GraphQLSchema(
        QueryRoot(),
        MutationRoot(sockets, subscriptions)
    )
