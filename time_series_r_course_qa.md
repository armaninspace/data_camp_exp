# R Time Series Courses: Q/A Pairs

## Forecasting in R (`24491`)

Q: How do you start analyzing a time series in R?  
A: By plotting the data first to see patterns, unusual observations, and changes over time.

Q: Why are benchmark forecasting methods useful?  
A: They give you baseline methods and help you check whether your forecasting approach is actually using the available information well.

Q: How is forecast accuracy handled in this course?  
A: The course covers methods for measuring forecast accuracy so models can be compared and evaluated.

Q: What is exponential smoothing?  
A: It is a forecasting approach that uses weighted averages of past observations, with more recent values getting higher weight.

Q: What is an ARIMA model used for?  
A: It is used for time series forecasting by modeling autocorrelations in the data.

Q: How are ARIMA and exponential smoothing different?  
A: Exponential smoothing focuses on trend and seasonality, while ARIMA focuses on autocorrelation structure.

Q: What do advanced methods add beyond basic ARIMA?  
A: They handle more complex seasonality and allow outside information like holidays or competitor activity to be included.

## Visualizing Time Series Data in R (`24593`)

Q: What is introduced first in this course?  
A: Basic R tools for time series visualization.

Q: What do univariate time series plots help you understand?  
A: They help you examine distribution, central tendency, and spread in a single series.

Q: What is the goal of multivariate time series visualization?  
A: To identify patterns across pairs or groups of time series.

Q: What kind of practical task is included in the course?  
A: A stock-picking case study where you use visualization to compare a candidate stock with an existing portfolio.

Q: How is visualization applied in the stock case study?  
A: By analyzing the statistical properties of individual stocks relative to the current portfolio to support a better investment choice.

## Case Study: Analyzing City Time Series Data in R (`24594`)

Q: What core R packages are emphasized in this course?  
A: `xts` and `zoo`.

Q: What do you do with the flight data chapter?  
A: Practice time series manipulation in R using Boston Logan flight-arrival data.

Q: What time series skills are practiced with weather data?  
A: Merging multiple `xts` objects and isolating specific periods of data.

Q: What kinds of economic indicators are used in the course?  
A: Indicators such as GDP per capita and unemployment for the U.S. and Massachusetts.

Q: What is the focus of the sports data chapter?  
A: Assembling time series data on Boston sports teams over several years.

Q: What is the broader purpose of the case study?  
A: To use real-world time series datasets to explore factors related to Boston tourism.
