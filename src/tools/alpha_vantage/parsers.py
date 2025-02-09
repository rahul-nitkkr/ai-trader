from datetime import datetime
from typing import List, Dict, Any

from .models import (
    InsiderTransaction, InsiderTransactionsResponse
)

def parse_datetime(date_str: str) -> datetime:
    """Parse datetime from Alpha Vantage format"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Unable to parse date: {date_str}")

def parse_insider_transactions(response: Dict[str, Any], status_code: int) -> InsiderTransactionsResponse:
    """Parse insider transactions response from Alpha Vantage API"""
    if status_code != 200:
        raise ValueError(f"API request failed with status code {status_code}")
        
    if "Error Message" in response:
        raise ValueError(f"API error: {response['Error Message']}")
        
    transactions = []
    for item in response.get("insiderTransactions", []):
        transaction = InsiderTransaction(
            symbol=item.get("symbol"),
            filing_date=datetime.strptime(item.get("filingDate", ""), "%Y-%m-%d"),
            transaction_date=datetime.strptime(item.get("transactionDate", ""), "%Y-%m-%d"),
            transaction_type=item.get("transactionType"),
            shares=float(item.get("shares", 0)),
            price=float(item.get("price", 0)),
            value=float(item.get("value", 0)),
            insider_name=item.get("insiderName"),
            insider_title=item.get("insiderTitle")
        )
        transactions.append(transaction)
        
    return InsiderTransactionsResponse(
        transactions=transactions,
        status_code=status_code
    ) 