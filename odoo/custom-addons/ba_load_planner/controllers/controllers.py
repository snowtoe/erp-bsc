# from odoo import http


# class BaLoadPlanner(http.Controller):
#     @http.route('/ba_load_planner/ba_load_planner', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ba_load_planner/ba_load_planner/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ba_load_planner.listing', {
#             'root': '/ba_load_planner/ba_load_planner',
#             'objects': http.request.env['ba_load_planner.ba_load_planner'].search([]),
#         })

#     @http.route('/ba_load_planner/ba_load_planner/objects/<model("ba_load_planner.ba_load_planner"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ba_load_planner.object', {
#             'object': obj
#         })

