import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    createChat,
    getChatHistory,
    getChatById,
    deleteChat as deleteChatApi,
    sendMessage,
    uploadImage,
} from '../api/chatApi';
import ChatSidebar from '../components/ChatSidebar';
import ChatWindow from '../components/ChatWindow';
import ImageUploader from '../components/ImageUploader';
import { startGuestChat, sendGuestMessage, uploadGuestImage } from '../api/guestApi';
import './ChatPage.css';

const ChatPage = () => {
    const { isAuthenticated, user, logout } = useAuth();
    const navigate = useNavigate();

    // Guest mode state (volatile, stored in component state)
    const [guestSessionId, setGuestSessionId] = useState(null);
    const [guestMessages, setGuestMessages] = useState([]);

    // Authenticated mode state
    const [chats, setChats] = useState([]);
    const [activeChatId, setActiveChatId] = useState(null);
    const [messages, setMessages] = useState([]);

    // UI state
    const [loading, setLoading] = useState(false);
    const [chatListLoading, setChatListLoading] = useState(false);
    const [showImageUploader, setShowImageUploader] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Load chat history on mount (authenticated users only)
    // For guests, create a session
    useEffect(() => {
        if (isAuthenticated) {
            loadChatHistory();
        } else {
            // Guest mode: create or restore session
            const savedSessionId = localStorage.getItem('guest_session_id');
            if (savedSessionId) {
                setGuestSessionId(savedSessionId);
            } else {
                initGuestSession();
            }
        }
    }, [isAuthenticated]);

    // Close mobile menu on resize
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth > 768) {
                setMobileMenuOpen(false);
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const loadChatHistory = async () => {
        setChatListLoading(true);
        try {
            const history = await getChatHistory();
            setChats(history);

            // Auto-select first chat if available
            if (history.length > 0 && !activeChatId) {
                handleChatSelect(history[0].chat_id);
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        } finally {
            setChatListLoading(false);
        }
    };

    const initGuestSession = async () => {
        try {
            const response = await startGuestChat();
            setGuestSessionId(response.session_id);
            localStorage.setItem('guest_session_id', response.session_id);
        } catch (error) {
            console.error('Failed to start guest session:', error);
        }
    };

    const handleNewChat = async () => {
        try {
            const newChat = await createChat();
            setChats([newChat, ...chats]);
            setActiveChatId(newChat.chat_id);
            setMessages([]);
        } catch (error) {
            console.error('Failed to create chat:', error);
            alert('Failed to create new chat');
        }
    };

    const handleChatSelect = async (chatId) => {
        setActiveChatId(chatId);
        setLoading(true);
        try {
            const chatData = await getChatById(chatId);
            setMessages(chatData.messages || []);
        } catch (error) {
            console.error('Failed to load chat:', error);
            setMessages([]);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteChat = async (chatId) => {
        try {
            await deleteChatApi(chatId);
            setChats(chats.filter((c) => c.chat_id !== chatId));

            // If deleted chat was active, clear messages
            if (activeChatId === chatId) {
                setActiveChatId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to delete chat:', error);
            alert('Failed to delete chat');
        }
    };

    const handleSendMessage = async (content) => {
        // GUEST MODE - Use backend guest API
        if (!isAuthenticated) {
            if (!guestSessionId) {
                alert('Initializing guest session, please try again...');
                return;
            }

            const userMessage = { role: 'user', content, timestamp: new Date() };
            setGuestMessages((prev) => [...prev, userMessage]);
            setLoading(true);

            try {
                const response = await sendGuestMessage(guestSessionId, content);
                const aiMessage = {
                    role: 'assistant',
                    content: response.assistant_message,
                    timestamp: new Date(),
                };
                setGuestMessages((prev) => [...prev, aiMessage]);
            } catch (error) {
                console.error('Failed to send guest message:', error);
                // If session expired, create new one
                if (error.response?.status === 404) {
                    localStorage.removeItem('guest_session_id');
                    await initGuestSession();
                    alert('Session expired. Please try sending your message again.');
                } else {
                    const errorMessage = {
                        role: 'assistant',
                        content: 'Sorry, I encountered an error. Please try again.',
                        timestamp: new Date(),
                    };
                    setGuestMessages((prev) => [...prev, errorMessage]);
                }
            } finally {
                setLoading(false);
            }
            return;
        }

        // AUTHENTICATED MODE
        // Create chat if none exists, then send the message
        let chatId = activeChatId;
        if (!chatId) {
            try {
                const newChat = await createChat();
                setChats([newChat, ...chats]);
                setActiveChatId(newChat.chat_id);
                chatId = newChat.chat_id;
            } catch (error) {
                console.error('Failed to create chat:', error);
                alert('Failed to create new chat');
                return;
            }
        }

        const userMessage = { role: 'user', content, created_at: new Date().toISOString() };
        setMessages((prev) => [...prev, userMessage]);
        setLoading(true);

        try {
            const response = await sendMessage(chatId, content);
            const aiMessage = {
                role: 'assistant',
                content: response.assistant_message,
                created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error('Failed to send message:', error);
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleImageUploadClick = () => {
        if (!isAuthenticated) {
            // Guest mode - check session
            if (!guestSessionId) {
                alert('Initializing guest session, please try again...');
                return;
            }
            setShowImageUploader(true);
            return;
        }

        // Authenticated mode - allow upload even without active chat
        setShowImageUploader(true);
    };

    const handleImageUpload = async (file) => {
        setLoading(true);

        try {
            // GUEST MODE
            if (!isAuthenticated) {
                if (!guestSessionId) {
                    throw new Error('No guest session available');
                }

                const response = await uploadGuestImage(guestSessionId, file);

                const aiMessage = {
                    role: 'assistant',
                    content: response.assistant_message,
                    timestamp: new Date(),
                };
                setGuestMessages((prev) => [...prev, aiMessage]);
                setShowImageUploader(false);
                return;
            }

            // AUTHENTICATED MODE - Create chat if needed
            let chatId = activeChatId;
            if (!chatId) {
                try {
                    const newChat = await createChat();
                    setChats([newChat, ...chats]);
                    setActiveChatId(newChat.chat_id);
                    chatId = newChat.chat_id;
                } catch (error) {
                    console.error('Failed to create chat:', error);
                    throw new Error('Failed to create chat');
                }
            }

            const response = await uploadImage(chatId, file);

            // Add assistant response to messages
            const aiMessage = {
                role: 'assistant',
                content: response.assistant_message,
                created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, aiMessage]);
            setShowImageUploader(false);
        } catch (error) {
            console.error('Failed to upload image:', error);
            throw new Error(error.response?.data?.detail || 'Upload failed');
        } finally {
            setLoading(false);
        }
    };



    const handleLogout = () => {
        logout();
        setMobileMenuOpen(false);
        navigate('/');
    };

    const handleHome = () => {
        // Only for guest mode
        if (window.confirm('Return to home page? Your guest session will be cleared.')) {
            localStorage.removeItem('guest_session_id');
            setMobileMenuOpen(false);
            navigate('/');
        }
    };

    const toggleMobileMenu = () => {
        setMobileMenuOpen(prev => !prev);
    };

    return (
        <div className="chat-page">
            {/* Mobile menu toggle button */}
            {isAuthenticated && (
                <button
                    className="mobile-menu-toggle"
                    onClick={toggleMobileMenu}
                    aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
                >
                    {mobileMenuOpen ? (
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    ) : (
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="3" y1="12" x2="21" y2="12"></line>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                    )}
                </button>
            )}

            {/* Sidebar overlay for mobile */}
            {isAuthenticated && mobileMenuOpen && (
                <div
                    className="sidebar-overlay active"
                    onClick={() => setMobileMenuOpen(false)}
                />
            )}

            {/* Show sidebar only for authenticated users */}
            {isAuthenticated && (
                <ChatSidebar
                    chats={chats}
                    activeChatId={activeChatId}
                    onChatSelect={handleChatSelect}
                    onNewChat={handleNewChat}
                    onDeleteChat={handleDeleteChat}
                    loading={chatListLoading}
                    mobileOpen={mobileMenuOpen}
                />
            )}

            <div className="chat-main">
                {/* Guest mode banner */}
                {!isAuthenticated && (
                    <div className="guest-banner">
                        <div className="guest-banner-content">
                            <p>
                                You're chatting as a <strong>guest</strong>. Your messages will not be saved.{' '}
                                <button className="link-btn" onClick={() => navigate('/auth')}>
                                    Sign in
                                </button>{' '}
                                to unlock full features.
                            </p>
                            <button className="btn btn-secondary btn-sm" onClick={handleHome}>
                                Home
                            </button>
                        </div>
                    </div>
                )}

                {/* Authenticated mode toolbar */}
                {isAuthenticated && (
                    <div className="chat-toolbar">
                        <div className="toolbar-user">
                            <span>{user?.name}</span>
                        </div>
                        <div className="toolbar-actions">
                            <button className="btn btn-danger" onClick={handleLogout}>
                                Logout
                            </button>
                        </div>
                    </div>
                )}

                <ChatWindow
                    messages={isAuthenticated ? messages : guestMessages}
                    onSendMessage={handleSendMessage}
                    loading={loading}
                    showImageUpload={isAuthenticated || (guestSessionId !== null)}
                    onImageUpload={handleImageUploadClick}
                />
            </div>

            {/* Modals */}
            {showImageUploader && (
                <ImageUploader
                    onUpload={handleImageUpload}
                    onClose={() => setShowImageUploader(false)}
                    loading={loading}
                />
            )}
        </div>
    );
};

export default ChatPage;
