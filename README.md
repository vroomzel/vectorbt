![](https://img.shields.io/travis/polakowo/vectorbt/master.svg?branch=master&style=for-the-badge)
![](https://img.shields.io/codecov/c/github/polakowo/vectorbt?style=for-the-badge)
![](https://img.shields.io/pypi/v/vectorbt?color=blue&style=for-the-badge)

# vectorbt

![Logo](https://raw.githubusercontent.com/polakowo/vectorbt/master/logo.png)

vectorbt is a backtesting library on steroids - it operates entirely on pandas and NumPy objects, and is 
accelerated by [Numba](https://github.com/numba/numba) to analyze trading strategies at speed and scale :fire:

In contrast to conventional libraries, vectorbt represents trading data as nd-arrays.
This enables superfast computation using vectorized operations with NumPy and non-vectorized but compiled 
operations with Numba, for example, for hyperparameter optimization. It also integrates 
[plotly.py](https://github.com/plotly/plotly.py) and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets) 
to display complex charts and dashboards akin to Tableau right in the Jupyter notebook. Due to high 
performance, vectorbt is able to process large amounts of data even without GPU and parallelization (both are work 
in progress), and enable the user to interact with data-hungry widgets without significant delays.

With vectorbt you can
* Analyze and engineer features for any time series data
* Supercharge pandas and your favorite tools to run much faster
* Test thousands of strategies, configurations, assets, and time ranges in one go
* Test machine learning models
* Build interactive charts/dashboards without leaving Jupyter

## Example

Here a snippet for testing 4851 window combinations of a dual SMA crossover strategy on the whole Bitcoin history 
in under 5 seconds (Note: compiling for the first time may take a while):

```python
import vectorbt as vbt
import numpy as np
import yfinance as yf

# Fetch daily price of Bitcoin
close = yf.Ticker("BTC-USD").history(period="max")['Close']

# Compute moving averages for all combinations of fast and slow windows
windows = np.arange(2, 101)
fast_ma, slow_ma = vbt.MA.run_combs(close, window=windows, r=2, short_names=['fast', 'slow'])

# Generate crossover signals for each combination
entries = fast_ma.ma_above(slow_ma, crossed=True)
exits = fast_ma.ma_below(slow_ma, crossed=True)

# Run simulation
portfolio = vbt.Portfolio.from_signals(close, entries, exits, fees=0.001, freq='1D')

# Get total return, reshape to symmetric matrix, and plot the whole thing
fig = portfolio.total_return().vbt.heatmap(
    x_level='fast_window', y_level='slow_window', symmetric=True,
    trace_kwargs=dict(colorbar=dict(title='Total return', tickformat='%')))
fig.show()
```

![dmac_heatmap.png](https://raw.githubusercontent.com/polakowo/vectorbt/master/img/dmac_heatmap.png)

Digging into each strategy configuration is as simple as indexing with pandas:

```python-repl
>>> portfolio[(14, 38)].stats()
Start                            2014-09-17 00:00:00
End                              2020-11-17 00:00:00
Duration                          2254 days 00:00:00
Total Profit                                 11203.3
Total Return [%]                             11203.3
Benchmark Return [%]                         3753.41
Position Coverage [%]                        58.0302
Max. Drawdown [%]                            52.7562
Avg. Drawdown [%]                            8.35486
Max. Drawdown Duration             513 days 00:00:00
Avg. Drawdown Duration    36 days 00:24:24.406779661
Num. Trades                                       30
Win Rate [%]                                 56.6667
Best Trade [%]                               247.337
Worst Trade [%]                             -13.9102
Avg. Trade [%]                               23.1471
Max. Trade Duration                156 days 00:00:00
Avg. Trade Duration                 42 days 04:48:00
Expectancy                                   225.217
SQN                                          1.45906
Gross Exposure                              0.580302
Sharpe Ratio                                 1.70494
Sortino Ratio                                2.67607
Calmar Ratio                                 2.18027
Name: (14, 38), dtype: object

>>> fig = portfolio[(14, 38)].plot(template='plotly_dark')
>>> fig.update_traces(xaxis="x1")
>>> fig.update_xaxes(spikemode='across+marker')
>>> fig.show()
```

![dmac_portfolio.png](https://raw.githubusercontent.com/polakowo/vectorbt/master/img/dmac_portfolio.png)

## Motivation

While there are [many other great backtesting packages for Python](https://github.com/mementum/backtrader#alternatives), 
vectorbt is more of a data science tool: it excels at processing performance and offers interactive tools to explore 
complex phenomena in trading. With it you can traverse a huge number of strategy configurations, time periods and 
instruments in little time, to explore where your strategy performs best and to uncover hidden patterns in data.

Take a simple [Dual Moving Average Crossover](https://en.wikipedia.org/wiki/Moving_average_crossover) strategy 
for example. By calculating the performance of each reasonable window combination and plotting the whole thing 
as a heatmap (as we do above), you can analyze how performance depends upon window size. If you additionally 
compute the same heatmap over multiple time periods, you may figure out how performance varies with downtrends 
and uptrends. Finally, by running the same pipeline over other strategies such as holding and trading randomly, 
you can compare them and decide whether your strategy is worth executing. With vectorbt, this analysis can 
be done in minutes and save you time and cost of getting the same insights elsewhere.

## How it works?

vectorbt combines pandas, NumPy and Numba sauce to obtain orders-of-magnitude speedup over other libraries. 
It natively works on pandas objects, while performing all computations using NumPy and Numba under the hood. 
This way, it is often much faster than pandas alone:

```python-repl
>>> import numpy as np
>>> import pandas as pd
>>> import vectorbt as vbt

>>> big_ts = pd.DataFrame(np.random.uniform(size=(1000, 1000)))

# pandas
>>> %timeit big_ts.expanding().max()
48.4 ms ± 557 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

# vectorbt
>>> %timeit big_ts.vbt.expanding_max()
8.82 ms ± 121 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
```

In contrast to most other similar backtesting libraries where backtesting is limited to simple arrays 
(think of an array for price, an array for signals, etc.), vectorbt is optimized for working with 
2-dimensional data: it treats index of a DataFrame as time axis and columns as distinct features
that should be backtest, and performs any calculation on the entire matrix at once. This way, user can 
construct huge matrices with thousands of columns and calculate the performance for each one with a single 
matrix operation, without any "Pythonic" loops.

To make the library easier to use, vectorbt introduces a namespace (accessor) to pandas objects 
(see [extending pandas](https://pandas.pydata.org/pandas-docs/stable/development/extending.html)). 
This way, user can easily switch between native pandas functionality and highly-efficient vectorbt 
methods. Moreover, each vectorbt method is flexible and can work on both Series and DataFrames.

## Features

- Extends pandas using a custom `vbt` accessor
    -> Compatible with any library
- For high performance, most operations are done strictly using NumPy and Numba 
    -> Much faster than comparable operations in pandas
    
```python-repl
# pandas
>>> %timeit big_ts + 1
242 ms ± 3.58 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# vectorbt
>>> %timeit big_ts.vbt + 1
3.32 ms ± 19.7 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
```
    
- Helper functions for combining, transforming, and indexing NumPy and pandas objects
    - NumPy-like broadcasting for pandas, among other features
    
```python-repl
# pandas
>>> pd.Series([1, 2, 3]) + pd.DataFrame([[1, 2, 3]])
   0  1  2
0  2  4  6

# vectorbt
>>> pd.Series([1, 2, 3]).vbt + pd.DataFrame([[1, 2, 3]])
   0  1  2
0  2  3  4
1  3  4  5
2  4  5  6
```
   
- Compiled versions of common pandas functions, such as rolling, groupby, and resample

```python-repl
# pandas
>>> %timeit big_ts.rolling(2).apply(np.mean, raw=True)
7.32 s ± 431 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# vectorbt
>>> mean_nb = njit(lambda col, i, x: np.mean(x))
>>> %timeit big_ts.vbt.rolling_apply(2, mean_nb)
86.2 ms ± 7.97 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

- Drawdown analysis

```python-repl
>>> pd.Series([2, 1, 3, 2]).vbt.drawdowns().plot().show()
```

![drawdowns.png](https://raw.githubusercontent.com/polakowo/vectorbt/master/img/drawdowns.png)

- Functions for working with signals
    - Entry, exit and random signal generation, ranking and distance functions
    - Signal factory for building iterative signal generators with ease
    
```python-repl
>>> pd.Series([False, True, True, True]).vbt.signals.first()
0    False
1     True
2    False
3    False
dtype: bool
```
    
- Functions for working with returns
    - Compiled versions of metrics found in [empyrical](https://github.com/quantopian/empyrical)

```python-repl
>>> pd.Series([0.01, -0.01, 0.01]).vbt.returns(freq='1D').sharpe_ratio()
5.515130702591433
```
    
- Class for modeling portfolios
    - Accepts signals, orders, and custom order function
    - Supports long and short positions
    - Supports individual and multi-asset mixed portfolios
    - Provides metrics and tools for analyzing returns, orders, trades and positions
    
```python-repl
>>> price = [1., 2., 3., 2., 1.]
>>> entries = [True, False, True, False, False]
>>> exits = [False, True, False, True, False]
>>> portfolio = vbt.Portfolio.from_signals(price, entries, exits, freq='1D')
>>> portfolio.trades().plot().show()
```

![trades.png](https://raw.githubusercontent.com/polakowo/vectorbt/master/img/trades.png)
    
- Technical indicators with full Numba support
    - Moving average, Bollinger Bands, RSI, Stochastic Oscillator, MACD, and more
    - Each offers methods for generating signals and plotting
    - Each allows arbitrary parameter combinations, from arrays to Cartesian products
    
```python-repl
>>> vbt.MA.run([1, 2, 3], window=[2, 3], ewm=[False, True]).ma
ma_window     2         3
ma_ewm    False      True 
0           NaN       NaN
1           1.5       NaN
2           2.5  2.428571
``` 

- Indicator factory for building complex technical indicators with ease
    - Supports [TA-Lib](https://github.com/mrjbq7/ta-lib) indicators out of the box
    
```python-repl
>>> SMA = vbt.IndicatorFactory.from_talib('SMA')
>>> SMA.run([1., 2., 3.], timeperiod=[2, 3]).real
sma_timeperiod    2    3
0               NaN  NaN
1               1.5  NaN
2               2.5  2.0
``` 
    
- Interactive Plotly-based widgets to visualize backtest results
    - Full integration with ipywidgets for displaying interactive dashboards in Jupyter

```python-repl
>>> a = np.random.normal(0, 4, size=10000)
>>> pd.Series(a).vbt.box(horizontal=True, trace_kwargs=dict(boxmean='sd')).show()
``` 

![Box.png](https://raw.githubusercontent.com/polakowo/vectorbt/master/img/Box.png)

## Installation

```
pip install vectorbt
```

See [Jupyter Notebook and JupyterLab Support](https://plotly.com/python/getting-started/#jupyter-notebook-support) 
for Plotly figures.

## [Documentation](https://polakowo.io/vectorbt/)

## Example notebooks

- [Assessing performance of DMAC on Bitcoin](https://nbviewer.jupyter.org/github/polakowo/vectorbt/blob/master/examples/BitcoinDMAC.ipynb)
- [Comparing effectiveness of stop signals](https://nbviewer.jupyter.org/github/polakowo/vectorbt/blob/master/examples/StopSignals.ipynb)
- [Backtesting per trading session](https://nbviewer.jupyter.org/github/polakowo/vectorbt/blob/master/examples/TradingSessions.ipynb)

Note: you will need to run the notebook to play with widgets.

## Dashboards

- [Detecting and backtesting common candlestick patterns](https://github.com/polakowo/vectorbt/tree/master/apps/candlestick-patterns)
