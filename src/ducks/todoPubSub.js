import { fromJS } from 'immutable';
import { createLogic } from 'redux-logic';
import gql from 'graphql-tag';

// Actions

const SUBSCRIBE = 'todo-pubsub/SUBSCRIBE';
const SUBSCRIBE_SUCCESS = 'todo-pubsub/SUBSCRIBE_SUCCESS';
const UNSUBSCRIBE = 'todo-pubsub/UNSUBSCRIBE';
const UNSUBSCRIBE_SUCCESS = 'todo-pubsub/UNSUBSCRIBE_SUCCESS';
const RECEIVE = 'todo-pubsub/RECEIVE';
const CREATE = 'todo-pubsub/CREATE';
const TOGGLE = 'todo-pubsub/TOGGLE';

// Reducer

const initialState = fromJS({
  subid: null,
  todos: []
});

export default function todoPubSubReducer(state = initialState, action = {}) {
  const todos = state.get('todos');
  switch (action.type) {
    case SUBSCRIBE:
      return state;
    case SUBSCRIBE_SUCCESS:
      return state.set('subid', action.subid);
    case UNSUBSCRIBE:
      return state;
    case UNSUBSCRIBE_SUCCESS:
      return state.set('subid', null);
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
  return {
    type: SUBSCRIBE
  };
}

export function unsubscribeTodos() {
  return {
    type: UNSUBSCRIBE
  };
}

export function subscribeTodosSuccess(subid) {
  return {
    type: SUBSCRIBE_SUCCESS,
    subid
  }
}

export function receiveTodo(todo) {
  return {
    type: RECEIVE,
    todo
  };
}

export function createTodo(todo) {
  return {
    type: CREATE,
    todo
  };
}

export function toggleTodo(todoId) {
  return {
    type: TOGGLE,
    todoId
  };
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
    if (subscriptions['todo']) {
      dispatch(subscribeTodosSuccess(subscriptions['todo']._networkSubscriptionId));
      return;
    }
    const sub = apolloClient.subscribe({ query: newTodosQuery }).subscribe({
      next(data) {
        console.log('data', data);
      },
      error(err) {
        console.log('error', err);
      }
    });
    subscriptions['todo'] = sub
    dispatch(subscribeTodosSuccess(sub._networkSubscriptionId));
  }
});

export const todoUnsubscribeLogic = createLogic({
  type: UNSUBSCRIBE,
  latest: true,

  process({ apolloClient, subscriptions }, dispatch) {
    const sub = subscriptions['todo'];
    sub.unsubscribe();
    subscriptions['todo'] = null;
  }
});
