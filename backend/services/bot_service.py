import os
import time
import logging
import threading
from typing import List, Dict, Optional
from datetime import datetime
import json
import asyncio
import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.publickey import PublicKey
from jupiter import Jupiter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class BotService:
    def __init__(self):
        self.is_running = False
        self.tracked_wallets: List[str] = []
        self.settings = {
            'max_sol_per_tx': float(os.getenv('MAX_SOL_PER_TX', '0.1')),
            'slippage': float(os.getenv('SLIPPAGE', '1.0')),
            'delay_ms': int(os.getenv('DELAY_MS', '1000')),
            'blacklisted_tokens': []
        }
        self.trade_history: List[Dict] = []
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.jupiter_api_key = os.getenv('JUPITER_API_KEY')
        
        if not all([self.private_key, self.helius_api_key, self.jupiter_api_key]):
            raise ValueError("Missing required environment variables")
        
        self.wallet = Keypair.from_secret_key(bytes.fromhex(self.private_key))
        self.jupiter = Jupiter(self.jupiter_api_key)
        self.solana_client = AsyncClient(os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com'))
        
    async def start(self):
        if self.is_running:
            return {"status": "already running"}
        
        self.is_running = True
        threading.Thread(target=self._run_bot_loop, daemon=True).start()
        return {"status": "started"}
    
    async def stop(self):
        self.is_running = False
        return {"status": "stopped"}
    
    async def get_status(self):
        return {
            "is_running": self.is_running,
            "tracked_wallets": self.tracked_wallets,
            "settings": self.settings,
            "last_trade": self.trade_history[-1] if self.trade_history else None
        }
    
    def _run_bot_loop(self):
        asyncio.run(self._monitor_transactions())
    
    async def _monitor_transactions(self):
        while self.is_running:
            try:
                for wallet in self.tracked_wallets:
                    await self._check_wallet_transactions(wallet)
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logging.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _check_wallet_transactions(self, wallet_address: str):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/transactions"
                headers = {"Authorization": f"Bearer {self.helius_api_key}"}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        transactions = await response.json()
                        for tx in transactions:
                            if self._is_swap_transaction(tx):
                                await self._copy_trade(tx, wallet_address)
        except Exception as e:
            logging.error(f"Error checking wallet {wallet_address}: {e}")
    
    def _is_swap_transaction(self, transaction: Dict) -> bool:
        # Check if transaction contains token swaps
        # This is a simplified check - you might need to adjust based on actual transaction structure
        return any(
            log.get('programId') == 'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB'  # Jupiter program ID
            for log in transaction.get('logs', [])
        )
    
    async def _copy_trade(self, transaction: Dict, copied_wallet: str):
        try:
            # Extract token swap details from transaction
            swap_details = self._extract_swap_details(transaction)
            if not swap_details:
                return
            
            # Apply delay if configured
            if self.settings['delay_ms'] > 0:
                await asyncio.sleep(self.settings['delay_ms'] / 1000)
            
            # Execute trade using Jupiter
            trade_result = await self._execute_jupiter_trade(swap_details)
            
            # Log the trade
            self._log_trade(swap_details, copied_wallet, trade_result)
            
        except Exception as e:
            logging.error(f"Error copying trade: {e}")
    
    def _extract_swap_details(self, transaction: Dict) -> Optional[Dict]:
        # Extract token swap details from transaction
        # This is a placeholder - you'll need to implement actual extraction logic
        # based on the transaction structure from Helius
        try:
            return {
                'input_mint': transaction.get('inputMint'),
                'output_mint': transaction.get('outputMint'),
                'amount': transaction.get('amount'),
                'slippage': self.settings['slippage']
            }
        except Exception as e:
            logging.error(f"Error extracting swap details: {e}")
            return None
    
    async def _execute_jupiter_trade(self, swap_details: Dict) -> Dict:
        try:
            # Get quote from Jupiter
            quote = await self.jupiter.get_quote(
                input_mint=swap_details['input_mint'],
                output_mint=swap_details['output_mint'],
                amount=swap_details['amount'],
                slippage=swap_details['slippage']
            )
            
            # Execute the swap
            swap_result = await self.jupiter.swap(
                quote=quote,
                wallet=self.wallet
            )
            
            return {
                'status': 'success',
                'transaction_id': swap_result.get('transaction_id'),
                'amount': swap_details['amount']
            }
            
        except Exception as e:
            logging.error(f"Error executing Jupiter trade: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _log_trade(self, swap_details: Dict, copied_wallet: str, trade_result: Dict):
        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'copied_wallet': copied_wallet,
            'input_mint': swap_details['input_mint'],
            'output_mint': swap_details['output_mint'],
            'amount': swap_details['amount'],
            'slippage': swap_details['slippage'],
            'result': trade_result
        }
        
        self.trade_history.append(trade_log)
        
        # Save to log file
        with open('trade_history.json', 'a') as f:
            f.write(json.dumps(trade_log) + '\n')
        
        logging.info(f"Logged trade: {trade_log}") 