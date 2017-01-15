# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from collections import OrderedDict
import graphene


class Todo(graphene.ObjectType):
    id = graphene.ID()
    text = graphene.String()
    completed = graphene.Boolean()


class TodoList(graphene.ObjectType):
    todos = graphene.List(Todo)


todo_data = OrderedDict(
    [(t.id, t) for t in [
        Todo('1', 'Make America Great Again', False),
        Todo('2', 'Quit TPP', False)
    ]]
)


class Query(graphene.ObjectType):
    todo_list = graphene.Field(TodoList)

    def resolve_todo_list(self, args, context, info):
        return TodoList(todo_data.values())


class AddTodo(graphene.Mutation):
    class Input:
        text = graphene.String()

    todo = graphene.Field(lambda: Todo)

    def mutate(self, args, context, info):
        todo = Todo(str(len(todo_data) + 1),
                    args.get('text', ''),
                    args.get('completed', False))
        todo_data[todo.id] = todo
        return AddTodo(todo=todo)


class ToggleTodo(graphene.Mutation):
    class Input:
        id = graphene.ID()

    todo = graphene.Field(lambda: Todo)

    def mutate(self, args, context, info):
        todo = todo_data[args.get('id')]
        todo.completed = not todo.completed
        return ToggleTodo(todo)


class Mutation(graphene.ObjectType):
    add_todo = AddTodo.Field()
    toggle_todo = ToggleTodo.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
