import React, { Component, PropTypes } from 'react';
import IPropTypes from 'react-immutable-proptypes';
import { Button, Divider } from 'semantic-ui-react';
import { connect } from 'react-redux';
import { execute } from '../../ducks/command';

class CommandApp extends Component {
  static propTypes = {
    output: IPropTypes.listOf(PropTypes.string).isRequired,
    commandExecute: PropTypes.func.isRequired
  }

  handleClick(event) {
    event.preventDefault();
    this.props.commandExecute();
  }

  render() {
    return (
      <div className="ui main text container main-content">
        <h1>Command Execution Example</h1>
        <Button primary onClick={e => this.handleClick(e)}>Countdown</Button>
        <Divider/>
        <h2>stdout</h2>
        <pre>{this.renderOutput()}</pre>
      </div>
    );
  }

  renderOutput() {
    const { output } = this.props;
    console.log('output', output);
    return <pre>{output.map(o => o).join('\n')}</pre>;
  }
}

const mapStateToProps = (state) => {
  const output = state['command'].get('output');
  return { output };
};

const mapDispatchToProps = (dispatch) => {
  return {
    commandExecute: () => {
      dispatch(execute('countdown'));
    }
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(CommandApp);
