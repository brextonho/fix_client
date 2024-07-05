# manage the state of the orders and handle order cancellations

import random
import time
from datetime import datetime, timedelta
from threading import Thread
from statistics import calculate_statistics
import quickfix as fix
import quickfix42 as fix42

class OrderManager:
    def __init__(self):
        self.active_orders = {} # dictionary of dictionaries, key: cl_ord_id, value: order data, to keep track of orders unfilled to cancel
        self.trade_data = [] # list of dictionaries, filled orders, to calculate stats for filled orders
        self.positions = {}  # dictionary to keep track of positions and average prices
        self.orders_sent = 0
        self.orders_cancelled = 0

    def add_order(self, cl_ord_id, order):
        """
        Add a new order to the active orders list.

        Args:
            cl_ord_id (str): The client order ID.
            order (dict): The order data containing details like symbol, side, quantity, and price.
        """
        order['fills'] = []  # Initialize the fills list
        order['filled_quantity'] = 0  # Initialize filled quantity
        self.active_orders[cl_ord_id] = order

    def remove_order(self, cl_ord_id):
        """
        Remove an order from the active orders list.

        Args:
            cl_ord_id (str): The client order ID.
        """
        if cl_ord_id in self.active_orders:
            del self.active_orders[cl_ord_id]

    def update_order(self, cl_ord_id, symbol, price, quantity, side):
        """
        Update an existing order during ExecType_FILL or ExecType_PARTIAL_FILL and add to trade data.

        Args:
            cl_ord_id (str): The client order ID.
            symbol (str): The symbol being traded.
            price (float): The price of the trade.
            quantity (int): The quantity of the trade.
            side (int): The side of the trade (BUY, SELL, or SHORT).
        """
        if cl_ord_id in self.active_orders:
            order = self.active_orders[cl_ord_id]
            order['filled_quantity'] += quantity
            order['fills'].append({'price': price, 'quantity': quantity})
            self.trade_data.append({'symbol': symbol, 'price': price, 'quantity': quantity, 'side': side})

            # Check if the order is fully filled
            if order['filled_quantity'] >= order['quantity']:
                del self.active_orders[cl_ord_id]

    def update_position(self, symbol, price, quantity, side):
        """
        Update the position and average price for the given symbol.

        Args:
            symbol (str): The symbol being traded.
            price (float): The price of the trade.
            quantity (int): The quantity of the trade.
            side (int): The side of the trade (BUY, SELL, or SHORT).
        """
        if symbol not in self.positions:
            self.positions[symbol] = {'position': 0, 'total_cost': 0, 'avg_price': None}

        position = self.positions[symbol]['position']
        total_cost = self.positions[symbol]['total_cost']

        if side == fix.Side_BUY:
            new_position = position + quantity
            new_total_cost = total_cost + (price * quantity)
        elif side == fix.Side_SELL or side == fix.Side_SELL_SHORT:
            new_position = position - quantity
            new_total_cost = total_cost - (price * quantity)
        else:
            new_position = position
            new_total_cost = total_cost

        if new_position != 0:
            avg_price = abs(new_total_cost / new_position)
        else:
            avg_price = None

        self.positions[symbol] = {
            'position': new_position,
            'total_cost': new_total_cost,
            'avg_price': avg_price
        }

    def generate_random_orders(self, fix_client, session_id, symbols, order_count, duration_minutes):
        """
        Generate random orders and send them to the FIX client.

        Args:
            fix_client (FixClient): The FIX client used to send orders.
            session_id (SessionID): The session ID for the FIX session.
            symbols (list): List of symbols to trade.
            order_count (int): The number of orders to send.
            duration_minutes (int): The duration in minutes over which to send the orders.
        """
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        while self.orders_sent < order_count and datetime.now() < end_time:
            symbol = random.choice(symbols)
            side = random.choice([fix.Side_BUY, fix.Side_SELL, fix.Side_SELL_SHORT])
            order_type = random.choice([fix.OrdType_MARKET, fix.OrdType_LIMIT])
            quantity = random.randint(1, 100)
            price = round(random.uniform(100, 200), 2) if order_type == fix.OrdType_LIMIT else None  # Random price for limit orders
            fix_client.send_order(session_id, symbol, side, order_type, quantity, price)
            time.sleep(0.1)
            # time.sleep(random.uniform(0.1, 1))  # Random delay between orders (for testing)

    def generate_random_cancellations(self, fix_client, session_id, duration_minutes):
        """
        Generate random cancellations for active orders.

        Args:
            fix_client (FixClient): The FIX client used to send cancel requests.
            session_id (SessionID): The session ID for the FIX session.
            duration_minutes (int): The duration in minutes over which to send the cancellations.
        """
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        while datetime.now() < end_time:
            if self.active_orders:
                cl_ord_id = random.choice(list(self.active_orders.keys()))
                order = self.active_orders[cl_ord_id]
                fix_client.send_cancel_order(session_id, cl_ord_id, order['symbol'], order['side'])
                time.sleep(0.1)
            # time.sleep(random.uniform(0.1, 1))  # Random delay between cancellations

    def print_statistics(self):
        stats = calculate_statistics(self.trade_data)
        print("Total Volume: ", stats['total_volume'])
        print("PNL: ", stats['pnl'])
        print("VWAP: ", stats['vwap'])
        print("Orders sent: ", self.orders_sent)
        print("Orders cancelled: ", self.orders_cancelled)
        print("Active Orders: ", self.active_orders)
        print("Positions: ", self.positions)