# -*- coding: utf-8 -*-
"""ARIMA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18OJrFoTOf4ek5zMIpLQDGroNiv2782wq

# SETUP
"""

#BIBLIOTECAS
import datetime as dt
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
from sklearn.preprocessing import MinMaxScaler
from sklearn import preprocessing
import numpy as np


# IMPORTAÇÃO DB
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

downloaded = drive.CreateFile({'id':"138bRT5WPXfCdZj2fS_sMars4NlaQr75y"})
downloaded.GetContentFile('Sales2.csv')

"""## Carregando DB"""

# CARREGANDO DB
df = pd.read_csv('Sales2.csv', sep=';', na_values='?')
df.head()

"""# Pré-processamento"""

# Trata a coluna Timestamp e insere a coluna Weekday necessária para realizar os próximos cálculos
df['Timestamp']= pd.to_datetime(df['Timestamp'],format='%Y-%m-%d')

# Obtém a coluna Price(Somatório das vendas do dia)
df_class2 = df[['Timestamp', 'Price']].groupby(pd.Grouper(key='Timestamp', freq='1D')).sum()['Price']

# A partir daqui, um novo dataframe será gerado(df2) para trabalharmos
df2 = pd.DataFrame(df_class2)
# Tratamento para que a coluna Timestamp seja criada(o index está como Timestamp, por isso a necessidade dessa atribuição)
df2['Timestamp'] = df2.index
# Necessário dropar o index Timestamp para que o index seja resetado para inteiros
df2 = df2.reset_index(drop=True)
df2

"""#Séries Temporais

"""

from matplotlib.pylab import rcParams
import matplotlib.pyplot as plt

rcParams['figure.figsize'] = 15,6

#dateparse = lambda dates: dt.datetime.strptime(dates, '%d-%m-%y') 

ts = df2['Price'] 

plt.plot(df2['Timestamp'], ts)

# Gráfico da série por dia
df_year = df2
df_year = df.set_index('Timestamp', drop=False).groupby([pd.Grouper(key='Timestamp',freq='D')])['Price'].sum().reset_index()
df_year #= df_year.set_index('Timestamp')
plt.plot(df_year['Timestamp'],df_year['Price'])

# Gráfico da série a cada 2 DIAS
df_year = df2
df_year = df.set_index('Timestamp', drop=False).groupby([pd.Grouper(key='Timestamp',freq='2D')])['Price'].sum().reset_index()
df_year #= df_year.set_index('Timestamp')
plt.plot(df_year['Timestamp'],df_year['Price'])

# Gráfico da série por semana
df_year = df2
df_year = df.set_index('Timestamp', drop=False).groupby([pd.Grouper(key='Timestamp',freq='W')])['Price'].sum().reset_index()
df_year #= df_year.set_index('Timestamp')
plt.plot(df_year['Timestamp'],df_year['Price'])

"""## ARIMA MODEL"""

from datetime import datetime
dateparse = lambda dates: dt.datetime.strptime(dates, '%Y-%m-%d %H:%M:%S.000') 
series = pd.read_csv('Sales2.csv',  sep=';', na_values='?', header=0, parse_dates=['Timestamp'],date_parser=dateparse,index_col=0)

# Obtém a coluna Price(Somatório das vendas do dia)
df_class2 = df[['Timestamp', 'Price']].groupby(pd.Grouper(key='Timestamp', freq='1D')).sum()['Price']

df_class2

# model = ARIMA(series2, order=(1,0,0))
# model_fit = model.fit(disp=0)
# print(model_fit.summary())
from pandas import DataFrame
from statsmodels.tsa.arima_model import ARIMA
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

model = ARIMA(df_class2, order=(1,0,0))
model_fit = model.fit(disp=0)
print(model_fit.summary())
# plot residual errors
residuals = DataFrame(model_fit.resid)
residuals.plot()
plt.show()
residuals.plot(kind='kde')
plt.show()
print(residuals.describe())

from pandas import DataFrame
from statsmodels.tsa.arima_model import ARIMA
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

#O modelo ARIMA com parâmetros 1,1,0 possui melhor resultado do que com 1,0,0 Test MSE: 1539142.829 1140194
X = df_class2.values
size = int(len(X) * 0.75)
train, test = X[0:size], X[size:len(X)]
history = [x for x in train]
predictions = list()
for t in range(len(test)):
    model = ARIMA(history, order=(6,1,2))
    model_fit = model.fit()#disp=0
    output = model_fit.forecast()
    yhat = output[0]
    predictions.append(yhat)
    obs = test[t]
    history.append(obs)
    print('predicted=%f, expected=%f' % (yhat, obs))
error = mean_squared_error(test, predictions)
print('Test MSE: %.3f' % error)
print('rmse = ', np.sqrt(mean_squared_error(test, predictions)))
plt.plot(test)
plt.plot(predictions, color='red')
plt.show()

from sklearn.metrics import mean_absolute_error
mae = mean_absolute_error(test, predictions)
mae

"""GRID SEARCH

"""

import warnings
from math import sqrt
from pandas import read_csv
from pandas import datetime
from sklearn.metrics import mean_squared_error

# X has all time series values
X = df_class2.values

# evaluate an ARIMA model for a given order (p,d,q)
def evaluate_arima_model(X, arima_order):
	# prepare training dataset
	train_size = int(len(X) * 0.66)
	train, test = X[0:train_size], X[train_size:]
	history = [x for x in train]
	# make predictions
	predictions = list()
	for t in range(len(test)):
		model = ARIMA(history, order=arima_order)
		model_fit = model.fit()
		yhat = model_fit.forecast()[0]
		predictions.append(yhat)
		history.append(test[t])
	# calculate out of sample error
	rmse = sqrt(mean_squared_error(test, predictions))
	return rmse

# evaluate combinations of p, d and q values for an ARIMA model
def evaluate_models(dataset, p_values, d_values, q_values):
	dataset = dataset.astype('float32')
	best_score, best_cfg = float("inf"), None
	for p in p_values:
		for d in d_values:
			for q in q_values:
				order = (p,d,q)
				try:
					rmse = evaluate_arima_model(dataset, order)
					if rmse < best_score:
						best_score, best_cfg = rmse, order
					print('ARIMA%s RMSE=%.3f' % (order,rmse))
				except:
					continue
	print('Best ARIMA%s RMSE=%.3f' % (best_cfg, best_score))

# evaluate parameters
p_values = [0, 1, 2, 4, 6, 8, 10]
d_values = range(0, 3)
q_values = range(0, 3)
warnings.filterwarnings("ignore")
evaluate_models(X, p_values, d_values, q_values)

from statsmodels.tsa.stattools import adfuller
def test_stationarity(timeseries):

    #Determing rolling statistics
    rolmean = pd.Series(timeseries).rolling(window=100).mean()
    rolstd = pd.Series(timeseries).rolling(window=100).std()

    #Plot rolling statistics:
    orig = plt.plot(timeseries, color='blue',label='Original')
    mean = plt.plot(rolmean, color='red', label='Rolling Mean')
    std = plt.plot(rolstd, color='black', label = 'Rolling Std')
    plt.legend(loc='best')
    plt.title('Rolling Mean & Standard Deviation')
    plt.show(block=False)

    #Perform Dickey-Fuller test:
    print('Results of Dickey-Fuller Test:')
    dftest = adfuller(timeseries, autolag='AIC')
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value','#Lags Used','Number of Observations Used'])
    for key,value in dftest[4].items():
        dfoutput['Critical Value (%s)'%key] = value
    print(dfoutput)

# Média móvel da série
test_stationarity(df_class2)

"""## Exponential Smoothing

"""

import pandas as pd
from statsmodels.tsa.api import SimpleExpSmoothing
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
import math

# O objeto series é uma série com a data e o valor da venda
series = df_class2

series

#First Instance
ins1 = SimpleExpSmoothing(series).fit(smoothing_level=0.2,optimized=False)
ins1_cast = ins1.forecast(50)
ins1_fitted = ins1.fittedvalues

#Second Instance
ins2 = SimpleExpSmoothing(series).fit(smoothing_level=0.6,optimized=False)
ins2_cast = ins2.forecast(3)
ins2_fitted = ins2.fittedvalues

# Third Instance
ins3 = SimpleExpSmoothing(series).fit()
ins3_cast = ins3.forecast(3)
ins3_fitted = ins3.fittedvalues

plt.plot(series, label='realdata', color='black')
# SES with alpha = 0.2
plt.plot(ins1_fitted, label='alpha0.2', color='red')
plt.plot(ins1_cast, label='alpha0.2cast', color = 'red')
plt.legend(loc=2)
plt.show()

# RMSE para alpha = 0.2
error_alpha02 = mean_squared_error(series,ins1_fitted)
RMSE_alpha2 = math.sqrt(error_alpha02)
RMSE_alpha2

# MAE para alpha = 0.2
mae_02 = mean_absolute_error(series,ins1_fitted)
mae_02

# SES with alpha = 0.6
plt.plot(series, label='realdata', color='black')
plt.plot(ins2_fitted, label='alpha0.6', color='blue')
plt.plot(ins2_cast, label='alpha0.6cast', color = 'red')
plt.legend(loc=2)
plt.show()

# RMSE para alpha = 0.6
error_alpha06 = mean_squared_error(series,ins2_fitted)
error_alpha06
RMSE_alpha6 = math.sqrt(error_alpha06)
RMSE_alpha6

# MAE para alpha = 0.6
mae_06 = mean_absolute_error(series,ins2_fitted)
mae_06

# SES com stats model 
plt.plot(series, label='realdata', color='black')
plt.plot(ins3_fitted, label='stats', color='green')
plt.plot(ins3_cast, label='statscast', color = 'green')
plt.legend(loc=2)
plt.show()

error_stats = mean_squared_error(series,ins3_fitted)
error_stats
RMSE_stats = math.sqrt(error_stats)
RMSE_stats

# Erro médio absoluto
mae_stats = mean_absolute_error(series,ins3_fitted)
mae_stats

"""## Holt Method"""

from statsmodels.tsa.api import Holt

# Holt 1
fit1 = Holt(series).fit(smoothing_level=0.8, smoothing_slope=0.2,optimized=False)
f1fit = fit1.fittedvalues

# Holt 2
fit2 = Holt(series,damped=True).fit(smoothing_level=0.8,smoothing_slope=0.2)
f2fit = fit2.fittedvalues

# Plotando Holt 1 vs Serie temporal
plt.plot(series, label='realdata', color='black')
# Holt 1 = 0.2
plt.plot(f1fit, label='holt1', color='green')
plt.legend(loc=2)
plt.show()

# Erro do método Holt 1
error_holt1 = mean_squared_error(series,f1fit)
error_holt1

# Plotando Holt 1 vs Serie temporal
plt.plot(series, label='realdata', color='black')
# Holt 1 = 0.2
plt.plot(f2fit, label='holt2', color='red')
plt.legend(loc=2)
plt.show()

# Erro do método Holt 2
error_holt2 = mean_squared_error(series,f2fit)
error_holt2