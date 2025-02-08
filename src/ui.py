import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from stock_screener import StockScreener

# Import our agents
from agents.warren_buffett import WarrenBuffettAgent
from agents.bill_ackman import BillAckmanAgent
from agents.technicals import TechnicalsAgent
from agents.sentiment import SentimentAgent
from agents.fundamentals import FundamentalsAgent
from agents.valuation import ValuationAgent
from agents.price_target import PriceTargetAgent
from agents.risk_manager import RiskManager
from agents.portfolio_manager import PortfolioManager

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="AI Trader Dashboard",
    page_icon="📈",
    layout="wide"
)

def initialize_agents(show_reasoning: bool = True) -> list:
    """Initialize all trading agents."""
    return [
        WarrenBuffettAgent(show_reasoning),
        BillAckmanAgent(show_reasoning),
        TechnicalsAgent(show_reasoning),
        SentimentAgent(show_reasoning),
        FundamentalsAgent(show_reasoning),
        ValuationAgent(show_reasoning),
        PriceTargetAgent(show_reasoning),
        RiskManager(show_reasoning)
    ]

def plot_price_chart(data: pd.DataFrame, price_targets: dict) -> go.Figure:
    """Create an interactive price chart with targets."""
    fig = make_subplots(rows=2, cols=1, 
                       shared_xaxes=True,
                       vertical_spacing=0.03,
                       row_heights=[0.7, 0.3])

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ),
        row=1, col=1
    )

    # Add price targets
    current_price = data['Close'].iloc[-1]
    fig.add_hline(y=price_targets['entry_price'], line_dash="dash", line_color="green",
                  annotation_text="Entry Target", row=1, col=1)
    fig.add_hline(y=price_targets['exit_price'], line_dash="dash", line_color="red",
                  annotation_text="Exit Target", row=1, col=1)
    fig.add_hline(y=price_targets['stop_loss'], line_dash="dash", line_color="orange",
                  annotation_text="Stop Loss", row=1, col=1)

    # Volume bars
    colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in data.iterrows()]
    fig.add_trace(
        go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color=colors),
        row=2, col=1
    )

    fig.update_layout(
        title='Price Chart with Trading Levels',
        yaxis_title='Price',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False
    )

    return fig

def format_agent_card(agent_name: str, signal: dict) -> None:
    """Format and display an agent's analysis card."""
    confidence = signal['confidence']
    signal_value = signal['signal']
    
    # Determine color based on signal
    if signal_value > 0:
        color = "success"
        signal_text = "BUY"
    elif signal_value < 0:
        color = "danger"
        signal_text = "SELL"
    else:
        color = "warning"
        signal_text = "HOLD"
    
    st.markdown(f"""
    <div style='border:1px solid #ddd; padding:10px; border-radius:5px; margin-bottom:10px;'>
        <h4>{agent_name}</h4>
        <p><b>Signal:</b> <span style='color:{color}'>{signal_text}</span></p>
        <p><b>Confidence:</b> {confidence:.1%}</p>
        <p><b>Reasoning:</b> {signal['reasoning']}</p>
    </div>
    """, unsafe_allow_html=True)

def display_screener_results(df: pd.DataFrame) -> None:
    """Display stock screener results."""
    # Add filters
    st.sidebar.subheader("Filters")
    
    # Minimum upside filter
    min_upside = st.sidebar.slider(
        "Minimum Potential Upside (%)",
        min_value=0,
        max_value=100,
        value=10
    )
    
    # Minimum confidence filter
    min_confidence = st.sidebar.slider(
        "Minimum Confidence (%)",
        min_value=0,
        max_value=100,
        value=50
    ) / 100
    
    # Filter DataFrame
    filtered_df = df[
        (df['potential_upside'] >= min_upside) &
        (df['confidence'] >= min_confidence)
    ]
    
    # Display results
    st.subheader(f"Top Investment Opportunities ({len(filtered_df)} stocks)")
    
    for _, row in filtered_df.iterrows():
        with st.expander(f"{row['symbol']} - {row['company_name']} - Upside: {row['potential_upside']:.1f}%"):
            cols = st.columns(4)
            
            # Company Information
            with cols[0]:
                st.markdown("**Company Info**")
                st.metric("Current Price", f"${row['current_price']:.2f}")
                st.metric("Target Price", f"${row['target_price']:.2f}")
                st.markdown(f"**Sector:** {row['sector']}")
                st.markdown(f"**Industry:** {row['industry']}")
                
            # Trading signals
            with cols[1]:
                st.markdown("**Trading Signals**")
                signal_color = "green" if row['aggregate_signal'] > 0 else "red" if row['aggregate_signal'] < 0 else "orange"
                signal_text = "BUY" if row['aggregate_signal'] > 0 else "SELL" if row['aggregate_signal'] < 0 else "HOLD"
                st.markdown(f"**Signal:** <span style='color:{signal_color}'>{signal_text}</span>", unsafe_allow_html=True)
                st.metric("Confidence", f"{row['confidence']:.1%}")
                
            # Financial Metrics
            with cols[2]:
                st.markdown("**Financial Metrics**")
                st.metric("Market Cap", f"${row['market_cap']:,.0f}")
                st.metric("Avg Daily Volume", f"{row['volume']:,.0f}")
                if row['pe_ratio'] > 0:
                    st.metric("Forward P/E", f"{row['pe_ratio']:.1f}")
                
            # Analysis summary
            with cols[3]:
                st.markdown("**Analysis Summary**")
                for reason in row['reasons']:
                    st.markdown(f"- {reason}")

def main():
    st.title("🤖 AI Trader Dashboard")
    
    # Initialize agents
    agents = initialize_agents(True)
    
    # Create tabs
    tab1, tab2 = st.tabs(["Single Stock Analysis", "Stock Screener"])
    
    with tab1:
        # Original single stock analysis UI
        st.sidebar.header("Stock Settings")
        symbol = st.sidebar.text_input("Stock Symbol", value="AAPL").upper()
        days = st.sidebar.slider("Analysis Period (days)", 30, 365, 180)
        initial_capital = st.sidebar.number_input(
            "Initial Capital ($)", 
            value=1000000, 
            step=100000,
            format="%d"
        )

        if st.sidebar.button("Analyze Stock"):
            try:
                portfolio_manager = PortfolioManager(agents, initial_capital, True)
                
                # Get data
                data = agents[0].get_historical_data(
                    symbol, 
                    (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    datetime.now().strftime('%Y-%m-%d')
                )

                if data.empty:
                    st.error(f"No data available for {symbol}")
                    return

                # Original analysis code...
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("Price Analysis")
                    price_target_agent = next(a for a in agents if isinstance(a, PriceTargetAgent))
                    price_analysis = price_target_agent.analyze(symbol, data)
                    
                    fig = plot_price_chart(data, price_analysis['metadata'])
                    st.plotly_chart(fig, use_container_width=True)

                    targets = price_analysis['metadata']
                    metrics_cols = st.columns(4)
                    with metrics_cols[0]:
                        st.metric("Current Price", f"${targets['current_price']:.2f}")
                    with metrics_cols[1]:
                        st.metric("Entry Target", f"${targets['entry_price']:.2f}")
                    with metrics_cols[2]:
                        st.metric("Exit Target", f"${targets['exit_price']:.2f}")
                    with metrics_cols[3]:
                        st.metric("Stop Loss", f"${targets['stop_loss']:.2f}")

                with col2:
                    st.subheader("Agent Analysis")
                    for agent in agents:
                        try:
                            signal = agent.analyze(symbol, data)
                            format_agent_card(agent.name, signal)
                        except Exception as e:
                            st.error(f"Error in {agent.name}: {str(e)}")

                    st.subheader("Final Decision")
                    try:
                        decision = portfolio_manager.analyze(symbol, data)
                        format_agent_card("Portfolio Manager", decision)
                    except Exception as e:
                        st.error(f"Error in Portfolio Manager: {str(e)}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                
    with tab2:
        st.sidebar.header("Screener Settings")
        
        # Segment selection
        segment = st.sidebar.selectbox(
            "Select Market Segment",
            options=['Large Cap', 'Mid Cap', 'Small Cap']
        )
        
        # Number of stocks to analyze
        num_stocks = st.sidebar.slider(
            "Number of Stocks to Analyze",
            min_value=5,
            max_value=30,
            value=10,
            step=5
        )
        
        # Parallel processing control
        max_workers = st.sidebar.slider(
            "Parallel Processing Threads",
            min_value=1,
            max_value=10,
            value=5
        )
        
        if st.sidebar.button("Run Screener"):
            with st.spinner(f"Analyzing {num_stocks} {segment} stocks... This may take a few minutes."):
                try:
                    # Initialize screener
                    screener = StockScreener(agents)
                    
                    # Run screening for selected segment
                    results = screener.screen_stocks(segment, num_stocks, max_workers)
                    
                    if results is not None and not results.empty:
                        # Display results
                        display_screener_results(results)
                    else:
                        st.error("No stocks found matching the criteria.")
                        
                except Exception as e:
                    st.error(f"An error occurred while screening stocks: {str(e)}")

if __name__ == "__main__":
    main() 