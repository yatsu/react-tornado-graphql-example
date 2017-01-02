import { fromJS } from 'immutable';
import { createLogic } from 'redux-logic';
import gql from 'graphql-tag';

// Actions

const SUBSCRIBE = 'todo-pubsub/SUBSCRIBE';
const UNSUBSCRIBE = 'todo-pubsub/UNSUBSCRIBE';
const RECEIVE = 'todo-pubsub/RECEIVE';
const CREATE = 'todo-pubsub/CREATE';
const TOGGLE = 'todo-pubsub/TOGGLE';

// Reducer

const initialState = fromJS({
  subscribed: false,
  todos: []
});

export default function todoPubSubReducer(state = initialState, action = {}) {
  const todos = state.get('todos');
  switch (action.type) {
    case SUBSCRIBE:
      return state.set('subscribed', true);
    case UNSUBSCRIBE:
      return state.set('subscribed', false);
    case RECEIVE:
      return state;
    case CREATE:
      return state.set('todos', todos.push(fromJS({
        id: todos.size.toString(),
        text: action.todo,
        completed: false
      })));
    case TOGGLE:
      const todo = todos.get(action.todoId);
      return state.set(
        'todos',
        todos.set(
          action.todoId,
          todo.set('completed', !todo.get('completed'))
        )
      );
    default:
      return state;
  }
}

// Action Creators

export function subscribeTodos() {
  return { type: SUBSCRIBE };
}

export function unsubscribeTodos() {
  return { type: UNSUBSCRIBE };
}

export function receiveTodo(todo) {
  return { type: RECEIVE, todo}
}

export function createTodo(todo) {
  return { type: CREATE, todo };
}

export function toggleTodo(todoId) {
  return { type: TOGGLE, todoId };
}

// GraphQL Queries

const newTodosQuery = gql`
  subscription todos {
    newTodos {
      id
      text
      completed
    }
  }
`;

// const todoListQuery = gql`
//   query TodoListQuery {
//     todoList {
//       todos {
//         id
//         text
//         completed
//       }
//     }
//   }
// `;

// const toggleTodoMutation = gql`
//   mutation toggleTodo($id: String!) {
//     toggleTodo(id: $id) {
//       completed
//     }
//   }
// `;

// Logic

export const todoSubscribeLogic = createLogic({
  type: SUBSCRIBE,
  latest: true,

  process({ apolloClient, subscriptions }, dispatch) {
    apolloClient.subscribe({ query: newTodosQuery }).subscribe({
      next(data) {
        console.log('newTodos', data);
      },
      error(err) {
        console.log('error', err);
      }
    });
  }
});

export const todoUnsubscribeLogic = createLogic({
  type: UNSUBSCRIBE,
  latest: true,

  process({ apolloClient, subscriptions }, dispatch) {
  }
});
