from odoo import http
from odoo.http import request


class P2PBridgeWebController(http.Controller):

    @http.route('/bridge/wallets', type='http', auth='user')
    def wallets_live(self, **kwargs):
        try:
            from ..models.mongo_service import MongoService
            mongo = MongoService()
            wallets = mongo.get_all_wallets()
            return request.render('p2p_bridge.wallets_live_template', {
                'wallets': wallets,
                'user': request.env.user,
            })
        except Exception as e:  # noqa: BLE001
            return request.render('p2p_bridge.error_template', {'error': str(e)})

    @http.route('/bridge/loans', type='http', auth='user')
    def loans_live(self, **kwargs):
        try:
            from ..models.mongo_service import MongoService
            mongo = MongoService()
            loans = mongo.get_loans()
            return request.render('p2p_bridge.loans_live_template', {
                'loans': loans,
                'user': request.env.user,
            })
        except Exception as e:  # noqa: BLE001
            return request.render('p2p_bridge.error_template', {'error': str(e)})


