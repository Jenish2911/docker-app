import React from 'react';
import styled from 'styled-components';

const DisplayContainer = styled.div`
  margin-top: 1rem;
  padding: 1rem;
  background-color: ${props => props.theme.white};
  border: 1px solid ${props => props.theme.secondary};
  border-radius: 4px;
  color:${props => props.theme.black};
`;

const DockerfileContent = styled.pre`
  white-space: pre-wrap;
  word-wrap: break-word;
`;

const FinalizeButton = styled.button`
  background-color: ${props => props.theme.primary};
  color: ${props => props.theme.white};
  border: none;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;
  border-radius: 4px;
`;

const DockerfileDisplay = ({ dockerfile, command, onFinalize }) => (
  <DisplayContainer>
    <h3>Generated Dockerfile:</h3>
    <DockerfileContent>{dockerfile}</DockerfileContent>
    {command && (
      <>
        <h4>Command to run:</h4>
        <DockerfileContent>{command}</DockerfileContent>
      </>
    )}
    <FinalizeButton onClick={onFinalize}>Finalize Dockerfile</FinalizeButton>
  </DisplayContainer>
);

export default DockerfileDisplay;