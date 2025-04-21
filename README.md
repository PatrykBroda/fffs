# Solana Meme Coin Copy Trading Bot

A full-stack web application for copying meme coin trades on Solana. The bot monitors specified wallets for Raydium/Jupiter buys and automatically copies trades with configurable parameters.

## Features

- Track multiple Solana wallets
- Monitor Raydium/Jupiter DEX trades
- Automatic trade copying with configurable parameters
- Live feed of copied trades
- Pause/Resume functionality
- Customizable settings (slippage, blacklist, delay)

## Tech Stack

- **Frontend:** React (Vite) + TailwindCSS
- **Backend:** Python + FastAPI
- **APIs:** Helius (Solana transactions), Jupiter (DEX aggregator)

## Project Structure

```
.
├── frontend/           # React + Vite frontend
├── backend/           # Python FastAPI backend
├── bot/              # Core trading bot logic
└── .env              # Environment variables
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.9+
- Solana CLI tools
- Helius API key
- Jupiter API key
- Solana private key

### Environment Variables

Create a `.env` file in the root directory with:

```env
HELIUS_API_KEY=your_helius_api_key
JUPITER_API_KEY=your_jupiter_api_key
SOLANA_PRIVATE_KEY=your_solana_private_key
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Start the backend server
2. Start the frontend development server
3. Open the web interface
4. Add wallets to track
5. Configure bot settings
6. Enable the bot

## Security Notes

- Never commit your `.env` file
- Keep your private keys secure
- Use appropriate slippage settings
- Consider implementing rate limiting