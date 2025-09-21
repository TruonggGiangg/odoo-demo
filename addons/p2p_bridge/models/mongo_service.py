from pymongo import MongoClient
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self):
        try:
            self.client = MongoClient("mongodb+srv://pnttoan1474:hcLcr7dk65Ry1g3s@cluster0.o63zzed.mongodb.net/DevP2PLending")
            self.db = self.client["DevP2PLending"]
            _logger.info("MongoDB connection established")
        except Exception as e:
            _logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_wallet(self, user_id):
        """Lấy thông tin ví tổng hợp theo user_id (Mongo _id dưới dạng string)"""
        try:
            user = self.db.users.find_one({"_id": user_id})
            if not user:
                return None
            usdt_wallets = user.get('usdtWallets', []) or []
            total_balance = sum(w.get('balance', 0) or 0 for w in usdt_wallets)
            return {
                'user_id': str(user.get('_id')),
                'balance': float(total_balance),
                'updated_at': datetime.utcnow(),
                'currency': 'VND'
            }
        except Exception as e:
            _logger.error(f"Error getting wallet for user {user_id}: {e}")
            return None
    
    def get_wallets_count(self):
        try:
            pipeline = [
                {
                    "$project": {
                        "wallet_count": {
                            "$add": [
                                {"$size": {"$ifNull": ["$usdtWallets", []]}},
                                {"$size": {"$ifNull": ["$externalWallets", []]}}
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_wallets": {"$sum": "$wallet_count"}
                    }
                }
            ]
            result = list(self.db.users.aggregate(pipeline))
            return result[0]["total_wallets"] if result else 0
        except Exception as e:
            _logger.error(f"Error counting wallets: {e}")
            return 0


    def get_all_wallets(self):
        """Tổng hợp ví theo user (sum balance USDT wallets) và trả về dạng {user_id, balance, currency, updated_at}"""
        try:
            pipeline = [
                {
                    "$project": {
                        "user_id": {"$toString": "$_id"},
                        "total_balance": {
                            "$sum": {
                                "$map": {
                                    "input": {"$ifNull": ["$usdtWallets", []]},
                                    "as": "w",
                                    "in": {"$ifNull": ["$$w.balance", 0]}
                                }
                            }
                        }
                    }
                }
            ]
            rows = list(self.db.users.aggregate(pipeline))
            return [
                {
                    'user_id': r.get('user_id'),
                    'balance': float(r.get('total_balance', 0) or 0),
                    'currency': 'USDT',
                    'updated_at': datetime.utcnow(),
                }
                for r in rows
            ]
        except Exception as e:
            _logger.error(f"Error getting all wallets: {e}")
            return []


    def get_loans(self):
        """Lấy tất cả loans"""
        try:
            return list(self.db.loancontracts.find())
        except Exception as e:
            _logger.error(f"Error getting loans: {e}")
            return []

    def get_loan(self, loan_id):
        """Lấy thông tin loan theo ID"""
        try:
            return self.db.loancontracts.find_one({"_id": loan_id})
        except Exception as e:
            _logger.error(f"Error getting loan {loan_id}: {e}")
            return None

    def get_loans_by_borrower(self, borrower_id):
        """Lấy loans theo borrower_id"""
        try:
            return list(self.db.loancontracts.find({"borrower_id": borrower_id}))
        except Exception as e:
            _logger.error(f"Error getting loans for borrower {borrower_id}: {e}")
            return []

    def get_loans_by_status(self, status):
        """Lấy loans theo status"""
        try:
            return list(self.db.loancontracts.find({"status": status}))
        except Exception as e:
            _logger.error(f"Error getting loans with status {status}: {e}")
            return []

    def get_transactions(self, user_id=None):
        """Lấy transactions"""
        try:
            if user_id:
                return list(self.db.transactions.find({"user_id": user_id}))
            else:
                return list(self.db.transactions.find())
        except Exception as e:
            _logger.error(f"Error getting transactions: {e}")
            return []

    def get_users(self):
        """Lấy tất cả users"""
        try:
            return list(self.db.users.find())
        except Exception as e:
            _logger.error(f"Error getting users: {e}")
            return []

    def get_user(self, user_id):
        """Lấy thông tin user"""
        try:
            return self.db.users.find_one({"user_id": user_id})
        except Exception as e:
            _logger.error(f"Error getting user {user_id}: {e}")
            return None

    def test_connection(self):
        """Test kết nối MongoDB"""
        try:
            # Thử ping database
            self.client.admin.command('ping')
            _logger.info("MongoDB connection test successful")
            return True
        except Exception as e:
            _logger.error(f"MongoDB connection test failed: {e}")
            return False

    def get_database_stats(self):
        """Lấy thống kê database"""
        try:
            stats = {
                'wallets_count': self.get_wallets_count(),
                'loancontracts_count': self.db.loancontracts.count_documents({}),
                'users_count': self.db.users.count_documents({}),
                'transactions_count': self.db.transactions.count_documents({})
            }
            return stats
        except Exception as e:
            _logger.error(f"Error getting database stats: {e}")
            return {}

    def close_connection(self):
        """Đóng kết nối MongoDB"""
        try:
            self.client.close()
            _logger.info("MongoDB connection closed")
        except Exception as e:
            _logger.error(f"Error closing MongoDB connection: {e}")
