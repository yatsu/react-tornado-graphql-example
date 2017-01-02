import {
  todoSubscribeLogic,
  todoUnsubscribeLogic,
  todoCreateLogic
} from '../ducks/todoPubSub';

const rootLogic = [
  todoSubscribeLogic,
  todoUnsubscribeLogic,
  todoCreateLogic
];

export default rootLogic;
