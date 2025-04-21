import React, { useState, useEffect, ChangeEvent } from 'react'
import { Toaster } from 'react-hot-toast'
import axios from 'axios'
import { PlusIcon, TrashIcon, PlayIcon, PauseIcon } from '@heroicons/react/24/outline'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { LoginPage } from './components/LoginPage'

interface Wallet {
  address: string
  name?: string
}

interface BotSettings {
  max_sol_per_tx: number
  slippage: number
  delay_ms: number
  blacklisted_tokens: string[]
}

interface BotState {
  is_running: boolean
  tracked_wallets: Wallet[]
  settings: BotSettings
}

function Dashboard() {
  const { logout } = useAuth();
  const [botState, setBotState] = useState<BotState>({
    is_running: false,
    tracked_wallets: [],
    settings: {
      max_sol_per_tx: 0.1,
      slippage: 1.0,
      delay_ms: 1000,
      blacklisted_tokens: []
    }
  })
  const [newWallet, setNewWallet] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchBotState()
  }, [])

  const fetchBotState = async () => {
    try {
      const response = await axios.get<BotState>('http://localhost:8000/state')
      setBotState(response.data)
    } catch (error) {
      console.error('Error fetching bot state:', error)
    }
  }

  const handleAddWallet = async () => {
    if (!newWallet.trim()) return

    try {
      await axios.post('http://localhost:8000/wallets', {
        address: newWallet.trim()
      })
      setNewWallet('')
      fetchBotState()
    } catch (error) {
      console.error('Error adding wallet:', error)
    }
  }

  const handleRemoveWallet = async (address: string) => {
    try {
      await axios.delete(`http://localhost:8000/wallets/${address}`)
      fetchBotState()
    } catch (error) {
      console.error('Error removing wallet:', error)
    }
  }

  const handleToggleBot = async () => {
    try {
      const response = await axios.post<{ is_running: boolean }>('http://localhost:8000/toggle')
      setBotState(prev => ({ ...prev, is_running: response.data.is_running }))
    } catch (error) {
      console.error('Error toggling bot:', error)
    }
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>, field: keyof BotSettings) => {
    const value = e.target.type === 'number' ? 
      (field === 'delay_ms' ? parseInt(e.target.value) : parseFloat(e.target.value)) : 
      e.target.value;

    setBotState(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        [field]: value
      }
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster position="top-right" />
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-2xl font-bold">Solana Meme Coin Copy Trader</h1>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
            
            {/* Bot Status */}
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Bot Status</h2>
                <button
                  onClick={handleToggleBot}
                  className={`px-4 py-2 rounded-md flex items-center ${
                    botState.is_running
                      ? 'bg-green-500 hover:bg-green-600'
                      : 'bg-red-500 hover:bg-red-600'
                  } text-white`}
                >
                  {botState.is_running ? (
                    <>
                      <PauseIcon className="h-5 w-5 mr-2" />
                      Stop Bot
                    </>
                  ) : (
                    <>
                      <PlayIcon className="h-5 w-5 mr-2" />
                      Start Bot
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* Wallet Management */}
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-4">Tracked Wallets</h2>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newWallet}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setNewWallet(e.target.value)}
                  placeholder="Enter wallet address"
                  className="flex-1 px-4 py-2 border rounded-md"
                />
                <button
                  onClick={handleAddWallet}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Wallet
                </button>
              </div>
              
              <div className="space-y-2">
                {botState.tracked_wallets.map((wallet) => (
                  <div
                    key={wallet.address}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                  >
                    <span className="font-mono">{wallet.address}</span>
                    <button
                      onClick={() => handleRemoveWallet(wallet.address)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Settings */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Bot Settings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Max SOL per Transaction
                  </label>
                  <input
                    type="number"
                    value={botState.settings.max_sol_per_tx}
                    onChange={(e) => handleInputChange(e, 'max_sol_per_tx')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Slippage (%)
                  </label>
                  <input
                    type="number"
                    value={botState.settings.slippage}
                    onChange={(e) => handleInputChange(e, 'slippage')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Delay (ms)
                  </label>
                  <input
                    type="number"
                    value={botState.settings.delay_ms}
                    onChange={(e) => handleInputChange(e, 'delay_ms')}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

function AppContent() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Dashboard /> : <LoginPage />;
}

export default App 