"""
Script que crea una factura en Odoo a un usuario dado pasado desde los argumentos de consola
La creación de una factura en Odoo tiene la siguiente estructura:
1. Se crea una cotización
2. Se acepta la cotización y se transforma en "órden de compra"
3. Se genera un pago pendiente a esa órden de compra
4. Se "confirma" la órden de compra y se genera una factura con la deuda

Archivo que se inicio con JSON_RPC pero que se terminó con XML_RPC (porque hay bastante más documentación)
"""

import json
import random
import urllib.request
import datetime
import sys
import xmlrpc.client

#Ip y puerto del API de Odoo
HOST = '' #localhost?
PORT = 8069
#Base de datos usada por Odoo
DB = ''
#Nombre de usuario con API generada (generalmente el correo de acceso)
USER = ''
#Contraseña del usuario (el token del API no sirve)
PASS = ''

def json_rpc(url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }
    req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={
        "Content-Type":"application/json",
    })
    reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
    if reply.get("error"):
        raise Exception(reply["error"])
    return reply["result"]

def call(url, service, method, *args):
    return json_rpc(url, "call", {"service": service, "method": method, "args": args})

# Log In
url = "http://%s:%s/jsonrpc" % (HOST, PORT)
uid = call(url, "common", "login", DB, USER, PASS)

#ID del producto dependiendo el sector del estadio que está como socio
product = 0;
if sys.argv[2] == "pacifico":
    product = 16
elif sys.argv[2] == "pacifico menor":
    product = 13
elif sys.argv[2] == "numerada":
    product = 14
elif sys.argv[2] == "numerada menor":
    product = 15
elif sys.argv[2] == "codos":
    product = 9
elif sys.argv[2] == "codos menor":
    product = 10
elif sys.argv[2] == "andes":
    product = 11
elif sys.argv[2] == "andes menor":
    product = 12
if product==0:
    print("error")

# Argumentos para crear una nueva cotización
args = {
    'partner_id': int(sys.argv[1]), #ID del contacto a generar la factura
    'date_order': sys.argv[3], #la fecha viene en formato
    'create_uid': uid,
    'state': 'draft',
    #'invoice_status': 'invoiced',
    "order_line":
        [
            [
                0,
                0,
                {
                    "product_id": product,
                    "product_uom_qty": 1,
                    'qty_delivered': 1,
                }
            ]
        ]
}
#Crea la cotización
order_id = call(url, "object", "execute", DB, uid, PASS, 'sale.order', 'create', args)
#Crea la órden de compra, a partir de la cotización
invoice_id = call(url, "object", "execute", DB, uid, PASS, 'sale.order', 'action_confirm', [order_id])
#Crea una "deuda" para la cotización cambiando el estado de la órden de compra como "confirmada"
payment_id = call(url, "object", "execute", DB, uid, PASS, 'sale.advance.payment.inv', 'create', [{'advance_payment_method': 'delivered', 'sale_order_ids': [order_id]}])
#Genero un modelo en RPC_XML // no supe como hacer esto con RPC_JSON
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format('http://'+HOST+':'+str(PORT)), allow_none=True)
#Creo el argumento para crear la factura
args = {
    'context': {
        'active_model': "sale.order",
        'sale_order_ids': [order_id],
        'active_ids': [order_id],
        'active_id': order_id,
    }
}
#Se genera la Factura (queda la orden de compra confirmada en el módulo de ventas y la factura/boleta en el módulo de facturación)
account_id = models.execute_kw(DB, uid, PASS, 'sale.advance.payment.inv', 'create_invoices', [payment_id], args)
#Se cambia el tipo de documento de factura a boleta electrónica (BE de servicios es ID: 14) // NO FUNCIONA y se tuvo que dejar creación por defecto como boleta id 14 desde interfáz de Odoo
#models.execute_kw(DB, uid, PASS, 'account.move', 'write', [[account_id], {'l10n_latam_document_type_id': 14}])