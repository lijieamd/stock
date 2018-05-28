# -*- coding: utf-8 -*-
"""
Created on Sat May 26 17:51:14 2018

@author: lijie
"""

from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API
from pytdx.params import TDXParams

api = TdxHq_API()
exapi = TdxExHq_API()

with api.connect('14.215.128.18', 7709):
    #data1 = api.get_minute_time_data(0, '000002')
    #data2 = api.get_history_minute_time_data(TDXParams.MARKET_SZ, '000002', 20180525)
    data = api.get_transaction_data(TDXParams.MARKET_SZ, '000001', 0, 30)