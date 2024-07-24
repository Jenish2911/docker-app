import React from 'react';
import styled from 'styled-components';

const MessageContainer = styled.div`
  max-width: 70%;
  padding: 0.5rem 1rem;
  margin: 0.5rem;
  border-radius: 20px;
  align-self: ${props => props.sender === 'user' ? 'flex-end' : 'flex-start'};
  background-color: ${props => props.sender === 'user' ? props.theme.primary : props.theme.secondary};
  color: ${props => props.theme.white};
`;

const Message = ({ message }) => (
  <MessageContainer sender={message.sender}>
    {message.text}
  </MessageContainer>
);

export default Message;