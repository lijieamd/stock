# -*- coding: utf-8 -*-
"""
Created on Mon May 28 19:03:47 2018

@author: lijie
"""

import datetime
import pandas as pd
from pathlib import Path
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API
from pytdx.params import TDXParams

class Stock():
    def __init__(self, code):
        self.code = str(code)
        self.market = 2
        if code.startswith('002') or code.startswith('300') or code.startswith('000'):
            self.market = TDXParams.MARKET_SZ
        elif code.startswith('60'):
            self.market = TDXParams.MARKET_SH
        if self.market == 2:
            raise Exception('code should be stock code')
        
        api = TdxHq_API()
        
        stock_path = Path.home().joinpath('stocks').joinpath(self.code)
        if not Path.exists(stock_path):
            Path.mkdir(stock_path)
        xdxr_path = stock_path.joinpath('xdxr_' + str(datetime.datetime.now().date()) + '.csv')
        if not Path.exists(xdxr_path):
            with api.connect('119.147.212.81', 7709):
                xdxr = api.to_df(api.get_xdxr_info(self.market, self.code))
                xdxr.to_csv(xdxr_path)
        self.xdxr = pd.read_csv(xdxr_path)
        pg = self.xdxr.loc[self.xdxr['peigu'] > 0]
        #if not pg.empty:
         #   raise Exception('stock has peigu')


if __name__ == '__main__':
    s = Stock('002466')
    #home = str(Path.home())