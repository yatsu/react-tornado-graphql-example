import { combineReducers } from 'redux';
import { routerReducer } from 'react-router-redux';
import todoReducer from '../ducks/todo';
import todoPubSubReducer from '../ducks/todoPubSub';
import commandReducer from '../ducks/command';

export default function configureRootReducer(client) {
  return combineReducers({
    routing: routerReducer,
    apollo: client.reducer(),
    todo: todoReducer,
    todoPubSub: todoPubSubReducer,
    command: commandReducer
  });
}
