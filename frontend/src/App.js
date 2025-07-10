import React, { useState, useEffect, useContext, createContext } from 'react';
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching current user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (username, email, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { username, email, password });
      return { success: true, user: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user,
    isSuperUser: user?.is_super_user || false
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Components
const Header = ({ activeTab, setActiveTab, setShowAuth }) => {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <header className="bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">📺 Live Streaming Platform</h1>
          
          {isAuthenticated ? (
            <div className="flex items-center space-x-4">
              <span className="text-sm">Welcome, {user.username}!</span>
              {user.is_super_user && (
                <span className="bg-yellow-500 text-yellow-900 px-2 py-1 rounded-full text-xs font-semibold">
                  Super User
                </span>
              )}
              <button
                onClick={logout}
                className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg text-sm transition-colors"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowAuth(true)}
                className="bg-white text-purple-600 hover:bg-gray-100 px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
              >
                Login / Register
              </button>
            </div>
          )}
        </div>
        
        <nav className="mt-4">
          <div className="flex space-x-6">
            <button
              onClick={() => setActiveTab('channels')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'channels' 
                  ? 'bg-white text-purple-600 font-semibold' 
                  : 'text-white hover:bg-white/20'
              }`}
            >
              Browse Channels
            </button>
            
            {isAuthenticated && (
              <>
                <button
                  onClick={() => setActiveTab('my-channels')}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    activeTab === 'my-channels' 
                      ? 'bg-white text-purple-600 font-semibold' 
                      : 'text-white hover:bg-white/20'
                  }`}
                >
                  My Channels
                </button>
                <button
                  onClick={() => setActiveTab('add-channel')}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    activeTab === 'add-channel' 
                      ? 'bg-white text-purple-600 font-semibold' 
                      : 'text-white hover:bg-white/20'
                  }`}
                >
                  Add Channel
                </button>
                {user.is_super_user && (
                  <button
                    onClick={() => setActiveTab('admin')}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      activeTab === 'admin' 
                        ? 'bg-white text-purple-600 font-semibold' 
                        : 'text-white hover:bg-white/20'
                    }`}
                  >
                    Admin Panel
                  </button>
                )}
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
};

const LoginForm = ({ onClose }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const result = await login(formData.username, formData.password);
        if (result.success) {
          if (onClose) onClose();
        } else {
          setError(result.error);
        }
      } else {
        const result = await register(formData.username, formData.email, formData.password);
        if (result.success) {
          setIsLogin(true);
          setError('');
          setFormData({ username: '', email: '', password: '' });
          alert('Registration successful! Please login.');
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        )}
        
        <h2 className="text-3xl font-bold text-center mb-8 text-gray-800">
          {isLogin ? 'Login' : 'Register'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-colors"
              required
            />
          </div>

          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-colors"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-colors"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-purple-600 hover:text-purple-800 font-medium"
          >
            {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  );
};

const ChannelCard = ({ channel, onPlay, showActions = false, onEdit, onDelete }) => {
  const { isSuperUser } = useAuth();
  
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
      <div className="aspect-video bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center">
        {channel.logo ? (
          <img
            src={channel.logo}
            alt={channel.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-6xl">📺</div>
        )}
      </div>
      
      <div className="p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">{channel.name}</h3>
        <p className="text-gray-600 mb-4 line-clamp-2">{channel.description}</p>
        
        {channel.category && (
          <span className="inline-block bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium mb-4">
            {channel.category}
          </span>
        )}
        
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {channel.urls.length} URL{channel.urls.length > 1 ? 's' : ''}
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => onPlay(channel)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              ▶️ Play
            </button>
            
            {showActions && (
              <>
                <button
                  onClick={() => onEdit(channel)}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(channel)}
                  className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Delete
                </button>
              </>
            )}
            
            {isSuperUser && (
              <button
                onClick={() => downloadM3U8(channel.id)}
                className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                📥 M3U8
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const VideoPlayer = ({ channel, onClose }) => {
  const [currentUrlIndex, setCurrentUrlIndex] = useState(0);
  const [error, setError] = useState('');

  const handleUrlChange = (index) => {
    setCurrentUrlIndex(index);
    setError('');
  };

  const handleVideoError = () => {
    setError('Failed to load video stream');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-screen overflow-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">{channel.name}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ✕
            </button>
          </div>
          
          <div className="aspect-video bg-black rounded-lg mb-4">
            {channel.urls[currentUrlIndex] ? (
              <video
                key={currentUrlIndex}
                controls
                autoPlay
                className="w-full h-full rounded-lg"
                onError={handleVideoError}
              >
                <source src={channel.urls[currentUrlIndex]} type="application/x-mpegURL" />
                <source src={channel.urls[currentUrlIndex]} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white">
                No video URL available
              </div>
            )}
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              {error}
            </div>
          )}
          
          {channel.urls.length > 1 && (
            <div className="mb-4">
              <h3 className="text-lg font-semibold mb-2">Available Streams:</h3>
              <div className="flex flex-wrap gap-2">
                {channel.urls.map((url, index) => (
                  <button
                    key={index}
                    onClick={() => handleUrlChange(index)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                      index === currentUrlIndex
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Stream {index + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <p className="text-gray-600">{channel.description}</p>
        </div>
      </div>
    </div>
  );
};

const ChannelForm = ({ channel, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: channel?.name || '',
    description: channel?.description || '',
    category: channel?.category || '',
    logo: channel?.logo || '',
    urls: channel?.urls || ['']
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUrlChange = (index, value) => {
    const newUrls = [...formData.urls];
    newUrls[index] = value;
    setFormData({...formData, urls: newUrls});
  };

  const addUrl = () => {
    setFormData({...formData, urls: [...formData.urls, '']});
  };

  const removeUrl = (index) => {
    const newUrls = formData.urls.filter((_, i) => i !== index);
    setFormData({...formData, urls: newUrls});
  };

  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setFormData({...formData, logo: e.target.result});
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const filteredUrls = formData.urls.filter(url => url.trim() !== '');
      const channelData = {
        ...formData,
        urls: filteredUrls
      };

      if (channel) {
        await axios.put(`${API}/channels/${channel.id}`, channelData);
      } else {
        await axios.post(`${API}/channels`, channelData);
      }

      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-screen overflow-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6">
            {channel ? 'Edit Channel' : 'Add New Channel'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Channel Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none resize-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                placeholder="e.g., Sports, News, Entertainment"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Logo
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleLogoChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
              {formData.logo && (
                <div className="mt-2">
                  <img
                    src={formData.logo}
                    alt="Logo preview"
                    className="w-24 h-24 object-cover rounded-lg border"
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Streaming URLs
              </label>
              {formData.urls.map((url, index) => (
                <div key={index} className="flex mb-2">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => handleUrlChange(index, e.target.value)}
                    placeholder="https://example.com/stream.m3u8"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => removeUrl(index)}
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-r-lg transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={addUrl}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Add URL
              </button>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Saving...' : 'Save Channel'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

const downloadM3U8 = async (channelId) => {
  try {
    const response = await axios.get(`${API}/channels/${channelId}/m3u8`);
    const { m3u8_urls } = response.data;
    
    if (m3u8_urls.length > 0) {
      alert(`M3U8 URLs for download:\n${m3u8_urls.join('\n')}`);
    } else {
      alert('No M3U8 URLs found for this channel');
    }
  } catch (error) {
    alert('Error fetching M3U8 URLs: ' + (error.response?.data?.detail || 'Unknown error'));
  }
};

const Dashboard = ({ showAuth, setShowAuth }) => {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState('channels');
  const [channels, setChannels] = useState([]);
  const [myChannels, setMyChannels] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingChannel, setEditingChannel] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  const fetchChannels = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCategory) params.append('category', selectedCategory);
      
      const response = await axios.get(`${API}/channels?${params}`);
      setChannels(response.data);
    } catch (error) {
      console.error('Error fetching channels:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyChannels = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/my-channels`);
      setMyChannels(response.data);
    } catch (error) {
      console.error('Error fetching my channels:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    if (activeTab === 'channels') {
      fetchChannels();
    } else if (activeTab === 'my-channels' && isAuthenticated) {
      fetchMyChannels();
    }
  }, [activeTab, searchTerm, selectedCategory, isAuthenticated]);

  // Redirect to channels tab if user is not authenticated and tries to access protected tabs
  useEffect(() => {
    if (!isAuthenticated && ['my-channels', 'add-channel', 'admin'].includes(activeTab)) {
      setActiveTab('channels');
    }
  }, [isAuthenticated, activeTab]);

  const handlePlay = (channel) => {
    setSelectedChannel(channel);
    setShowPlayer(true);
  };

  const handleEdit = (channel) => {
    if (!isAuthenticated) {
      setShowAuth(true);
      return;
    }
    setEditingChannel(channel);
    setShowForm(true);
  };

  const handleDelete = async (channel) => {
    if (!isAuthenticated) {
      setShowAuth(true);
      return;
    }
    if (window.confirm('Are you sure you want to delete this channel?')) {
      try {
        await axios.delete(`${API}/channels/${channel.id}`);
        fetchMyChannels();
      } catch (error) {
        alert('Error deleting channel: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    }
  };

  const handleSave = () => {
    setShowForm(false);
    setEditingChannel(null);
    if (activeTab === 'my-channels') {
      fetchMyChannels();
    } else {
      fetchChannels();
    }
  };

  const handleAddChannel = () => {
    if (!isAuthenticated) {
      setShowAuth(true);
      return;
    }
    setActiveTab('add-channel');
  };

  const renderChannels = () => {
    const channelsToShow = activeTab === 'my-channels' ? myChannels : channels;
    const showActions = activeTab === 'my-channels' && isAuthenticated;

    if (loading) {
      return <div className="text-center py-8">Loading channels...</div>;
    }

    if (channelsToShow.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-4">
            {activeTab === 'my-channels' ? 'No channels found. Create your first channel!' : 'No channels available'}
          </div>
          {activeTab === 'channels' && (
            <button
              onClick={handleAddChannel}
              className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
            >
              {isAuthenticated ? 'Add First Channel' : 'Login to Add Channel'}
            </button>
          )}
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {channelsToShow.map((channel) => (
          <ChannelCard
            key={channel.id}
            channel={channel}
            onPlay={handlePlay}
            showActions={showActions}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        setShowAuth={setShowAuth}
      />
      
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'channels' && (
          <div className="mb-8">
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search channels..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                />
              </div>
              <div className="w-full md:w-64">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                >
                  <option value="">All Categories</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleAddChannel}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
              >
                {isAuthenticated ? 'Add Channel' : 'Login to Add'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'add-channel' && isAuthenticated ? (
          <ChannelForm
            onSave={handleSave}
            onCancel={() => setActiveTab('my-channels')}
          />
        ) : (
          renderChannels()
        )}
      </main>

      {showPlayer && selectedChannel && (
        <VideoPlayer
          channel={selectedChannel}
          onClose={() => setShowPlayer(false)}
        />
      )}

      {showForm && (
        <ChannelForm
          channel={editingChannel}
          onSave={handleSave}
          onCancel={() => setShowForm(false)}
        />
      )}
    </div>
  );
};

function App() {
  const { isAuthenticated, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {showAuth ? (
        <LoginForm onClose={() => setShowAuth(false)} />
      ) : (
        <Dashboard showAuth={showAuth} setShowAuth={setShowAuth} />
      )}
    </div>
  );
}

export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}