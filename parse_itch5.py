import struct
from typing import Tuple


def parse_stock_directory(
    a: bytes,
) -> Tuple[
    int,
    int,
    bytes,
    bytes,
    str,
    str,
    int,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    int,
    str,
]:
    """
    Parse a stock directory message.

    This function unpacks a stock directory message into its constituent components.
    The expected message format includes 17 elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Stock symbol
    5. Market category
    6. Financial status indicator
    7. Round lot size
    8. Round lots only
    9. Issue classification
    10. Issue subtype
    11. Authenticity
    12. Short sale threshold indicator
    13. IPO flag
    14. LULD reference price tier
    15. ETP flag
    16. ETP leverage factor
    17. Inverse indicator

    Parameters:
    a (bytes): The stock directory message in bytes to be parsed.

    Returns:
    Tuple[int, int, bytes, bytes, str, str, int, str, str, str, str, str, str, str, str, int, str]:
    A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6s8sccIcc2scccccIc", a)
    m = list(m)
    m[3] = m[3].decode().strip()
    return tuple(m)


# Message Type A
def parse_add_order(a: bytes) -> Tuple[int, int, int, int, str, int, str, float]:
    """
    Parse an add order message.

    This function unpacks an add order message into its constituent components.
    The expected message format includes eight elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number
    5. Buy/sell indicator
    6. Shares
    7. Stock
    8. Price

    The price is converted from integer to floating-point by dividing by 10,000.

    Parameters:
    a (bytes): The add order message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, str, int, str, float]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQcI8sL", a)
    m = list(m)
    m[4] = m[4].decode()
    m[6] = m[6].decode().strip()
    m[2] = int.from_bytes(m[2], byteorder="big")
    m[7] = float(m[7]) / 10000
    return tuple(m)


# Message Type F
def parse_add_order_with_mpid(
    a: bytes,
) -> Tuple[int, int, int, int, str, int, str, float, bytes]:
    """
    Parse an add order with MPID message.

    This function unpacks an add order with MPID message into its constituent components.
    The expected message format includes nine elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number
    5. Buy/sell indicator
    6. Shares
    7. Stock
    8. Price
    9. Attribution

    The price is converted from integer to floating-point by dividing by 10,000.

    Parameters:
    a (bytes): The add order with MPID message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, str, int, str, float]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQcI8sL4s", a)
    m = list(m)
    m[4] = m[4].decode()
    m[6] = m[6].decode().strip()
    m[2] = int.from_bytes(m[2], byteorder="big")
    m[7] = float(m[7]) / 10000
    m.pop()  # Remove the attribution as it is not used
    return tuple(m)


# Message Type E
def parse_order_executed(a: bytes) -> Tuple[int, int, int, int, int, int]:
    """
    Parse an order executed message.

    This function unpacks an order executed message into its constituent components.
    The expected message format includes six elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number
    5. Executed shares
    6. Match number

    Parameters:
    a (bytes): The order executed message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, int, int]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQIQ", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    return tuple(m)


# Message Type C
def parse_order_executed_price(
    a: bytes,
) -> Tuple[int, int, int, int, int, int, str, float]:
    """
    Parse an order executed price message.

    This function unpacks an order executed price message into its constituent components.
    The expected message format includes eight elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number
    5. Executed shares
    6. Match number
    7. Printable
    8. Execution price

    The execution price is converted from integer to floating-point by dividing by 10,000.

    Parameters:
    a (bytes): The order executed price message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, int, int, str, float]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQIQcL", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    m[6] = m[6].decode()
    m[7] = float(m[7]) / 10000
    return tuple(m)


# Message Type X
def parse_order_cancel(a: bytes) -> Tuple[int, int, int, int, int]:
    """
    Parse an order cancel message.

    This function unpacks an order cancel message into its constituent components.
    The expected message format includes five elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number
    5. Cancelled shares

    Parameters:
    a (bytes): The order cancel message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, int]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQI", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    return tuple(m)


# Message Type D
def parse_order_delete(a: bytes) -> Tuple[int, int, int, int]:
    """
    Parse an order delete message.

    This function unpacks an order delete message into its constituent components.
    The expected message format includes four elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number

    Parameters:
    a (bytes): The order delete message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQ", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    return tuple(m)


# Message Type U
def parse_order_replace(a: bytes) -> Tuple[int, int, int, int, int, int, float]:
    """
    Parse an order replace message.

    This function unpacks an order replace message into its constituent components.
    The expected message format includes seven elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Original order reference number
    5. New order reference number
    6. Shares
    7. Price

    The price is converted from integer to floating-point by dividing by 10,000.

    Parameters:
    a (bytes): The order replace message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, int, int, float]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQQIL", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    m[6] = float(m[6]) / 10000
    return tuple(m)


# Message Type P
def parse_trade(a: bytes) -> Tuple[int, int, int, int, bytes, int, bytes, float, int]:
    """
    Parse a trade message.

    This function unpacks a trade message into its constituent components.
    The expected message format includes nine elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Order reference number
    5. Buy/sell indicator
    6. Shares
    7. Stock
    8. Price
    9. Match number

    The price is converted from integer to floating-point by dividing by 10,000.

    Parameters:
    a (bytes): The trade message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, str, int, bytes, float, int]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQcI8sLQ", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    m[4] = m[4].decode()
    m[6] = m[6].decode().strip()
    m[7] = float(m[7]) / 10000
    return tuple(m)


# Message Type Q
def parse_cross_trade(a: bytes) -> Tuple[int, int, int, int, bytes, float, int, str]:
    """
    Parse a cross trade message.

    This function unpacks a cross trade message into its constituent components.
    The expected message format includes eight elements:
    1. Stock locate
    2. Tracking number
    3. Timestamp
    4. Shares
    5. Stock
    6. Cross price
    7. Match number
    8. Cross type

    The cross price is converted from integer to floating-point by dividing by 10,000.

    Parameters:
    a (bytes): The cross trade message in bytes to be parsed.

    Returns:
    Tuple[int, int, int, int, bytes, float, int, str]: A tuple containing the parsed values.
    """
    m = struct.unpack("!HH6sQ8sLQc", a)
    m = list(m)
    m[2] = int.from_bytes(m[2], byteorder="big")
    m[4] = m[4].decode().strip()
    m[5] = float(m[5]) / 10000
    return tuple(m)
