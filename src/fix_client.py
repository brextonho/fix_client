# handle the connection to the FIX server, logon, and message handling
import quickfix as fix
import quickfix42 as fix42
import logging
from order_manager import OrderManager
from datetime import datetime
from logger import CustomFormatter

# Configure logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class Application(fix.Application):
    def __init__(self, order_manager):
        super().__init__()
        self.orderID = 0
        self.execID = 0
        self.order_manager = order_manager

    def onCreate(self, sessionID):
        logging.info(f"Session created: {sessionID}")

    def onLogon(self, sessionID):
        logging.info(f"Logon: {sessionID}")

    def onLogout(self, sessionID):
        logging.info(f"Logout: {sessionID}")

    def toAdmin(self, message, sessionID):
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        logging.info(f"ToAdmin: {message}")

        if msgType.getValue() == fix.MsgType_Logon:
            message.setField(fix.ResetSeqNumFlag(True))

    def fromAdmin(self, message, sessionID):
        logging.info(f"FromAdmin: {message}")

    def toApp(self, message, sessionID):
        logging.info(f"ToApp: {message}")

    def fromApp(self, message, sessionID):
        self.onMessage(message, sessionID)

    def onMessage(self, message, sessionID):
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        if msgType.getValue() == fix.MsgType_ExecutionReport:
            self.onExecutionReport(message)
        elif msgType.getValue() == fix.MsgType_OrderCancelReject:
            self.onOrderCancelReject(message)
        else:
            logging.info(f"Other Messages: {message}")

    def onExecutionReport(self, message):
        logging.info(f"Execution Report: {message}")

        # Extract common fields from the message
        symbol = fix.Symbol()
        side = fix.Side()
        cl_ord_id = fix.ClOrdID()

        message.getField(symbol)
        message.getField(side)
        message.getField(cl_ord_id)
        
        # Check for AvgPx field
        # avgPx = fix.AvgPx()
        # if not message.isSetField(avgPx):
        #     avgPx.setValue(0.0)  # Default value if not set by server
        #     message.setField(avgPx)
        #     logging.warning("AvgPx field was missing. Set to default value 0.0")

        # # Check for Price field for limit orders
        # if not message.isSetField(price):
        #     price.setValue(0.0)  # Default value if not set by server
        #     message.setField(price)
        #     logging.warning("Price field was missing. Set to default value 0.0")

        # cumQty = fix.CumQty()
        # if not message.isSetField(cumQty):
        #     cumQty.setValue(0)
        #     message.setField(cumQty)
        #     logging.warning("CumQty field was missing. Set to default value 0")

        # execID = fix.ExecID()
        # if not message.isSetField(execID):
        #     execID.setValue('0')
        #     message.setField(execID)
        #     logging.warning("ExecID field was missing. Set to default value 0")

        # Extract execution type from the message
        exec_type = fix.ExecType()
        message.getField(exec_type)

        if exec_type.getValue() == fix.ExecType_NEW:

            price = fix.Price()
            quantity = fix.OrderQty()
            message.getField(price)
            message.getField(quantity)

            # only add when executionreport NEW order response
            self.order_manager.add_order(cl_ord_id.getString(), {
                'symbol': symbol.getString(),
                'side': side.getValue(),
                # 'order_type': 'NEW',
                'quantity': quantity.getValue(),
                'price': price.getValue()
            })
            self.order_manager.orders_sent += 1 # increment only upon confirmation (35=8)
            logging.info('ADDED NEW ORDER')

        elif exec_type.getValue() == fix.ExecType_PARTIAL_FILL:

            lastPx = fix.LastPx()
            lastQty = fix.LastQty()
            message.getField(lastPx)
            message.getField(lastQty)

            self.order_manager.update_order(cl_ord_id.getString(), symbol.getString(), lastPx.getValue(), lastQty.getValue(), side.getValue())
            self.order_manager.update_position(symbol.getString(), lastPx.getValue(), lastQty.getValue(), side.getValue())
            logging.info('UPDATED PARTIAL FILL')

        elif exec_type.getValue() == fix.ExecType_FILL:

            lastPx = fix.LastPx()
            lastQty = fix.LastQty()
            message.getField(lastPx)
            message.getField(lastQty)

            self.order_manager.update_order(cl_ord_id.getString(), symbol.getString(), lastPx.getValue(), lastQty.getValue(), side.getValue())
            self.order_manager.update_position(symbol.getString(), lastPx.getValue(), lastQty.getValue(), side.getValue())
            logging.info('UPDATED FILL')

        elif exec_type.getValue() == fix.ExecType_CANCELLED:
            orig_cl_ord_id = fix.OrigClOrdID()
            message.getField(orig_cl_ord_id)

            self.order_manager.remove_order(cl_ord_id.getValue())
            self.order_manager.remove_order(orig_cl_ord_id.getString())
            self.order_manager.orders_cancelled += 1 # increment only upon confirmation (35=9)
            logging.info('REMOVED CANCELLED ORDER')

        else:
            logging.info(f"Message: {message}")

        # self.order_manager.print_statistics() # uncomment this if you want to print after every execution

    def onOrderCancelReject(self, message):
        logging.info(f"Order Cancel Reject: {message}")

    def send_order(self, sessionID, symbol, side, order_type, quantity, price=None):
        self.orderID += 1
        uniqueClOrdID = f"{self.orderID}_{int(datetime.now().timestamp() * 1000)}"
        clOrdID = fix.ClOrdID(uniqueClOrdID)
        handlInst = fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION)
        symbol_field = fix.Symbol(symbol)
        side_field = fix.Side(side)
        transactTime = fix.TransactTime()
        ordType = fix.OrdType(order_type)

        newOrderSingle = fix42.NewOrderSingle()
        newOrderSingle.setField(clOrdID)
        newOrderSingle.setField(handlInst)
        newOrderSingle.setField(symbol_field)
        newOrderSingle.setField(side_field)
        newOrderSingle.setField(transactTime)
        newOrderSingle.setField(ordType)
        newOrderSingle.setField(fix.OrderQty(quantity))
        newOrderSingle.setField(fix.TransactTime())
        newOrderSingle.setField(fix.Text("New Order"))
        # message.setField(fix.TimeInForce('3'))
        # 0 = Day (or session)
        # 1 = Good Till Cancel (GTC)
        # 2 = At the Opening (OPG)
        # 3 = Immediate or Cancel (IOC)

        if order_type == fix.OrdType_LIMIT:
            if price is not None:
                newOrderSingle.setField(fix.Price(price))
            else:
                logging.error("Price must be set for limit orders")
                return

        fix.Session.sendToTarget(newOrderSingle, sessionID)

    def send_cancel_order(self, sessionID, orig_cl_ord_id, symbol, side):
        self.orderID += 1
        origClOrdID = fix.OrigClOrdID(orig_cl_ord_id)
        clOrdID = fix.ClOrdID(str(self.orderID))
        symbol_field = fix.Symbol(symbol)
        side_field = fix.Side(side)
        transactTime = fix.TransactTime()

        cancelRequest = fix42.OrderCancelRequest()
        cancelRequest.setField(origClOrdID)
        cancelRequest.setField(clOrdID)
        cancelRequest.setField(symbol_field)
        cancelRequest.setField(side_field)
        cancelRequest.setField(transactTime)
        cancelRequest.setField(fix.Text("Order Cancel Request"))

        fix.Session.sendToTarget(cancelRequest, sessionID)
        