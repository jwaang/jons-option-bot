import math
import argparse
import pandas as pd
from yahoo_fin import options
from yahoo_fin import stock_info as si

def calculate(spread_type, data, strike1, strike2):
    if spread_type == 'cs':
        # max gain = higher strike premium - lower strike premium
        # max loss = ((higher strike - lower strike) * 100) - max gain
        # pop = 100 - [(the credit received / strike price width) x 100]
        strike1_diff = strike1['Ask'] - strike1['Bid']
        strike2_diff = strike2['Ask'] - strike2['Bid']
        max_gain = round((strike2['Last Price'] - strike1['Last Price']) * 100, 0)
        max_loss = round(((strike2['Strike'] - strike1['Strike']) * 100) - max_gain, 0)
        percent_return = round(max_gain / max_loss, 2) if max_loss != 0 else 0
        pop = round(100 - (((max_gain / 100) / (strike2['Strike'] - strike1['Strike'])) * 100), 2)
        data.append([strike1['Strike'], strike2['Strike'], strike1_diff, strike2_diff, max_loss, max_gain, percent_return, pop])
    elif spread_type == 'ds':
        # max loss = lower strike premium - higher strike premium
        # max gain = ((higher strike - lower strike) * 100) - max loss
        # pop = 100 - [(the max profit / strike price width) x 100]
        strike1_diff = strike1['Ask'] - strike1['Bid']
        strike2_diff = strike2['Ask'] - strike2['Bid']
        max_loss = round((strike1['Last Price'] - strike2['Last Price']) * 100, 0)
        max_gain = round(((strike2['Strike'] - strike1['Strike']) * 100) - max_loss, 0)
        percent_return = round(max_gain / max_loss, 2) if max_loss != 0 else 0
        pop = round(100 - (((max_gain / 100) / (strike2['Strike'] - strike1['Strike'])) * 100), 2)
        data.append([strike1['Strike'], strike2['Strike'], strike1_diff, strike2_diff, max_loss, max_gain, percent_return, pop])

def find_spreads(ticker, date, spread_type, rr=None, pop=None):
    try:
        curr_price = math.floor(si.get_live_price(ticker))
        if spread_type == 'cs':
            data = []
            puts = options.get_puts(ticker, date)
            puts_filtered = puts[puts['Strike'] <= curr_price]
            for i in range(0, len(puts_filtered)-1):
                for j in range(i+1, len(puts_filtered)):
                    calculate(spread_type, data, puts_filtered.iloc[i], puts_filtered.iloc[j])
            df = pd.DataFrame(data, columns=['Strike 1 (LONG)', 'Strike 2 (SHORT)', 'S1 Spread Diff', 'S2 Spread Diff', 'Max Loss', 'Max Gain', 'Risk/Reward Ratio', 'PoP (%)'])
            pd.set_option('display.max_rows', df.shape[0]+1)
            if rr != None:
                df = df.loc[(df['Risk/Reward Ratio'] >= float(rr))]
            if pop != None:
                df = df.loc[(df['PoP (%)'] >= float(pop))]
            # if rr == None and pop == None:
            #     df = df.loc[(df['Risk/Reward Ratio'] >= .25) & (df['PoP (%)'] <= 99.99)]
            return 'No good credit spread found' if df.empty else df # .sort_values(by='Risk/Reward', ascending=False)
        elif spread_type == 'ds':
            data = []
            calls = options.get_calls(ticker, date)
            calls_filtered = calls[calls['Strike'] >= curr_price]
            for i in range(0, len(calls_filtered)-1):
                for j in range(i+1, len(calls_filtered)):
                    calculate(spread_type, data, calls_filtered.iloc[i], calls_filtered.iloc[j])
            df = pd.DataFrame(data, columns=['Strike 1 (LONG)', 'Strike 2 (SHORT)', 'S1 Spread Diff', 'S2 Spread Diff', 'Max Loss', 'Max Gain', 'Risk/Reward Ratio', 'PoP (%)'])
            pd.set_option('display.max_rows', df.shape[0]+1)
            if rr != None:
                df = df.loc[(df['Risk/Reward Ratio'] >= float(rr))]
            if pop != None:
                df = df.loc[(df['PoP (%)'] >= float(pop))]
            # if rr == None and pop == None:
            #     df = df.loc[(df['Risk/Reward Ratio'] >= 2) & (df['PoP (%)'] >= 20)]
            return 'No good debit spread found' if df.empty else df # .sort_values(by='Risk/Reward', ascending=False)
        else:
            return 'Not a valid spread type'
    except AssertionError:
        return 'Not a valid ticker symbol'
    except ValueError:
        return 'Not a valid expiration date'

def main():
    args = init_args()
    if args.ticker is not None and args.exp_date is not None and args.spread_type is not None:
        print(find_spreads(args.ticker, args.exp_date, args.spread_type, args.rr, args.pop))
    else:
        print('No arguments provided. Try script.py -h')

def init_args():
    parser = argparse.ArgumentParser(description="Filter for the best spreads for an option")
    parser.add_argument('ticker', metavar='T', type=str, help='Provide a ticker symbol')
    parser.add_argument('exp_date', metavar='D', type=str, help='Provide an expiration date in this format MM/DD/YYYY')
    parser.add_argument('spread_type', metavar='S', type=str, help='Provide a spread type either cs or ds. Bullish sentiment only')
    parser.add_argument('-rr', type=float, help='Provide a numerical value for risk reward filtering. For DS, this should be greater than 2 and for CS it should be greater than .25')
    parser.add_argument('-pop', type=float, help='Provide a numerical value for probability of profitability filtering. For DS, this should be greater than 20 and for CS it should be greater than 50')
    return parser.parse_args()

# Uncomment if using script.py as standalone
# main()