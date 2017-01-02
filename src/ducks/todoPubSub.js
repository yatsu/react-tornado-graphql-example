import { fromJS } from 'immutable';
import { createLogic } from 'redux-logic';
import gql from 'graphql-tag';

// Actions

const SUBSCRIBE = 'todo-pubsub/SUBSCRIBE';
const SUBSCRIBE_SUCCEEDED = 'todo-pubsub/SUBSCRIBE_SUCCEEDED';
const UNSUBSCRIBE = 'todo-pubsub/UNSUBSCRIBE';
const UNSUBSCRIBE_SUCCEEDED = 'todo-pubsub/UNSUBSCRIBE_SUCCEEDED';
const RECEIVED = 'todo-pubsub/RECEIVED';
const CREATE = 'todo-pubsub/CREATE';
const CREATE_SUCCEEDED = 'todo-pubsub/CREATE_SUCCEEDED';
const CREATE_FAILED = 'todo-pubsub/CREATE_FAILED';
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
    case SUBSCRIBE_SUCCEEDED:
      return state.set('subid', action.subid);
    case UNSUBSCRIBE:
      return state;
    case UNSUBSCRIBE_SUCCEEDED:
      return state.set('subid', null);
    case RECEIVED:
      return state.set('todos', todos.push(fromJS({
        id: action.todo.id,
        text: action.todo.text,
        completed: action.todo.completed
      })));
    case CREATE:
      return state;
    case CREATE_SUCCEEDED:
      return state;
    case CREATE_FAILED:
      return state.set('createError', action.createError);
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

export function subscribeTodosSucceed(subid) {
  return {
    type: SUBSCRIBE_SUCCEEDED,
    subid
  }
}

export function unsubscribeTodos() {
  return {
    type: UNSUBSCRIBE
  };
}

export function unsubscribeTodosSucceed(subid) {
  return {
    type: UNSUBSCRIBE_SUCCEEDED,
    subid
  }
}

export function todoReceived(todo) {
  return {
    type: RECEIVED,
    todo
  };
}

export function createTodo(todo) {
  return {
    type: CREATE,
    todo
  };
}

export function createTodoSucceeded(todo) {
  return {
    type: CREATE_SUCCEEDED,
    todo
  };
}

export function createTodoFailed(error) {
  return {
    type: CREATE_FAILED,
    createError: error
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

const addTodoMutation = gql`
  mutation addTodo($text: String!) {
    addTodo(text: $text) {
      id
      text
      completed
    }
  }
`;

// Logic

export const todoSubscribeLogic = createLogic({
  type: SUBSCRIBE,

  process({ apolloClient, subscriptions }, dispatch, done) {
    if (subscriptions['todo']) {
      dispatch(subscribeTodosSucceed(subscriptions['todo']._networkSubscriptionId));
      return;
    }
    const sub = apolloClient.subscribe({ query: newTodosQuery }).subscribe({
      next(todo) {
        dispatch(todoReceived(todo));
      },
      error(err) {
        console.error('subscription error', err);
      }
    });
    subscriptions['todo'] = sub
    dispatch(subscribeTodosSucceed(sub._networkSubscriptionId));
  }
});

export const todoUnsubscribeLogic = createLogic({
  type: UNSUBSCRIBE,
  latest: true,

  process({ apolloClient, subscriptions }, dispatch) {
    const sub = subscriptions['todo'];
    sub.unsubscribe();
    subscriptions['todo'] = null;
    dispatch(unsubscribeTodosSucceed(sub._networkSubscriptionId));
  }
});

export const todoCreateLogic = createLogic({
  type: CREATE,

  processOptions: {
    dispatchReturn: true,
    successType: createTodoSucceeded,
    failType: createTodoFailed
  },

  process({ apolloClient, action }, dispatch) {
    return apolloClient.mutate({
      mutation: addTodoMutation,
      variables: { text: action.todo }
    })
    .then(resp => resp.data.addTodo);
  }
});
