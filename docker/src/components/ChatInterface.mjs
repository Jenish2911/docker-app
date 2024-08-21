import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { PersonIcon } from '../icons/PersonIcon.js';
import { RobotIcon } from '../icons/RobotIcon.js';
import { SendIcon } from '../icons/SendIcon.js';
import DockerfileDisplay from './DockerfileDisplay.mjs';
import axios from 'axios';

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #384d54;
  color: #ffffff;
  padding: 1rem;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  margin-bottom: 1rem;
  padding: 1rem;
`;

const MessageBubble = styled.div`
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
`;

const MessageContent = styled.div`
  background-color: ${props => props.isUser ? '#0db7ed' : '#2c3e50'};
  border-radius: 18px;
  padding: 8px 12px;
  max-width: 70%;
`;

const InputContainer = styled.div`
  display: flex;
  background-color: #2c3e50;
  border-radius: 25px;
  padding: 0.5rem;
`;

const Input = styled.input`
  flex: 1;
  background-color: transparent;
  border: none;
  color: #ffffff;
  font-size: 1rem;
  padding: 0.5rem 1rem;
  &::placeholder {
    color: #bdc3c7;
  }
  &:focus {
    outline: none;
  }
`;

const SendButton = styled.button`
  background-color: #0db7ed;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const IconWrapper = styled.div`
  background-color: ${props => props.isUser ? '#0db7ed' : '#2c3e50'};
  border-radius: 50%;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: ${props => props.isUser ? '0 0 0 8px' : '0 8px 0 0'};
`;

const GitHubPrompt = styled.div`
  background-color: #2c3e50;
  border-radius: 18px;
  padding: 16px;
  margin-bottom: 1rem;
  text-align: center;
`;

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [dockerfile, setDockerfile] = useState(null);
  const [command, setCommand] = useState(null);
  const [githubLink, setGitHubLink] = useState('');
  const [hasGitHubLink, setHasGitHubLink] = useState(false);

  useEffect(() => {
    const savedGitHubLink = localStorage.getItem('githubLink');
    if (savedGitHubLink) {
      setGitHubLink(savedGitHubLink);
      setHasGitHubLink(true);
    }
  }, []);

  const handleGitHubSubmit = () => {
    if (githubLink.trim()) {
      setHasGitHubLink(true);
      localStorage.setItem('githubLink', githubLink);
    } else {
      setGitHubLink('Not provided');
      setHasGitHubLink(true);
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      const newMessages = [...messages, { text: input, sender: 'user' }];
      setMessages(newMessages);

      // Concatenate all previous messages to form the chat history
      const chatHistory = newMessages.map(msg => `${msg.sender === 'user' ? 'Human' : 'AI'}: ${msg.text}`).join('\n');

      axios.post('http://localhost:3001/', { 
        message: input, 
        githubLink: githubLink || 'Not provided',
        hasgit: hasGitHubLink,
        chat_history: chatHistory // Include the chat history in the request
      })
        .then(response => {
          console.log(response.data);
          setMessages(prev => [...prev, { text: response.data.message, sender: 'ai' }]);
          if (response.data.type === 'dockerfile') {
            setDockerfile(response.data.dockerfile);
            setCommand(response.data.commands);  
          }
        })
        .catch(error => {
          console.error('Error:', error);
          setMessages(prev => [...prev, { text: "Sorry, there was an error processing your request.", sender: 'ai' }]);
        });
      setInput('');
    }
  };

  const handleFinalizeDockerfile = () => {
    console.log("Dockerfile finalized:", dockerfile);
    axios.post('http://localhost:3001/finalize', {
      "dockerfile": dockerfile,
      "commands": command,
      "githubLink": githubLink || 'Not provided',
      
    }).then(response => {
      console.log(response);
    }).catch(error => {
      console.error('Error:', error);
    });
  };

  if (!hasGitHubLink) {
    return (
      <GitHubPrompt>
        <h2>Please enter your GitHub link:</h2>
        <Input
          value={githubLink}
          onChange={(e) => setGitHubLink(e.target.value)}
          placeholder="GitHub link (or leave blank)"
        />
        <SendButton onClick={handleGitHubSubmit}>
          <SendIcon />
        </SendButton>
      </GitHubPrompt>
    );
  }

  return (
    <ChatContainer>
      <MessagesContainer>
        {messages.map((message, index) => (
          <MessageBubble key={index} style={{justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'}}>
            {message.sender === 'ai' && <IconWrapper><RobotIcon /></IconWrapper>}
            <MessageContent isUser={message.sender === 'user'}>
              {message.text}
            </MessageContent>
            {message.sender === 'user' && <IconWrapper isUser><PersonIcon /></IconWrapper>}
          </MessageBubble>
        ))}
      </MessagesContainer>
      {dockerfile && (
        <DockerfileDisplay 
          dockerfile={dockerfile}
          command={command}
          onFinalize={handleFinalizeDockerfile} 
        />
      )}
      <InputContainer>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message here"
        />
        <SendButton onClick={handleSend}>
          <SendIcon />
        </SendButton>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatInterface;
