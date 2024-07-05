import logging
import time
from threading import Thread
from fix_client import Application
from order_manager import OrderManager
import quickfix as fix

def main():
    logging.basicConfig(level=logging.INFO)

    # Configuration
    config_file = "../config/fix.cfg"
    symbols = ["MSFT", "AAPL", "BAC"]
    order_count = 1000 # 10
    duration_minutes = 5 #0.2 #1 # 5

    # Initialize the OrderManager
    order_manager = OrderManager()

    # Initialize the FIX application with the OrderManager
    application = Application(order_manager)
    settings = fix.SessionSettings(config_file)
    store_factory = fix.FileStoreFactory(settings)
    log_factory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(application, store_factory, settings, log_factory)

    try:
        # Start the FIX session
        initiator.start()
        
        # Wait for the session to logon
        time.sleep(5)

        # Get SenderCompID and TargetCompID from settings
        session = settings.get().getSessions()[0]
        sender_comp_id = settings.get(session).getString(fix.SenderCompID())
        target_comp_id = settings.get(session).getString(fix.TargetCompID())

        # Create the session ID
        session_id = fix.SessionID("FIX.4.2", sender_comp_id, target_comp_id)
        
        # Generating random orders
        generator_thread = Thread(target=order_manager.generate_random_orders, args=(application, session_id, symbols, order_count, duration_minutes))
        generator_thread.start()
        generator_thread.join()

        time.sleep(30) # wait for orders to be filled by the server
        order_manager.print_statistics()

        # Generating random cancellations for any active orders unfilled
        cancel_thread = Thread(target=order_manager.generate_random_cancellations, args=(application, session_id, duration_minutes))
        cancel_thread.start()
        cancel_thread.join()
        time.sleep(30) # wait for orders to be in the server

        # Print statistics after all orders are processed
        order_manager.print_statistics()


    finally:
        initiator.stop()

if __name__ == "__main__":
    main()
