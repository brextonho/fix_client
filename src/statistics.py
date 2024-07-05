# calculate trading statistics, including total trading volume, PNL, and VWAP


def calculate_total_volume(trade_data):
    """
    Calculate the total trading volume for each symbol.

    Args:
        trade_data (list): List of trade dictionaries containing 'symbol', 'price', and 'quantity'.

    Returns:
        dict: Dictionary containing total volume for each symbol, rounded to 2 decimal places.
    """
    total_volume = {}
    for trade in trade_data:
        symbol = trade['symbol']
        volume = trade['price'] * trade['quantity']
        if symbol in total_volume:
            total_volume[symbol] += volume
        else:
            total_volume[symbol] = volume
    total_volume = {k: round(v, 2) for k, v in total_volume.items()}
    print_total_volume(total_volume)
    return total_volume

def print_total_volume(total_volume):
    """
    Print the aggregated total volume for all symbols.

    Args:
        total_volume (dict): Dictionary containing total volume for each symbol.
    """
    total_volume_sum = round(sum(total_volume.values()), 2)
    print(f"Aggregated Total Volume: {total_volume_sum}")

def calculate_pnl(trade_data):
    """
    Calculate the profit and loss (PnL) for each symbol.

    Args:
        trade_data (list): List of trade dictionaries containing 'symbol', 'price', 'quantity', and 'side'.

    Returns:
        dict: Dictionary containing PnL for each symbol.
    """
    pnl = {}
    for trade in trade_data:
        symbol = trade['symbol']
        quantity = trade['quantity']
        price = trade['price']
        side = trade['side']
        if symbol not in pnl:
            pnl[symbol] = 0
        if side == 1:  # BUY
            pnl[symbol] -= price * quantity
        elif side == 2 or side == 5:  # SELL or SHORT
            pnl[symbol] += price * quantity
    print_pnl(pnl)
    return pnl

def print_pnl(pnl):
    """
    Print the aggregated profit and loss (PnL) for all symbols.

    Args:
        pnl (dict): Dictionary containing PnL for each symbol.
    """
    pnl_sum = round(sum(pnl.values()), 2)
    print(f"Aggregated PNL: {pnl_sum}")

def calculate_vwap(trade_data):
    """
    Calculate the volume-weighted average price (VWAP) for each symbol.

    Args:
        trade_data (list): List of trade dictionaries containing 'symbol', 'price', and 'quantity'.

    Returns:
        dict: Dictionary containing VWAP for each symbol, rounded to 2 decimal places.
    """
    total_value = {}
    total_quantity = {}
    for trade in trade_data:
        symbol = trade['symbol']
        quantity = trade['quantity']
        price = trade['price']
        if symbol in total_value:
            total_value[symbol] += price * quantity
            total_quantity[symbol] += quantity
        else:
            total_value[symbol] = price * quantity
            total_quantity[symbol] = quantity
    
    vwap = {}
    for symbol in total_value:
        vwap[symbol] = round(total_value[symbol] / total_quantity[symbol], 2)
    return vwap

def calculate_statistics(trade_data):
    total_volume = calculate_total_volume(trade_data)
    pnl = calculate_pnl(trade_data)
    vwap = calculate_vwap(trade_data)
    return {
        'total_volume': total_volume,
        'pnl': pnl,
        'vwap': vwap
    }
