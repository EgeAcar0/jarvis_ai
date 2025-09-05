import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substr(2, 9));
  const [systemInfo, setSystemInfo] = useState(null);
  const [pendingCommands, setPendingCommands] = useState([]);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    connectWebSocket();
    fetchSystemInfo();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'ws://localhost:8001';
    const wsUrl = backendUrl.replace('https', 'wss').replace('http', 'ws') + `/api/ws/${sessionId}`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      setIsConnected(true);
      console.log('Connected to JARVIS');
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.data]);
        setIsTyping(false);
        
        // Check if it's a command proposal
        if (data.data.message_type === 'command_proposal') {
          // Extract command ID from message
          const commandIdMatch = data.data.message.match(/\*\*Command ID:\*\* ([\w-]+)/);
          if (commandIdMatch) {
            setPendingCommands(prev => [...prev, {
              id: commandIdMatch[1],
              message: data.data.message,
              timestamp: data.data.timestamp
            }]);
          }
        }
      }
    };
    
    wsRef.current.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from JARVIS');
      // Attempt to reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  };

  const fetchSystemInfo = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/system-info`);
      const data = await response.json();
      setSystemInfo(data);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    }
  };

  const sendMessage = () => {
    if (inputMessage.trim() && wsRef.current && isConnected) {
      const message = {
        message: inputMessage,
        timestamp: new Date().toISOString()
      };
      
      // Add user message to display immediately
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        session_id: sessionId,
        message: inputMessage,
        sender: 'user',
        timestamp: new Date().toISOString(),
        message_type: 'text'
      }]);
      
      wsRef.current.send(JSON.stringify(message));
      setInputMessage('');
      setIsTyping(true);
      
      // Focus back to input
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const approveCommand = async (commandId) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/commands/${commandId}/approve`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Add command result to messages
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          session_id: sessionId,
          message: `**Command Executed Successfully**\n\nOutput:\n\`\`\`\n${result.result.output}\n\`\`\`\n\nReturn Code: ${result.result.return_code}`,
          sender: 'jarvis',
          timestamp: new Date().toISOString(),
          message_type: 'command_result'
        }]);
        
        // Remove from pending commands
        setPendingCommands(prev => prev.filter(cmd => cmd.id !== commandId));
      }
    } catch (error) {
      console.error('Failed to approve command:', error);
    }
  };

  const rejectCommand = async (commandId) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      await fetch(`${backendUrl}/api/commands/${commandId}/reject`, {
        method: 'POST'
      });
      
      // Remove from pending commands
      setPendingCommands(prev => prev.filter(cmd => cmd.id !== commandId));
      
      // Add rejection message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        session_id: sessionId,
        message: "Command rejected by user.",
        sender: 'jarvis',
        timestamp: new Date().toISOString(),
        message_type: 'text'
      }]);
    } catch (error) {
      console.error('Failed to reject command:', error);
    }
  };

  const formatMessage = (message) => {
    // Convert markdown-style formatting to HTML
    return message
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/\n/g, '<br />');
  };

  return (
    <div className="App">
      {/* Background */}
      <div className="jarvis-background"></div>
      
      {/* Header */}
      <header className="jarvis-header">
        <div className="header-left">
          <div className="jarvis-logo">
            <div className="logo-ring"></div>
            <div className="logo-center">J</div>
          </div>
          <div className="jarvis-title">
            <h1>JARVIS</h1>
            <span className="subtitle">Just A Rather Very Intelligent System</span>
          </div>
        </div>
        
        <div className="header-right">
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <div className="status-indicator"></div>
            <span>{isConnected ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          
          {systemInfo && (
            <div className="system-info">
              <div className="info-item">
                <span className="label">PLATFORM:</span>
                <span className="value">{systemInfo.platform.toUpperCase()}</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Pending Commands Panel */}
      {pendingCommands.length > 0 && (
        <div className="pending-commands">
          <h3>Pending Command Approvals</h3>
          {pendingCommands.map((cmd) => (
            <div key={cmd.id} className="command-approval">
              <div className="command-info">
                <div className="command-preview">
                  <div dangerouslySetInnerHTML={{ __html: formatMessage(cmd.message) }} />
                </div>
              </div>
              <div className="approval-buttons">
                <button 
                  className="approve-btn"
                  onClick={() => approveCommand(cmd.id)}
                >
                  APPROVE
                </button>
                <button 
                  className="reject-btn"
                  onClick={() => rejectCommand(cmd.id)}
                >
                  REJECT
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Chat Interface */}
      <main className="chat-container">
        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.sender}`}>
              <div className="message-header">
                <span className="sender-name">
                  {msg.sender === 'user' ? 'YOU' : 'JARVIS'}
                </span>
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div 
                className={`message-content ${msg.message_type}`}
                dangerouslySetInnerHTML={{ __html: formatMessage(msg.message) }}
              />
            </div>
          ))}
          
          {isTyping && (
            <div className="message jarvis">
              <div className="message-header">
                <span className="sender-name">JARVIS</span>
              </div>
              <div className="message-content typing">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>Analyzing...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Speak to JARVIS..."
              className="message-input"
              disabled={!isConnected}
              rows="1"
            />
            <button 
              onClick={sendMessage}
              disabled={!isConnected || !inputMessage.trim()}
              className="send-button"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;