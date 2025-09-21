from odoo import models, fields, api
from .mongo_service import MongoService
import logging

_logger = logging.getLogger(__name__)

# Local mapping to keep status values compatible with Odoo selection
_P2P_ALLOWED_STATUSES = {"waiting", "success", "clean", "fail"}
_P2P_STATUS_MAP = {
    # Map server-like synonyms
    "waiting": "waiting",
    "queued": "waiting",
    "processing": "success",
    "in_progress": "success",
    "done": "clean",
    "finished": "clean",
    "canceled": "fail",
    "cancel": "fail",
    # Map legacy Odoo values to server model
    "pending": "waiting",
    "active": "success",
    "completed": "clean",
    "cancelled": "fail",
}

def _normalize_status(raw_status: str) -> str:
    if not raw_status:
        return "pending"
    mapped = _P2P_STATUS_MAP.get(str(raw_status).lower(), str(raw_status).lower())
    return mapped if mapped in _P2P_ALLOWED_STATUSES else "waiting"

class P2PBridge(models.Model):
    _name = 'p2p.bridge'
    _description = 'P2P MongoDB Bridge'

    user_id = fields.Char(string='User ID', required=True)
    wallet_balance = fields.Float(compute="_compute_wallet_balance", string='Wallet Balance')
    last_sync = fields.Datetime(string='Last Sync', default=fields.Datetime.now)

    @api.depends('user_id')
    def _compute_wallet_balance(self):
        for record in self:
            try:
                mongo = MongoService()
                wallet = mongo.get_wallet(record.user_id)
                record.wallet_balance = wallet.get("balance", 0) if wallet else 0
            except Exception as e:
                _logger.error(f"Error computing wallet balance: {e}")
                record.wallet_balance = 0

    def sync_mongodb_data(self):
        """Đồng bộ dữ liệu từ MongoDB"""
        try:
            mongo = MongoService()
            
            # Sync wallets
            wallets = mongo.get_all_wallets()
            for wallet_data in wallets:
                user_id = wallet_data.get('user_id')
                if user_id:
                    existing_wallet = self.env['p2p.wallet'].search([('user_id', '=', user_id)], limit=1)
                    values = {
                        'user_id': user_id,
                        'wallet_balance': wallet_data.get('balance', 0.0) or 0.0,
                        'currency': wallet_data.get('currency') or 'USDT',
                        'last_updated': wallet_data.get('updated_at'),
                        'last_sync': fields.Datetime.now(),
                    }
                    if existing_wallet:
                        existing_wallet.write(values)
                    else:
                        self.env['p2p.wallet'].create(values)
            
            # Sync loans
            loans = mongo.get_loans()
            loan_model = self.env['p2p.loan']
            for loan_data in loans:
                loan_id = loan_data.get('_id')
                if loan_id:
                    existing_loan = loan_model.search([('loan_id', '=', str(loan_id))])
                    if existing_loan:
                        existing_loan.write({
                            'borrower_id': loan_data.get('borrower_id'),
                            'amount': loan_data.get('amount', 0),
                            'interest_rate': loan_data.get('interest_rate', 0),
                            'status': _normalize_status(loan_data.get('status')),
                            'description': loan_data.get('description', ''),
                            'last_sync': fields.Datetime.now()
                        })
                    else:
                        loan_model.create({
                            'loan_id': str(loan_id),
                            'borrower_id': loan_data.get('borrower_id'),
                            'amount': loan_data.get('amount', 0),
                            'interest_rate': loan_data.get('interest_rate', 0),
                            'term_months': loan_data.get('term_months', 12),
                            'status': _normalize_status(loan_data.get('status')),
                            'description': loan_data.get('description', ''),
                            'created_at': loan_data.get('created_at'),
                            'last_sync': fields.Datetime.now()
                        })
            
            _logger.info("MongoDB sync completed successfully")
            
        except Exception as e:
            _logger.error(f"Error syncing MongoDB data: {e}")

class P2PWallet(models.Model):
    _name = 'p2p.wallet'
    _description = 'P2P Wallet'
    _rec_name = 'user_id'

    user_id = fields.Char(string='User ID', required=True)
    wallet_balance = fields.Float(string='Balance', default=0.0)
    currency = fields.Char(string='Currency', default='VND')
    last_updated = fields.Datetime(string='Last Updated', default=fields.Datetime.now)
    last_sync = fields.Datetime(string='Last Sync', default=fields.Datetime.now)

    def sync_mongodb_data(self):
        """Đồng bộ dữ liệu từ MongoDB - tương thích với cron job"""
        try:
            # Gọi method từ P2PBridge model
            bridge_model = self.env['p2p.bridge']
            bridge_model.sync_mongodb_data()
            _logger.info("MongoDB sync called from P2PWallet model")
        except Exception as e:
            _logger.error(f"Error calling sync from P2PWallet: {e}")

    def sync_from_mongodb(self):
        """Đồng bộ wallet từ MongoDB"""
        try:
            mongo = MongoService()
            wallet = mongo.get_wallet(self.user_id)
            if wallet:
                self.write({
                    'wallet_balance': wallet.get('balance', 0),
                    'last_updated': wallet.get('updated_at'),
                    'last_sync': fields.Datetime.now()
                })
        except Exception as e:
            _logger.error(f"Error syncing wallet {self.user_id}: {e}")

class P2PLoan(models.Model):
    _name = 'p2p.loan'
    _description = 'P2P Loan'
    _rec_name = 'contractId'

    contractId = fields.Char(string='Contract ID')
    loan_id = fields.Char(string='Loan ID')
    borrower_id = fields.Char(string='Borrower ID', required=True)
    capital = fields.Float(string='Capital')
    interest_rate = fields.Float(string='Interest Rate (%)')
    term_months = fields.Integer(string='Term (Months)')
    status = fields.Selection([
        ('waiting', 'Waiting'),
        ('success', 'Success'),
        ('clean', 'Clean'),
        ('fail', 'Fail')
    ], string='Status', default='waiting')
    willing = fields.Text(string='Willing')
    maturity_date = fields.Date(string='Maturity Date')
    created_date = fields.Date(string='Created Date')
    monthly_principal_pay = fields.Float(string='Monthly Principal Pay')
    monthly_interest_pay = fields.Float(string='Monthly Interest Pay')
    monthly_pay = fields.Float(string='Monthly Pay', default=0.0)
    entirely_pay = fields.Float(string='Entirely Pay')
    total_notes = fields.Integer(string='Total Notes')
    invested_notes = fields.Integer(string='Invested Notes')
    description = fields.Text(string='Description')
    created_at = fields.Datetime(string='Created At')
    last_sync = fields.Datetime(string='Last Sync', default=fields.Datetime.now)

    @api.model
    def _auto_init(self):
        """Auto-add missing columns during model initialization"""
        super()._auto_init()
        try:
            # Add missing columns if they don't exist
            self.env.cr.execute("""
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "contractId" VARCHAR;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "willing" TEXT;
                ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "maturity_date" DATE;
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
            _logger.warning(f"Could not add columns automatically: {e}")

    def sync_from_mongodb(self):
        """Đồng bộ loan từ MongoDB"""
        try:
            mongo = MongoService()
            loan = mongo.get_loan(self.contractId)
            if loan:
                self.write({
                    'borrower_id': loan.get('borrower_id'),
                    'capital': loan.get('info', {}).get('capital'),
                    'interest_rate': loan.get('info', {}).get('rate'),
                    'term_months': loan.get('info', {}).get('periodMonth'),
                    'status': _normalize_status(loan.get('status')),
                    'willing': loan.get('info', {}).get('willing'),
                    'maturity_date': loan.get('info', {}).get('maturityDate'),
                    'created_date': loan.get('info', {}).get('createdDate'),
                    'monthly_principal_pay': loan.get('info', {}).get('monthlyPrincipalPay'),
                    'monthly_interest_pay': loan.get('info', {}).get('monthlyInterestPay'),
                    'monthly_pay': loan.get('info', {}).get('monthlyPay'),
                    'entirely_pay': loan.get('info', {}).get('entirelyPay'),
                    'total_notes': loan.get('totalNotes'),
                    'invested_notes': loan.get('investedNotes'),
                    'description': loan.get('description'),
                    'created_at': loan.get('createdAt'),
                    'last_sync': fields.Datetime.now()
                })
        except Exception as e:
            _logger.error(f"Error syncing loan {self.contractId}: {e}")


class P2PBorrower(models.Model):
    _name = 'p2p.borrower'
    _description = 'P2P Borrower'
    _rec_name = 'name'
    _inherit = []

    name = fields.Char(string='Full Name', required=True, )
    email = fields.Char(string='Email', required=True, )
    phone = fields.Char(string='Phone', required=True, )
    national_id = fields.Char(string='National ID', required=True, )
    date_of_birth = fields.Date(string='Date of Birth', required=True, )
    address = fields.Text(string='Address', required=True, )
    
    # Status fields
    is_active = fields.Boolean(string='Active', default=True, )
    status = fields.Selection([
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended')
    ], string='Status', default='pending', )
    
    # eKYC fields
    kyc_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], string='KYC Status', default='not_started', )
    
    kyc_documents = fields.One2many('p2p.kyc.document', 'borrower_id', string='KYC Documents')
    kyc_verification_date = fields.Datetime(string='KYC Verification Date')
    kyc_notes = fields.Text(string='KYC Notes')
    
    # Financial information
    credit_score = fields.Integer(string='Credit Score', default=0)
    monthly_income = fields.Float(string='Monthly Income', default=0.0)
    employment_status = fields.Selection([
        ('employed', 'Employed'),
        ('self_employed', 'Self Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student')
    ], string='Employment Status', default='employed')
    
    # Relationship fields
    loans = fields.One2many('p2p.loan', 'borrower_id', string='Loans')
    loan_count = fields.Integer(string='Total Loans', compute='_compute_loan_count')
    
    # Audit fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    last_updated = fields.Datetime(string='Last Updated', default=fields.Datetime.now)
    
    @api.depends('loans')
    def _compute_loan_count(self):
        for record in self:
            record.loan_count = len(record.loans)
    
    def action_activate(self):
        """Activate borrower"""
        self.write({'is_active': True, 'status': 'verified'})
    
    def action_deactivate(self):
        """Deactivate borrower"""
        self.write({'is_active': False, 'status': 'suspended'})
    
    def action_verify_kyc(self):
        """Mark KYC as verified"""
        self.write({
            'kyc_status': 'completed',
            'kyc_verification_date': fields.Datetime.now(),
            'status': 'verified'
        })
    
    def action_reject_kyc(self):
        """Reject KYC"""
        self.write({
            'kyc_status': 'rejected',
            'status': 'rejected'
        })


class P2PInvestor(models.Model):
    _name = 'p2p.investor'
    _description = 'P2P Investor'
    _rec_name = 'name'
    _inherit = []

    name = fields.Char(string='Full Name', required=True, )
    email = fields.Char(string='Email', required=True, )
    phone = fields.Char(string='Phone', required=True, )
    national_id = fields.Char(string='National ID', required=True, )
    date_of_birth = fields.Date(string='Date of Birth', required=True, )
    address = fields.Text(string='Address', required=True, )
    
    # Status fields
    is_active = fields.Boolean(string='Active', default=True, )
    status = fields.Selection([
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended')
    ], string='Status', default='pending', )
    
    # eKYC fields
    kyc_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], string='KYC Status', default='not_started', )
    
    kyc_documents = fields.One2many('p2p.kyc.document', 'investor_id', string='KYC Documents')
    kyc_verification_date = fields.Datetime(string='KYC Verification Date')
    kyc_notes = fields.Text(string='KYC Notes')
    
    # Financial information
    investment_capacity = fields.Float(string='Investment Capacity', default=0.0)
    risk_tolerance = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk')
    ], string='Risk Tolerance', default='medium')
    
    # Relationship fields
    # investments = fields.One2many('p2p.investment', 'investor_id', string='Investments')
    # investment_count = fields.Integer(string='Total Investments', compute='_compute_investment_count')
    
    # Audit fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    last_updated = fields.Datetime(string='Last Updated', default=fields.Datetime.now)
    
    # @api.depends('investments')
    # def _compute_investment_count(self):
    #     for record in self:
    #         record.investment_count = len(record.investments)
    
    def action_activate(self):
        """Activate investor"""
        self.write({'is_active': True, 'status': 'verified'})
    
    def action_deactivate(self):
        """Deactivate investor"""
        self.write({'is_active': False, 'status': 'suspended'})
    
    def action_verify_kyc(self):
        """Mark KYC as verified"""
        self.write({
            'kyc_status': 'completed',
            'kyc_verification_date': fields.Datetime.now(),
            'status': 'verified'
        })
    
    def action_reject_kyc(self):
        """Reject KYC"""
        self.write({
            'kyc_status': 'rejected',
            'status': 'rejected'
        })


class P2PKYCDocument(models.Model):
    _name = 'p2p.kyc.document'
    _description = 'P2P KYC Document'

    name = fields.Char(string='Document Name', required=True)
    document_type = fields.Selection([
        ('id_card', 'ID Card'),
        ('passport', 'Passport'),
        ('driver_license', 'Driver License'),
        ('utility_bill', 'Utility Bill'),
        ('bank_statement', 'Bank Statement'),
        ('other', 'Other')
    ], string='Document Type', required=True)
    
    document_file = fields.Binary(string='Document File', required=True)
    document_filename = fields.Char(string='Filename')
    
    verification_status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Verification Status', default='pending')
    
    verification_notes = fields.Text(string='Verification Notes')
    verified_by = fields.Many2one('res.users', string='Verified By')
    verified_date = fields.Datetime(string='Verified Date')
    
    # Relationships
    borrower_id = fields.Many2one('p2p.borrower', string='Borrower')
    investor_id = fields.Many2one('p2p.investor', string='Investor')
    
    def action_verify(self):
        """Verify document"""
        self.write({
            'verification_status': 'verified',
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now()
        })
    
    def action_reject(self):
        """Reject document"""
        self.write({
            'verification_status': 'rejected',
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now()
        })
