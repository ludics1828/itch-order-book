import os
from tqdm import tqdm
import parse_itch5 as itch
from orderbook import OrderBook, Order


def reconstruct_orderbook(path):
    # Create dictionary of order books, which will be keyed by stock locate number
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
                # If the order book for this stock symbol doesn't exist, create it
                if m[0] not in order_book:
                    order_book[m[0]] = OrderBook(m[6])
                order = Order(m[2], m[3], m[4], m[5], m[7])
                order_book[m[0]].add_order(order)
            elif message_type == b"F":
                a = binary.read(39)  # Add Order with MPID Message
                m = itch.parse_add_order_with_mpid(a)
                order = Order(m[2], m[3], m[4], m[5], m[7])
                if m[0] not in order_book:
                    order_book[m[0]] = OrderBook(m[6])
                order_book[m[0]].add_order(order)
            elif message_type == b"E":
                a = binary.read(30)  # Order Executed Message
                m = itch.parse_order_executed(a)
                order_book[m[0]].process_trade(m[3], m[2], m[4], None, True)
            elif message_type == b"C":
                a = binary.read(35)  # Order Executed with Price Message
                m = itch.parse_order_executed_price(a)
                order_book[m[0]].process_trade(m[3], m[2], m[4], m[7], m[6] == "Y")
            elif message_type == b"X":
                a = binary.read(22)  # Order Cancel Message
                m = itch.parse_order_cancel(a)
                order = order_book[m[0]].orders[m[3]]
                new_shares = order.shares - m[4]
                order_book[m[0]].update_order(m[3], m[2], new_shares, order.price)
            elif message_type == b"D":
                a = binary.read(18)  # Order Delete Message
                m = itch.parse_order_delete(a)
                order_book[m[0]].remove_order(m[3])
            elif message_type == b"U":
                a = binary.read(34)  # Order Replace Message
                m = itch.parse_order_replace(a)
                original_order_ref = m[3]
                original_order = order_book[m[0]].orders[original_order_ref]
                buy_sell_indicator = original_order.buy_sell_indicator
                order_book[m[0]].remove_order(original_order_ref)
                new_order = Order(m[2], m[4], buy_sell_indicator, m[5], m[6])
                order_book[m[0]].add_order(new_order)
            elif message_type == b"P":
                a = binary.read(43)  # Trade Message
                m = itch.parse_trade(a)
                if m[0] not in order_book:
                    order_book[m[0]] = OrderBook(m[6])
                order_book[m[0]].record_trade(m[2], m[3], m[4], m[5], m[7])
                # print(m)
            elif message_type == b"Q":
                a = binary.read(39)  # Cross Trade Message
                m = itch.parse_cross_trade(a)
                if m[0] not in order_book:
                    order_book[m[0]] = OrderBook(m[4])
                order_book[m[0]].record_cross_trade(m[2], m[3], m[5])
            elif message_type == b"B":
                a = binary.read(18)  # NOII Message
            elif message_type == b"I":
                a = binary.read(49)  # Net Order Imbalance Indicator (NOII) Message

            progress_bar.update(len(a) + 1)

            message_type = binary.read(1)

    for stock in order_book:
        order_book[stock].export_to_csv()

    return order_book


if __name__ == "__main__":
    filepath = ""
    order_book = reconstruct_orderbook(filepath)
