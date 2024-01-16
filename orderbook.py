import csv
import os
from typing import Dict, List, Optional, Tuple

from sortedcontainers import SortedDict


class Order:
    def __init__(
        self,
        timestamp: int,
        order_ref_number: int,
        buy_sell_indicator: str,
        shares: int,
        price: float,
    ) -> None:
        """
        Initializes an Order instance.

        Parameters:
        timestamp (int): Timestamp of the order in nanoseconds since midnight.
        order_ref_number (int): Unique identifier for the order.
        buy_sell_indicator (str): Indicates the type of order: 'B' for buy and 'S' for sell.
        shares (int): The number of shares involved in the order.
        price (float): The price per share for the order.
        """
        self.timestamp = timestamp
        self.order_ref_number = order_ref_number
        self.buy_sell_indicator = buy_sell_indicator
        self.shares = shares
        self.price = price

    def update_order(
        self,
        new_timestamp: Optional[int] = None,
        new_shares: Optional[int] = None,
        new_price: Optional[float] = None,
    ) -> None:
        """
        Updates the order's attributes if new values are provided.

        Parameters:
        new_timestamp (int, optional): New timestamp for the order (nanoseconds since midnight).
        new_shares (int, optional): Updated number of shares in the order.
        new_price (float, optional): Updated price per share of the order.
        """
        if new_timestamp is not None:
            self.timestamp = new_timestamp
        if new_shares is not None:
            self.shares = new_shares
        if new_price is not None:
            self.price = new_price


class OrderBook:
    def __init__(self, stock_symbol: str, depth: int = 3) -> None:
        """
        Initializes an OrderBook for a specific stock.

        Parameters:
        stock_symbol (str): Symbol of the stock associated with this order book.
        depth (int): Depth of price levels to record.

        Attributes:
        orders (Dict[int, Order]): Orders indexed by reference number, storing all active orders.
        buy_orders (SortedDict): Sorted buy orders, with highest bids first.
        sell_orders (SortedDict): Sorted sell orders, with lowest asks first.
        trades (List[Tuple[int, int, float]]): Completed trades with form (timestamp, shares, price).
        order_book_history (List[List[Optional[float]]]): Historical snapshots of the order book state,
            each including order levels up to the specified depth.
        """
        self.stock_symbol = stock_symbol
        self.depth = depth
        self.orders: Dict[int, Order] = {}
        self.buy_orders: SortedDict[Tuple[float, int, int], Order] = SortedDict()
        self.sell_orders: SortedDict[Tuple[float, int, int], Order] = SortedDict()
        self.trades: List[Tuple[int, int, float]] = []
        self.order_book_history: List[Tuple[Optional[float]]] = []

    def add_order(self, order: Order) -> None:
        """
        Adds a new order to the order book.

        Parameters:
        order (Order): The order to be added.
        """
        self.orders[order.order_ref_number] = order

        if order.buy_sell_indicator == "B":
            order_key = (-order.price, order.timestamp, order.order_ref_number)
            self.buy_orders[order_key] = order
        else:
            order_key = (order.price, order.timestamp, order.order_ref_number)
            self.sell_orders[order_key] = order

    def remove_order(self, order_ref_number: int) -> None:
        """
        Removes an order from the order book.

        Parameters:
        order_ref_number (int): Reference number of the order to remove.
        """
        if order_ref_number in self.orders:
            order = self.orders.pop(order_ref_number)
            if order.buy_sell_indicator == "B":
                order_key = (-order.price, order.timestamp, order_ref_number)
                self.buy_orders.pop(order_key, None)
            else:
                order_key = (order.price, order.timestamp, order_ref_number)
                self.sell_orders.pop(order_key, None)

    def process_trade(
        self,
        timestamp: int,
        order_ref_number: int,
        shares: int,
        price: Optional[float] = None,
        printable: Optional[bool] = True,
    ) -> None:
        """
        Processes an executed trade by updating the order book. If new_shares is less than or equal to zero, the order is removed.

        Parameters:
        timestamp (int): Timestamp of the trade.
        order_ref_number (int): Reference number of the order involved in the trade.
        shares (int): Number of shares involved in the trade.
        price (float, optional): Trade price, defaults to the order's price if not provided.
        printable (bool, optional): If True, the trade is recorded in the trade history.
        """
        if order_ref_number in self.orders:
            order = self.orders[order_ref_number]
            new_shares = order.shares - shares
            if new_shares <= 0:
                self.remove_order(order_ref_number)
            else:
                order.update_order(None, new_shares, None)
            if printable:
                price = price if price is not None else order.price
                self.record_trade(timestamp, shares, price)

    def _accumulate_order_levels(self, orders: SortedDict) -> List[Tuple[float, int]]:
        """
        Accumulates the top levels of the order book, up to the orderbook's specified depth.

        Parameters:
        orders (SortedDict): Sorted dictionary of orders.
        depth (int): Number of levels to accumulate.

        Returns:
        List[Tuple[float, int]]: Price and aggregated shares at each level.
        """
        levels = []
        for (price, _, _), order in orders.items():
            price = abs(price)
            if len(levels) < self.depth:
                if len(levels) == 0 or levels[-1][0] != price:
                    levels.append((price, order.shares))
                else:
                    levels[-1] = (levels[-1][0], levels[-1][1] + order.shares)
            else:
                break
        return levels

    def record_trade(
        self,
        timestamp: int,
        shares: int,
        price: float,
    ) -> None:
        """
        Records a completed trade in the order book's trade history.

        Parameters:
        timestamp (int): Trade timestamp.
        shares (int): Number of shares traded.
        price (float): Trade price.
        """
        trade = (timestamp, shares, price)
        self.trades.append(trade)

    def record_state(self, timestamp: int) -> None:
        """
        Records the current state of the order book at a specified timestamp up to the orderbook's specified depth.

        Parameters:
        timestamp (int): Timestamp of the trade.
        """
        buy_levels = self._accumulate_order_levels(self.buy_orders)
        sell_levels = self._accumulate_order_levels(self.sell_orders)

        state_record = [timestamp]
        for i in range(self.depth):
            state_record.extend(
                [
                    buy_levels[i][0] if i < len(buy_levels) else None,
                    buy_levels[i][1] if i < len(buy_levels) else None,
                    sell_levels[i][0] if i < len(sell_levels) else None,
                    sell_levels[i][1] if i < len(sell_levels) else None,
                ]
            )
        self.order_book_history.append(state_record)

    def export_to_csv(self, base_directory: Optional[str] = "output") -> None:
        """
        Exports the order book and trade history to seperate CSV files.

        Parameters:
        base_directory (str): Base directory path to create the stock symbol folder and save the CSV files.
        """
        directory = os.path.join(base_directory, self.stock_symbol)
        os.makedirs(directory, exist_ok=True)

        with open(
            f"{directory}/{self.stock_symbol}_order_book_history.csv", "w", newline=""
        ) as file:
            writer = csv.writer(file)
            header = ["timestamp"]
            for i in range(self.depth):
                header.extend(
                    [
                        f"buy_price_{i+1}",
                        f"buy_shares_{i+1}",
                        f"sell_price_{i+1}",
                        f"sell_shares_{i+1}",
                    ]
                )
            writer.writerow(header)
            for record in self.order_book_history:
                writer.writerow(record)

        with open(
            f"{directory}/{self.stock_symbol}_trades.csv", "w", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "shares", "prices"])
            for trade in self.trades:
                writer.writerow(trade)
