from itertools import combinations
import numpy as np

# List of forex pairs
#forex_pairs = ['EURUSD', 'EURJPY', 'USDJPY', 'GBPUSD']
#forex_pairs = ['eurusd','eurjpy', 'eurgbp','audjpy','audusd','gbpjpy','nzdjpy','usdcad','usdchf','usdhkd','usdjpy']
    
def generate_combos(forex_pairs):
# Generate all unique combinations of pairs
    pair_combinations = list(combinations(forex_pairs, 2))
    return pair_combinations


# Print the result
#for pair in pair_combinations:
#    print(pair)


def combos_to_df(df, forex_pairs):
        """Computes log returns for forex pairs and stores pair combinations."""
        #self.combos = self.generate_combos()
        forex_pais = generate_combos(forex_pairs)
        
        # Compute log returns
        for pair in forex_pairs:
            df[f'{pair}_log_return'] = np.log(df[f'{pair}_close']) - np.log(df[f'{pair}_close'].shift(1))
        
        return df