from __future__ import annotations

import os
from typing import Dict

from tqdm import tqdm

import parse_itch5 as itch
from orderbook import Order, OrderBook


def reconstruct_orderbook(
    path: str, selected_symbols: set, depth: int = 3
) -> Dict[str, OrderBook]:
    """
    Reconstructs the order book from a binary file containing ITCH messages.

    Args:
        path (str): The path to the binary file.
        selected_symbols (set): A set of selected symbols to reconstruct the order book for.
        depth (int, optional): The depth of the order book. Defaults to 3.

    Returns:
        dict: A dictionary of order books, keyed by stock locate number.

    Raises:
        FileNotFoundError: If the specified file path does not exist.

    Example:
        >>> path = "/path/to/data/01302019.NASDAQ_ITCH50"
        >>> selected_symbols = {"AAPL", "GOOGL", "MSFT"}
        >>> depth = 10
        >>> order_books = reconstruct_orderbook(path, selected_symbols, depth)
    """
    if not os.path.exists(path):
        raise FileNotFoundError("The specified file path does not exist.")

    # Set of stock locate numbers for selected stocks, taken from the stock directory message (R)
    selected_stocks = set()
    # Dictionary of order books, which will be keyed by stock locate number
    order_book = {}

    with open(path, "rb") as binary:
        total_size = os.path.getsize(path)
        progress_bar = tqdm(
            total=total_size, unit="B", unit_scale=True, desc="Processing File"
        )
        message_type = binary.read(1)
        while message_type:
            a = b""
            if message_type == b"S":
                a = binary.read(11)  # System Event Message
            elif message_type == b"R":
                a = binary.read(38)  # Stock Directory Message
                m = itch.parse_stock_directory(a)
                if m[3] in selected_symbols:
                    selected_stocks.add(m[0])
                    order_book[m[0]] = OrderBook(m[3], depth)
                    # print("Symbol:", m[3], "Locate: ", m[0])
            elif message_type == b"H":
                a = binary.read(24)  # Stock Trading Action Message
            elif message_type == b"Y":
                a = binary.read(19)  # Reg SHO Restriction Message
            elif message_type == b"L":
                a = binary.read(25)  # Market Participant Position Message
            elif message_type == b"V":
                a = binary.read(34)  # MWCB Decline Level Message
            elif message_type == b"W":
                a = binary.read(11)  # MWCB Status Message
            elif message_type == b"K":
                a = binary.read(27)  # IPO Quoting Period Update Message
            elif message_type == b"J":
                a = binary.read(34)  # Limit Up-Limit Down Auction Collar Message
            elif message_type == b"h":
                a = binary.read(20)  # Operational Halt Message
            elif message_type == b"A":
                a = binary.read(35)  # Add Order Message
                m = itch.parse_add_order(a)
                if m[0] in selected_stocks:
                    order = Order(m[2], m[3], m[4], m[5], m[7])
                    order_book[m[0]].add_order(order)
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"F":
                a = binary.read(39)  # Add Order with MPID Message
                m = itch.parse_add_order_with_mpid(a)
                if m[0] in selected_stocks:
                    order = Order(m[2], m[3], m[4], m[5], m[7])
                    order_book[m[0]].add_order(order)
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"E":
                a = binary.read(30)  # Order Executed Message
                m = itch.parse_order_executed(a)
                if m[0] in selected_stocks:
                    order_book[m[0]].process_trade(m[2], m[3], m[4])
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"C":
                a = binary.read(35)  # Order Executed with Price Message
                m = itch.parse_order_executed_price(a)
                if m[0] in selected_stocks:
                    order_book[m[0]].process_trade(m[2], m[3], m[4], m[7], m[6] == "Y")
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"X":
                a = binary.read(22)  # Order Cancel Message
                m = itch.parse_order_cancel(a)
                if m[0] in selected_stocks:
                    order = order_book[m[0]].orders[m[3]]
                    order.update_order(None, order.shares - m[4], None)
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"D":
                a = binary.read(18)  # Order Delete Message
                m = itch.parse_order_delete(a)
                if m[0] in selected_stocks:
                    order_book[m[0]].remove_order(m[3])
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"U":
                a = binary.read(34)  # Order Replace Message
                m = itch.parse_order_replace(a)
                if m[0] in selected_stocks:
                    og = order_book[m[0]].orders[m[3]]
                    order_book[m[0]].remove_order(og.order_ref_number)
                    order_book[m[0]].add_order(
                        Order(m[2], m[4], og.buy_sell_indicator, m[5], m[6])
                    )
                    order_book[m[0]].record_state(m[2])
            elif message_type == b"P":
                a = binary.read(43)  # Trade Message
                m = itch.parse_trade(a)
                if m[0] in selected_stocks:
                    order_book[m[0]].record_trade(m[2], m[5], m[7])
            elif message_type == b"Q":
                a = binary.read(39)  # Cross Trade Message
                m = itch.parse_cross_trade(a)
                if m[0] in selected_stocks:
                    order_book[m[0]].record_trade(m[2], m[3], m[5])
            elif message_type == b"B":
                a = binary.read(18)  # NOII Message
            elif message_type == b"I":
                a = binary.read(49)  # Net Order Imbalance Indicator (NOII) Message

            progress_bar.update(len(a) + 1)

            message_type = binary.read(1)

    progress_bar.close()
    return order_book


if __name__ == "__main__":
    data_filepath = "/path/to/data/01302019.NASDAQ_ITCH50"
    selected_symbols = {"AAPL", "GOOGL", "MSFT"}
    depth = 5
    order_book = reconstruct_orderbook(data_filepath, selected_symbols, depth)

    print("Exporting to CSV...")
    for stock in order_book:
        order_book[stock].export_to_csv()
    print("Done!")
