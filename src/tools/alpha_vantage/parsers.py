from datetime import datetime
from typing import List, Dict, Any

from tools.alpha_vantage.models import (
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
    """Parse insider transactions response"""
    transactions = []
    
    # Check if we have any transactions in the response
    if not isinstance(response, list):
        return InsiderTransactionsResponse(
            status_code=status_code,
            raw_response=response,
            transactions=[]
        )
    
    for item in response:
        try:
            transaction = InsiderTransaction(
                symbol=item.get('ticker', ''),
                filing_date=parse_datetime(item.get('transaction_date', '')),  # Using transaction_date as filing_date
                transaction_date=parse_datetime(item.get('transaction_date', '')),
                transaction_type='Sale' if item.get('acquisition_or_disposal') == 'D' else 'Purchase',
                shares=int(float(item.get('shares', '0'))),
                price=float(item.get('share_price', '0')),
                insider_name=item.get('executive', ''),
                insider_title=item.get('executive_title', '')
            )
            transactions.append(transaction)
        except (ValueError, TypeError) as e:
            print(f"Error parsing transaction: {e}")
            continue
    
    return InsiderTransactionsResponse(
        status_code=status_code,
        raw_response=response,
        transactions=transactions
    ) 