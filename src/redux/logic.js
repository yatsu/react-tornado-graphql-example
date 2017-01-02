import { todoSubscribeLogic, todoUnsubscribeLogic } from '../ducks/todoPubSub';

const rootLogic = [
  todoSubscribeLogic,
  todoUnsubscribeLogic
];

export default rootLogic;
