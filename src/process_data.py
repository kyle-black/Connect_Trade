import pandas as pd
import numpy as np
from sklearn.decomposition import PCA


def make_features(df):
        """Loads raw forex data from CSV."""
       # df = pd.read_csv('data/all_forex_pull_15_min.csv')
        ###########  Turn time to COS and SIN data
        period = 86400  # 24 hours

        timestamps = df['timestamps']
        # Compute sine and cosine
        sin_time = np.sin(2 * np.pi * (timestamps % period) / period)
        cos_time = np.cos(2 * np.pi * (timestamps % period) / period)

        
        
        
        df['sin_time'] = sin_time
        df['cos_time'] = cos_time

        window_length =15
        num_std_dev = 2
        eurusd_close ='eurusd_close'
        df['Middle_Band'] = df[eurusd_close].rolling(window=window_length).mean()
        df['Upper_Band'] = df['Middle_Band'] + df[eurusd_close].rolling(window=window_length).std() * num_std_dev
        df['Lower_Band'] = df['Middle_Band'] - df[eurusd_close].rolling(window=window_length).std() * num_std_dev

        # Log Returns
        df['Log_Returns'] = np.log(df[eurusd_close]/ df[eurusd_close].shift(window_length))

        ####################### MACD 
        exp1 = df[eurusd_close].ewm(span=12, adjust=False).mean()
        exp2 = df[eurusd_close].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line_MACD'] = df['MACD'].ewm(span=9, adjust=False).mean()

        ######################### RSI
        delta = df[eurusd_close].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=window_length).mean()
        avg_loss = loss.rolling(window=window_length).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        low_min  = df[eurusd_close].rolling(window=window_length).min()
        high_max = df[eurusd_close].rolling(window=window_length).max()

        df['%K'] = (df[eurusd_close] - low_min) / (high_max - low_min) * 100
        df['%D'] = df['%K'].rolling(window=window_length).mean()

        df['daily_return'] = df[eurusd_close].diff()
        df['direction'] = np.where(df['daily_return'] > 0, 1, -1)
        df.loc[df['daily_return'] == 0, 'direction'] = 0

        period9_high = df[eurusd_close].rolling(window=9).max()
        period9_low = df[eurusd_close].rolling(window=9).min()
        df['tenkan_sen'] = (period9_high + period9_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = df[eurusd_close].rolling(window=26).max()
        period26_low = df[eurusd_close].rolling(window=26).min()
        df['kijun_sen'] = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        period52_high = df[eurusd_close].rolling(window= 52).max()
        period52_low = df[eurusd_close].rolling(window=52).min()
        df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)

        # Chikou Span (Lagging Span): eurusd_close shifted back 26 periods
        df['chikou_span'] = df[eurusd_close].shift(26)


        
        
        return df


def cointegration_spread(df, combos):
        """Computes cointegration spread using PCA and retains log returns."""
        coint_data = []  

        sin_time =df['sin_time']
        cos_time = df['cos_time'] 
        RSI = df['RSI']
        K_ = df['%K']
        D_ =df['%D']
        D_R =df['direction']
        T_S = df['tenkan_sen']
        K_S = df['kijun_sen']
        S_A = df['senkou_span_a']
        S_B = df['senkou_span_b']
        C_S = df['chikou_span']


        original_closes = df.filter(like='_close', axis=1)
        log_returns = df.filter(like='_log_return', axis=1)  # Keep log returns

        for asset_0, asset_1 in combos:
            print(f'Calculating {asset_0} & {asset_1}')
            asset_0_returns = df[f'{asset_0}_log_return']
            asset_1_returns = df[f'{asset_1}_log_return']

            # Drop NaNs for valid PCA calculation
            log_df = pd.concat([asset_0_returns, asset_1_returns], axis=1).dropna()
            
            # PCA-based Beta Estimation
            pca = PCA(n_components=1)
            pca.fit(log_df)

            weights = pca.components_[0]  
            if weights[1] == 0:
                continue  # Skip if division by zero

            beta = -weights[0] / weights[1]  
            spread = asset_0_returns - beta * asset_1_returns
            spread_normalized = (spread - spread.mean()) / spread.std()

            coint_name = f'{asset_0}_{asset_1}_Coin'
            coint_data.append(pd.DataFrame({coint_name: spread, f'Normalized_{coint_name}': spread_normalized}))
        
        if coint_data:
            combo_df = pd.concat(coint_data, axis=1)
            # Add original close prices and log returns back into the final DataFrame
            combo_df = pd.concat([combo_df, original_closes, log_returns, sin_time, cos_time,RSI,K_,D_,D_R,T_S,K_S,S_A,S_B,C_S], axis=1)

        return combo_df