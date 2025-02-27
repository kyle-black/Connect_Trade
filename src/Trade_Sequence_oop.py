import pandas as pd
import numpy as pn
import live_data_pull
import model_run
import process_data
import Buy_Sell
import process_data



class TradeProcess:
    def __init__(self, forex_list):
        
        self.forex_list = forex_list
        self.df = None



  #  def pull_forex_prices(self):

   #     df =live_data_pull.symbol_cycle(self.forex_list)
    #    return df

    def data_processes(self):
        self.df =live_data_pull.symbol_cycle(self.forex_list)
        
        self.df = process_data.make_features(self.df)
        return self.df

    def make_predictions(self):
        pass

    def live_trade(self):
        pass




if __name__ == "__main__":
    print('Running Model Process')
    forex_list = ['eurusd', 'eurjpy', 'eurgbp', 'audjpy', 'audusd', 'gbpjpy', 'nzdjpy', 'usdcad', 'usdchf', 'usdhkd', 'usdjpy']
    
    TP = TradeProcess(forex_list)
    df = TP.data_processes()

    print(df)