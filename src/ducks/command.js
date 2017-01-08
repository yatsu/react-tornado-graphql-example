import { List as iList, fromJS } from 'immutable';
import { createLogic } from 'redux-logic';
import gql from 'graphql-tag';

// Actions

const EXECUTE = 'command/EXECUTE';
const EXECUTE_SUCCEEDED = 'command/EXECUTE_SUCCEEDED';
const EXECUTE_FAILED = 'command/EXECUTE_FAILED';
const OUTPUT_RECEIVED = 'command/OUTPUT_RECEIVED';
const OUTPUT_FINISHED = 'command/OUTPUT_FINISHED';

// Reducer

const initialState = fromJS({
  subid: null,
  command: null,
  output: [],
});

export default function commandReducer(state = initialState, action = {}) {
  switch (action.type) {
    case EXECUTE:
      return state
        .set('command', action.command)
        .set('output', iList());
    case EXECUTE_SUCCEEDED:
      return state.set('subid', action.subid)
    case EXECUTE_FAILED:
      return state.set('output', iList());
    case OUTPUT_RECEIVED:
      return state.set('output', state.get('output').push(action.output));
    case OUTPUT_FINISHED:
      return state;
    default:
      return state;
  }
}

// Action Creators

export function execute(command) {
  return {
    type: EXECUTE,
    command
  };
}

export function executeSucceeded(subid) {
  return {
    type: EXECUTE_SUCCEEDED,
    subid
  };
}

export function executeFailed() {
  return {
    type: EXECUTE_FAILED
  };
}

export function outputReceived(output) {
  return {
    type: OUTPUT_RECEIVED,
    output
  };
}

export function outputFinished() {
  return {
    type: OUTPUT_FINISHED,
    subid: null
  };
}

// GraphQL Queries

const commandQuery = gql`
  subscription commandExecute($command: String!) {
    commandExecute(command: $command) {
      stdout
      finished
      timestamp
    }
  }
`;

// Logic

export const commandLogic = createLogic({
  type: EXECUTE,
  latest: true,

  process({ apolloClient, subscriptions }, dispatch, done) {
    if (subscriptions['command']) {
      return;
    }
    const sub = apolloClient.subscribe({ query: commandQuery }).subscribe({
      next(resp) {
        if (resp.stdout) {
          dispatch(outputReceived(resp.stdout));
        }
        if (resp.finished) {
          sub.unsubscribe();
          subscriptions['command'] = null;
          dispatch(outputFinished());
        }
      },
      error(err) {
        console.error('command subscription error', err);
      }
    });
    console.log('sub', sub);
    subscriptions['command'] = sub
    dispatch(executeSucceeded(sub._networkSubscriptionId));
  }
});
