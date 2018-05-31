import datetime
import numpy as np
import pandas as pd
import os
from pathlib import Path
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API
from pytdx.params import TDXParams

class Stock():
    
    PRICE_TOLERANT = 0.001
    PRICE_PRCISION = 0.01
    
    TDX_IP = '119.147.212.81'
    TDX_PORT = 7709
    
    def __init__(self, code):
        self.code = str(code)
        self.market = 2
        if code.startswith('002') or code.startswith('300') or code.startswith('000'):
            self.market = TDXParams.MARKET_SZ
        elif code.startswith('60'):
            self.market = TDXParams.MARKET_SH
        if self.market == 2:
            raise Exception('code should be stock code')
        
        self.api = TdxHq_API()
        
        # stock path
        self.stock_path = Path.home().joinpath('stocks').joinpath(self.code)
        self.day_k_path = self.stock_path.joinpath('day_k')
        self.vpd_path = self.stock_path.joinpath('vpd')
        if not Path.exists(self.stock_path):
            os.makedirs(self.stock_path)
        if not Path.exists(self.day_k_path):
            os.makedirs(self.day_k_path)
        if not Path.exists(self.vpd_path):
            os.makedirs(self.vpd_path)
        
        # get xdxr
        self.xdxr = self.get_xdxr()
        
        # get day-k data
        self.day_k = self.get_all_day_k()
        self.trading_days = pd.to_datetime(self.day_k.datetime).dt.strftime('%Y%m%d')
        self.day_k.datetime = self.trading_days
            
        # get day minute time data
        self.vpd = self.get_minute_vpd('20171124')

    def get_xdxr(self):
        xdxr_path = self.stock_path.joinpath('xdxr_' + str(datetime.datetime.now().date()) + '.csv')
        if not Path.exists(xdxr_path):
            with self.api.connect(self.TDX_IP, self.TDX_PORT):
                xdxr = self.api.to_df(self.api.get_xdxr_info(self.market, self.code))
                if xdxr.empty:
                    raise Exception('xdxr empty')
                xdxr.to_csv(xdxr_path)
            #pg = xdxr.loc[xdxr['peigu'] > 0]
            #if not pg.empty:
             #   raise Exception('stock has peigu')
        return pd.read_csv(xdxr_path, index_col = 0)
        
    def get_all_day_k(self):
        day_k_file = self.day_k_path.joinpath(str(datetime.datetime.now().date()) + '.csv')
        if not Path.exists(day_k_file):
            day_k = pd.DataFrame()
            with self.api.connect(self.TDX_IP, self.TDX_PORT):
                for offset in range(0,10000,800):
                    df = self.api.to_df(self.api.get_security_bars(9, self.market, self.code, offset, 800))
                    if not df.empty:
                        day_k = pd.concat([df, day_k], ignore_index = True)
                    else:
                        break
            if day_k.size < 10:
                raise Exception('day_k empty')
                
            day_k = day_k[day_k.vol > 0]
            day_k.reset_index(drop=True, inplace=True)
            #dt = pd.to_datetime(day_k.datetime)
            #day_k = day_k.drop(columns=['datetime'])
            #day_k = day_k.assign(datetime = dt)
            day_k.to_csv(day_k_file)
            
        return pd.read_csv(day_k_file, index_col = 0)
    
    # day minute time volumn-price-distribution
    def get_minute_vpd(self, date):
        vpd_file = self.vpd_path.joinpath(str(date) + '.csv')
        if not Path.exists(vpd_file):   
            with self.api.connect(self.TDX_IP, self.TDX_PORT):
                #self.fs = api.get_minute_time_data(self.market, self.code)
                raw_df = self.api.to_df(self.api.get_history_minute_time_data(self.market, self.code, date))
                if raw_df.shape != (240, 2):
                    raise Exception('raw_df wrong size')
                
            vpd = pd.DataFrame()
            vpd = vpd.append(raw_df.sort_values(by=['price']), ignore_index=True)

            last_price = -1
            last_index = -1
            drop_index = []
            for v in vpd.index:
                price = vpd.at[v, 'price']
                if self.price_equal(price, last_price):
                    vpd.at[last_index, 'vol'] += vpd.at[v, 'vol']
                    drop_index.append(v)
                else:
                    last_price = price
                    last_index = v

            vpd = vpd.drop(drop_index)
            vpd.reset_index(drop=True, inplace=True)
            vpd.to_csv(vpd_file)

        return pd.read_csv(vpd_file, index_col = 0)
            
    def price_range(self, start, end):
        while start < (end - self.PRICE_TOLERANT):
            yield round(start,2)
            start += self.PRICE_PRCISION

    def price_equal(self, a,b):
        if abs(a-b) < self.PRICE_TOLERANT:
            return True
        else:
            return False

    def price_higher(self, a,b):
        if (a-b) > (self.PRICE_PRCISION - self.PRICE_TOLERANT):
            return True
        else:
            return False

    def price_lower(self, a,b):
        if (b-a) > (self.PRICE_PRCISION - self.PRICE_TOLERANT):
            return True
        else:
            return False

    def test_vpd(self):
        tri_factor = 1/np.tan(45)
        chip_hist = []
        chip = pd.DataFrame()
        chip_inc = pd.DataFrame()
        chip_inc_temp = pd.DataFrame()
        for day in self.trading_days[0:20]:
            if datetime.datetime.now().date().strftime('%Y%m%d') == day:
                continue
    
            vpd = self.get_minute_vpd(day)
            vpd.reset_index(drop=True, inplace=True)
            #vpd.set_index('price', inplace=True)
    
            if chip.empty:
                chip = pd.DataFrame(vpd, copy=True)
                chip['vol'] = chip['vol'].astype('float64')
                chip.drop(chip.index, inplace=True)
                chip = chip.append({'price': 4.79, 'vol': 6000*10000/100}, ignore_index=True)
    
                chip_inc = pd.DataFrame(chip, copy=True)
                chip_inc['vol'] = chip_inc['vol'].astype('float64')
    
                chip_inc_temp = pd.DataFrame(chip, copy=True)
                chip_inc_temp['vol'] = chip_inc_temp['vol'].astype('float64')
    
            chip_inc['vol'] = np.zeros(chip_inc.shape[0])
            for i, p_outer in vpd.iterrows():
                chip_inc_temp['vol'] = np.zeros(chip_inc_temp.shape[0])
                for j, p_inner in chip.iterrows():
                    inc = 0
                    if p_outer.price > chip.iloc[-1].price:
                        inc = (p_outer.price - p_inner.price)*tri_factor
                    else:
                        inc = (chip.iloc[-1].price - p_inner.price)*tri_factor
                    chip_inc_temp.at[j, 'vol'] += inc
                c = p_outer.vol/chip_inc_temp.sum().vol
                chip_inc_temp['vol'] = chip_inc_temp['vol'].mul(c)
                chip_inc['vol'] = chip_inc['vol'].add(chip_inc_temp['vol'])   
    
            chip['vol'] = chip['vol'].sub(chip_inc['vol'])
            sum_negative = 0.0
            for i, r in chip.iterrows():
                if r.vol < 0:
                    sum_negative -= r.vol
                    chip.at[i, 'vol'] = 0.0
    
            for i, r in chip.iterrows():        
                if r.vol >= sum_negative:
                    chip.at[i, 'vol'] -= sum_negative
                    break
                else:         
                    sum_negative -= chip.at[i, 'vol']
                    chip.at[i, 'vol'] = 0.0
    
            chip = chip.merge(vpd, how='outer', left_on='price', right_on='price', sort=True, suffixes=['', '_inc'])
            for i, r in chip.iterrows():
                if np.isnan(r.vol):
                    chip.at[i, 'vol'] = 0.0
                if not np.isnan(r.vol_inc):
                    chip.at[i, 'vol'] += chip.at[i, 'vol_inc']
            chip.drop('vol_inc', axis=1, inplace=True)
            chip.drop(chip[chip['vol']==0].index, inplace=True)
    
            chip_inc = pd.DataFrame(chip, copy=True)
            chip_inc['vol'] = chip_inc['vol'].astype('float64')
    
            chip_inc_temp = pd.DataFrame(chip, copy=True)
            chip_inc_temp['vol'] = chip_inc_temp['vol'].astype('float64')
    
            chip_hist.append(pd.DataFrame(chip, copy=True))
            print(day)
            if abs(chip.sum().vol - 600000) > 0.1:
                raise Exception('vol error')
       
if __name__ == '__main__':
    s = Stock('603363')
    s.test_vpd()
    
    
    
    
    
    
    
    
    
    
    