import {
  todoSubscribeLogic,
  todoUnsubscribeLogic,
  todoCreateLogic
} from '../ducks/todoPubSub';
import { commandLogic } from '../ducks/command';

const rootLogic = [
  todoSubscribeLogic,
  todoUnsubscribeLogic,
  todoCreateLogic,
  commandLogic
];

export default rootLogic;
