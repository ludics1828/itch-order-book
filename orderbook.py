import os
import csv
from typing import Dict, Tuple, List, Optional
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
        Initialize an order with given parameters.

        Parameters:
        timestamp (int): Timestamp of the order (ns since midnight).
        order_ref_number (int): Unique reference number of the order.
        buy_sell_indicator (str): "B" if buy order, "S" if sell order.
        shares (int): Number of shares in the order.
        price (float): Price of the order.
        """
        self.original_timestamp = timestamp
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
        Updates the order with new values if provided.

        Parameters:
        new_timestamp (int, optional): New timestamp.
        new_shares (int, optional): New number of shares.
        new_price (float, optional): New price.
        """
        if new_timestamp is not None:
            self.timestamp = new_timestamp
        if new_shares is not None:
            self.shares = new_shares
        if new_price is not None:
            self.price = new_price


class OrderBook:
    def __init__(self, stock_symbol: str, depth: int = 5) -> None:
        """
        Initializes an OrderBook for a specific stock.

        Parameters:
        stock_symbol (str): Symbol of the stock associated with this order book.
        depth (int): Depth of price levels to record.

        Attributes:
        orders (Dict[int, Order]): Orders indexed by reference number.
        buy_orders (SortedDict): Sorted buy orders.
        sell_orders (SortedDict): Sorted sell orders.
        trades (List[Tuple[int, int, float, int]]): Completed trades.
        cross_trades (List[Tuple[int, float, int]]): Completed cross trades.
        order_book_history (List[List[Optional[float]]]): History of order book states.
        """
        self.stock_symbol = stock_symbol
        self.depth = depth
        self.orders: Dict[int, Order] = {}
        self.buy_orders: SortedDict[Tuple[float, int, int], Order] = SortedDict()
        self.sell_orders: SortedDict[Tuple[float, int, int], Order] = SortedDict()
        self.trades: List[Tuple[int, int, float, int]] = []
        self.cross_trades: List[Tuple[int, float, int]] = []
        self.order_book_history: List[Tuple[Optional[float]]] = []

    def _accumulate_order_levels(
        self, orders: SortedDict, depth: int
    ) -> List[Tuple[float, int]]:
        """
        Accumulates the top 'depth' levels for given orders.

        Parameters:
        orders (SortedDict): Sorted dictionary of orders.
        depth (int): Number of levels to accumulate.

        Returns:
        List[Tuple[float, int]]: Price and aggregated shares at each level.
        """
        levels = []
        for (price, _, _), order in orders.items():
            if len(levels) < depth:
                if len(levels) == 0 or levels[-1][0] != price:
                    levels.append((price, order.shares))
                else:
                    levels[-1] = (levels[-1][0], levels[-1][1] + order.shares)
            else:
                break
        return levels

    def add_order(self, order: Order) -> None:
        """
        Adds a new order to the order book.

        Parameters:
        order (Order): The order to be added.
        """
        self.orders[order.order_ref_number] = order
        order_key = (order.price, order.original_timestamp, order.order_ref_number)
        if order.buy_sell_indicator == "B":
            self.buy_orders[order_key] = order
        else:
            self.sell_orders[order_key] = order
        self.record_state(order.timestamp)

    def update_order(
        self,
        order_ref_number: int,
        new_timestamp: int,
        new_shares: Optional[int] = None,
        new_price: Optional[float] = None,
    ) -> None:
        """
        Updates an existing order in the order book.

        Parameters:
        order_ref_number (int): Reference number of the order.
        new_timestamp (int, optional): Updated timestamp.
        new_shares (int, optional): Updated number of shares.
        new_price (float, optional): Updated price.
        """
        if order_ref_number in self.orders:
            order = self.orders[order_ref_number]
            old_order_key = (order.price, order.timestamp, order_ref_number)
            order.update_order(None, new_shares, new_price)
            if old_order_key[0] != order.price:
                new_order_key = (order.price, order.timestamp, order_ref_number)
                if order.buy_sell_indicator == "B":
                    if old_order_key in self.buy_orders:
                        del self.buy_orders[old_order_key]
                    self.buy_orders[new_order_key] = order
                else:
                    if old_order_key in self.sell_orders:
                        del self.sell_orders[old_order_key]
                    self.sell_orders[new_order_key] = order
        self.record_state(new_timestamp)

    def remove_order(self, order_ref_number: int) -> None:
        """
        Removes an order from the order book.

        Parameters:
        order_ref_number (int): Reference number of the order to remove.
        """
        if order_ref_number in self.orders:
            order = self.orders.pop(order_ref_number)
            order_key = (order.price, order.timestamp, order_ref_number)
            if order.buy_sell_indicator == "B":
                self.buy_orders.pop(order_key, None)
            else:
                self.sell_orders.pop(order_key, None)
        self.record_state(order.timestamp)

    def process_trade(
        self,
        timestamp: int,
        order_ref_number: int,
        shares: int,
        price: Optional[float] = None,
        printable: Optional[bool] = True,
    ) -> None:
        """
        Processes a trade and updates the order book.

        Parameters:
        order_ref_number (int): Reference number of the order involved in the trade.
        timestamp (int): Trade timestamp.
        shares (int): Number of shares traded.
        price (float): Trade price.
        printable (bool, optional): Flag to record trade if True.
        """
        if order_ref_number in self.orders:
            order = self.orders[order_ref_number]
            new_shares = order.shares - shares
            if price is None:
                price = order.price
            if new_shares <= 0:
                self.remove_order(order_ref_number)
            else:
                self.update_order(order_ref_number, timestamp, new_shares, price)
            if printable:
                self.record_trade(
                    timestamp,
                    order_ref_number,
                )

    def record_trade(
        self,
        timestamp: int,
        order_ref_number: int,
        shares: int,
        price: float,
        buy_sell_indicator: str,
    ) -> None:
        """
        Records a trade in the order book with a consistent data order.

        Parameters:
        timestamp (int): Trade timestamp.
        order_ref_number (int): Reference number of the order.
        buy_sell_indicator (str): "B" if buy order, "S" if sell order.
        price (float): Trade price.
        shares (int): Number of shares traded.
        """
        trade = (timestamp, order_ref_number, buy_sell_indicator, shares, price)
        self.trades.append(trade)

    def record_cross_trade(self, timestamp: int, price: float, shares: int) -> None:
        """
        Records a cross trade with a consistent data order.

        Parameters:
        shares (int): Number of shares in the cross trade.
        price (float): Trade price.
        timestamp (int): Trade timestamp.
        """
        cross_trade = (timestamp, price, shares)
        self.cross_trades.append(cross_trade)

    def record_state(self, timestamp: int) -> None:
        """
        Records the current state of the order book.

        Parameters:
        timestamp (int): Timestamp of the order book state.
        """
        buy_levels = self._accumulate_order_levels(self.buy_orders, self.depth)
        sell_levels = self._accumulate_order_levels(self.sell_orders, self.depth)

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
        Exports the order book history, trades, and cross trades to CSV files with consistent headers.
        Creates a folder named after the stock symbol for storing these files.

        Parameters:
        base_directory (str): Base directory path to create the stock symbol folder and save the CSV files.
        """
        # Create directory for the stock symbol if it doesn't exist
        directory = os.path.join(base_directory, self.stock_symbol)
        os.makedirs(directory, exist_ok=True)

        # Export order book history
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

        # Export trades
        with open(
            f"{directory}/{self.stock_symbol}_trades.csv", "w", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "timestamp",
                    "order_ref_number",
                    "buy_sell_indicator",
                    "price",
                    "shares",
                ]
            )
            for trade in self.trades:
                writer.writerow(trade)

        # Export cross trades
        with open(
            f"{directory}/{self.stock_symbol}_cross_trades.csv", "w", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "shares", "price"])
            for cross_trade in self.cross_trades:
                writer.writerow(cross_trade)
