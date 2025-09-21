from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SyncWizard(models.TransientModel):
    _name = 'p2p.sync.wizard'
    _description = 'P2P Sync Wizard'

    def test_mongodb_connection(self):
        """Test kết nối MongoDB"""
        try:
            from ..models.mongo_service import MongoService
            mongo = MongoService()
            if mongo.test_connection():
                stats = mongo.get_database_stats()
                message = f"""
                ✅ Kết nối MongoDB thành công!
                
                Thống kê database:
                - Wallets: {stats.get('wallets_count', 0)}
                - Loans: {stats.get('loancontracts_count', 0)} 
                - Users: {stats.get('users_count', 0)}
                - Transactions: {stats.get('transactions_count', 0)}
                """
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Thành công',
                        'message': message,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError("❌ Không thể kết nối đến MongoDB")
        except Exception as e:
            raise UserError(f"❌ Lỗi kết nối MongoDB: {str(e)}")

    def _ensure_columns_exist(self):
        """Đảm bảo tất cả columns tồn tại trong database"""
        try:
            self.env.cr.execute("""
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "contractId" VARCHAR;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "willing" TEXT;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "maturity_date" DATE;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "capital" NUMERIC;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "created_date" DATE;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "monthly_principal_pay" NUMERIC;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "monthly_interest_pay" NUMERIC;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "monthly_pay" NUMERIC;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "entirely_pay" NUMERIC;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "total_notes" INTEGER;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "invested_notes" INTEGER;
            """)
            self.env.cr.commit()
        except Exception as e:
            _logger.warning(f"Could not add columns: {e}")

    def _clean_old_data(self):
        """Xóa dữ liệu cũ trước khi sync"""
        try:
            # Xóa tất cả loans cũ
            loan_model = self.env['p2p.loan']
            old_loans = loan_model.search([])
            if old_loans:
                old_loans.unlink()
                _logger.info(f"Deleted {len(old_loans)} old loan records")
            
            # Xóa tất cả wallets cũ
            wallet_model = self.env['p2p.wallet']
            old_wallets = wallet_model.search([])
            if old_wallets:
                old_wallets.unlink()
                _logger.info(f"Deleted {len(old_wallets)} old wallet records")
                
        except Exception as e:
            _logger.warning(f"Could not clean old data: {e}")

    def sync_all_data(self):
        """Đồng bộ tất cả dữ liệu"""
        try:
            # Đảm bảo columns tồn tại trước khi sync
            self._ensure_columns_exist()
            
            # Xóa dữ liệu cũ trước khi sync
            self._clean_old_data()
            
            # Sync wallets
            wallet_model = self.env['p2p.wallet']
            from ..models.mongo_service import MongoService
            mongo = MongoService()
            
            wallets = mongo.get_all_wallets()
            synced_wallets = 0
            for wallet_data in wallets:
                user_id = wallet_data.get('user_id')
                if user_id:
                    existing = wallet_model.search([('user_id', '=', user_id)])
                    if existing:
                        existing.write({
                            'wallet_balance': wallet_data.get('balance', 0),
                            'last_sync': fields.Datetime.now()
                        })
                    else:
                        wallet_model.create({
                            'user_id': user_id,
                            'wallet_balance': wallet_data.get('balance', 0),
                            'last_sync': fields.Datetime.now()
                        })
                    synced_wallets += 1

            # Sync loans
            loan_model = self.env['p2p.loan']
            loans = mongo.get_loans()
            synced_loans = 0
            for loan_data in loans:
                loan_id = loan_data.get('contractId') or loan_data.get('_id')
                if loan_id:
                    existing_loan = loan_model.search([('contractId', '=', str(loan_id))])
                    if not existing_loan:
                        # Fallback: search by loan_id if contractId not found
                        existing_loan = loan_model.search([('loan_id', '=', str(loan_id))])
                    if existing_loan:
                        existing_loan.write({
                            'contractId': str(loan_data.get('contractId') or loan_data.get('_id')),
                            'borrower_id': str(loan_data.get('borrower', '')),
                            'capital': float(loan_data.get('info', {}).get("capital", 0)),   
                            'interest_rate': float(loan_data.get("info", {}).get("rate", 0)),
                            'term_months': int(loan_data.get("info", {}).get("periodMonth", 12)),
                            'status': loan_data.get('status', 'waiting'),
                            'willing': str(loan_data.get("info", {}).get("willing", '')),
                            'maturity_date': loan_data.get("info", {}).get("maturityDate"),
                            'created_date': loan_data.get("info", {}).get("createdDate"),
                            'monthly_principal_pay': float(loan_data.get("info", {}).get("monthlyPrincipalPay", 0)),
                            'monthly_interest_pay': float(loan_data.get("info", {}).get("monthlyInterestPay", 0)),
                            'monthly_pay': float(loan_data.get("info", {}).get("monthlyPay", 0)),
                            'entirely_pay': float(loan_data.get("info", {}).get("entirelyPay", 0)),
                            'total_notes': int(loan_data.get('totalNotes', 0)),
                            'invested_notes': int(loan_data.get('investedNotes', 0)),
                            'created_at': loan_data.get('createdAt'),
                            'last_sync': fields.Datetime.now()
                        })
                    else:
                        loan_model.create({
                            'contractId': str(loan_data.get('contractId') or loan_data.get('_id')),
                            'loan_id': str(loan_data.get('contractId') or loan_data.get('_id')),  # Fallback
                            'borrower_id': str(loan_data.get('borrower', '')),
                            'capital': float(loan_data.get('info', {}).get("capital", 0)),
                            'interest_rate': float(loan_data.get("info", {}).get("rate", 0)),
                            'term_months': int(loan_data.get("info", {}).get("periodMonth", 12)),
                            'status': loan_data.get('status', 'waiting'),
                            'willing': str(loan_data.get("info", {}).get("willing", '')),
                            'maturity_date': loan_data.get("info", {}).get("maturityDate"),
                            'created_date': loan_data.get("info", {}).get("createdDate"),
                            'monthly_principal_pay': float(loan_data.get("info", {}).get("monthlyPrincipalPay", 0)),
                            'monthly_interest_pay': float(loan_data.get("info", {}).get("monthlyInterestPay", 0)),
                            'monthly_pay': float(loan_data.get("info", {}).get("monthlyPay", 0)),
                            'entirely_pay': float(loan_data.get("info", {}).get("entirelyPay", 0)),
                            'total_notes': int(loan_data.get("totalNotes", 0)),
                            'invested_notes': int(loan_data.get("investedNotes", 0)),
                            'created_at': loan_data.get('createdAt'),
                            'last_sync': fields.Datetime.now()
                        })
                    synced_loans += 1

            message = f"""
            ✅ Đồng bộ thành công!
            
            Kết quả:
            - Wallets đã đồng bộ: {synced_wallets}
            - Loans đã đồng bộ: {synced_loans}
            """
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(f"❌ Lỗi đồng bộ dữ liệu: {str(e)}")

    def fix_database_columns(self):
        """Sửa lỗi database columns"""
        try:
            self._ensure_columns_exist()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Database Fix',
                    'message': '✅ Đã thêm columns vào database thành công!',
                    'type': 'success',
                    'sticky': True,
                }
            }
        except Exception as e:
            raise UserError(f"❌ Lỗi sửa database: {str(e)}")

    def debug_loan_data(self):
        """Debug dữ liệu loan từ MongoDB"""
        try:
            from ..models.mongo_service import MongoService
            mongo = MongoService()
            loans = mongo.get_loans()
            
            if loans:
                # Lấy loan đầu tiên để debug
                sample_loan = loans[0]
                debug_info = f"""
                📊 Debug Loan Data:
                
                Sample loan structure:
                - contractId: {sample_loan.get('contractId')}
                - borrower: {sample_loan.get('borrower')}
                - status: {sample_loan.get('status')}
                - totalNotes: {sample_loan.get('totalNotes')}
                - investedNotes: {sample_loan.get('investedNotes')}
                
                Info object:
                - capital: {sample_loan.get('info', {}).get('capital')}
                - rate: {sample_loan.get('info', {}).get('rate')}
                - periodMonth: {sample_loan.get('info', {}).get('periodMonth')}
                - willing: {sample_loan.get('info', {}).get('willing')}
                
                Total loans found: {len(loans)}
                """
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Debug Loan Data',
                        'message': debug_info,
                        'type': 'info',
                        'sticky': True,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Debug Loan Data',
                        'message': '❌ Không tìm thấy loan nào trong MongoDB',
                        'type': 'warning',
                        'sticky': True,
                    }
                }
        except Exception as e:
            raise UserError(f"❌ Lỗi debug: {str(e)}")

    def clean_old_data(self):
        """Xóa dữ liệu cũ"""
        try:
            self._clean_old_data()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Clean Data',
                    'message': '✅ Đã xóa dữ liệu cũ thành công!',
                    'type': 'success',
                    'sticky': True,
                }
            }
        except Exception as e:
            raise UserError(f"❌ Lỗi xóa dữ liệu: {str(e)}")

    def open_wallets(self):
        """Mở danh sách wallets"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'P2P Wallets',
            'res_model': 'p2p.wallet',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def open_loans(self):
        """Mở danh sách loans"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'P2P Loans',
            'res_model': 'p2p.loan',
            'view_mode': 'list,form',
            'target': 'current',
        }
