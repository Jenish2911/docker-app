import React from 'react';
import styled, { ThemeProvider } from 'styled-components';
import ChatInterface from './components/ChatInterface.mjs';
import DockerfileDisplay from './components/DockerfileDisplay.mjs';
import { theme } from './theme.js';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: ${props => props.theme.secondary};
`;

function App() {
  return (
    <ThemeProvider theme={theme}>
      <AppContainer>
        <ChatInterface />
       
      </AppContainer>
    </ThemeProvider>
  );
}

export default App;