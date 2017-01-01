import { fromJS } from 'immutable';
import React from 'react';
import ReactDOM from 'react-dom';
import { Router, Route, IndexRoute, browserHistory } from 'react-router';
import { syncHistoryWithStore } from 'react-router-redux';
import { Client } from 'subscriptions-transport-ws';
import ApolloClient, { createNetworkInterface } from 'apollo-client';
import { ApolloProvider } from 'react-apollo';
import App from './containers/App';
import HomeApp from './containers/Home/HomeApp';
import TodoApp from './containers/Todo/TodoApp';
import RemoteTodoApp from './containers/RemoteTodo/RemoteTodoApp';
import configureStore from './redux/store';
import './index.css';

const initialState = {
  todo: fromJS({
    todos: [
      {id: '0', text: 'hello', completed: true},
      {id: '1', text: 'world', completed: false}
    ]
  })
};

const addGraphQLSubscriptions = (networkInterface, wsClient) => Object.assign(networkInterface, {
  subscribe: (request, handler) => wsClient.subscribe({
    query: print(request.query),
    variables: request.variables,
  }, handler),
  unsubscribe: (id) => {
    wsClient.unsubscribe(id);
  },
});
const networkInterface = createNetworkInterface({
  uri: 'http://localhost:4000/graphql',
  opts: {
    credentials: 'same-origin',
  },
});
const wsClient = new Client('ws://localhost:4000');
const networkInterfaceWithSubscriptions = addGraphQLSubscriptions(
  networkInterface,
  wsClient
);
const client = new ApolloClient({
  networkInterface: networkInterfaceWithSubscriptions
});

const store = configureStore(initialState, client);
const history = syncHistoryWithStore(browserHistory, store)

ReactDOM.render(
  <ApolloProvider store={store} client={client}>
    <Router history={history}>
      <Route path="/" component={App}>
        <IndexRoute component={HomeApp}/>
        <Route path="todo" component={TodoApp}/>
        <Route path="remote" component={RemoteTodoApp}/>
      </Route>
    </Router>
  </ApolloProvider>,
  document.getElementById('root')
);
