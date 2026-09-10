import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import { AuthProvider } from './contexts/AuthContext'
import { ChatProvider } from './contexts/ChatContext'
import { ThemeProvider } from './contexts/ThemeContext'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><ThemeProvider><AuthProvider><ChatProvider><App /></ChatProvider></AuthProvider></ThemeProvider></React.StrictMode>)
