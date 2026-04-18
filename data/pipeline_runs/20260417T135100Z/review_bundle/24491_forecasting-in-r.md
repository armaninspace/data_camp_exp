# Forecasting in R (`24491`)

## Q/A Pairs

Q: How can I spot trends or seasonality in my time series plots?  
A: You can spot trends or seasonality in your time series plots by visually examining the graphs for patterns, such as consistent upward or downward movements (trends) or regular, repeating cycles (seasonality).

Q: What should I look for in a time series plot to identify unusual patterns or outliers?  
A: Look for features in the plot that stand out from the general pattern, such as sudden spikes, drops, or changes that do not fit the overall trend or seasonality. These may indicate unusual observations or outliers.

Q: What is a time series, and how do I create one in R?  
A: A time series is a sequence of data points measured over time. In R, you create a time series object to plot your data and analyze patterns such as trends and seasonality.

Q: Why is it important to plot time series data before analyzing it?  
A: Plotting time series data is important because it helps visualize features like patterns, unusual observations, and changes over time, which should be considered when choosing forecasting methods.

Q: How can I compare the performance of different forecasting models?  
A: You can compare the performance of different forecasting models by using methods for measuring forecast accuracy, as discussed in the course.

Q: What does it mean if my forecasting method hasn't used all the available information?  
A: If your forecasting method hasn't used all the available information, it means the method may not have adequately utilized the data, which can lead to less accurate forecasts.

Q: How do I measure how accurate my forecasts are?  
A: You measure forecast accuracy using specific methods for measuring forecast accuracy, which are covered in the course.

Q: What are benchmark forecasting methods, and why do we use them?  
A: Benchmark forecasting methods are simple methods used as a reference point to evaluate the performance of more complex forecasting models.

Q: When should I use exponential smoothing for forecasting?  
A: Use exponential smoothing when you need reliable forecasts quickly for a wide range of time series, especially in business applications.

Q: Why do more recent observations get more weight in exponential smoothing?  
A: More recent observations get more weight in exponential smoothing because the method assigns exponentially decreasing weights to older data, making recent data more influential in the forecast.

Q: What is exponential smoothing, and how does it work?  
A: Exponential smoothing is a forecasting method that produces forecasts as weighted averages of past observations, with weights that decrease exponentially for older data.

Q: Are there any limitations to using exponential smoothing methods?  
A: Exponential smoothing methods may not work well for time series with complicated seasonality, such as weekly or hourly patterns, or when additional information needs to be included.

Q: Can ARIMA models handle seasonality and trends in the data?  
A: ARIMA models can handle trends and, with extensions, can also handle seasonality in the data.

Q: How do ARIMA models use autocorrelation in time series data?  
A: ARIMA models use autocorrelation by aiming to describe the autocorrelations present in the time series data.

Q: How do I decide whether to use ARIMA or exponential smoothing for my data?  
A: Decide based on the data: use exponential smoothing for trend and seasonality, and ARIMA if you need to model autocorrelations.

Q: What is an ARIMA model, and how is it different from exponential smoothing?  
A: An ARIMA model is a time series forecasting approach that describes autocorrelations in the data, while exponential smoothing is based on modeling trend and seasonality.

Q: How can I include extra information, like holidays or competitor actions, in my forecasting models?  
A: You can include extra information, such as holidays or competitor actions, by extending ARIMA models to allow for additional variables.

Q: What should I do if my data has complicated seasonality, like weekly or hourly patterns?  
A: Use advanced forecasting methods that can handle more complicated seasonality, such as weekly or hourly patterns.

Q: How do advanced forecasting methods improve on the basic models covered earlier in the course?  
A: Advanced forecasting methods improve on basic models by handling more complicated seasonality and allowing the inclusion of additional information, such as holidays or competitor activity.

Q: What are the limitations of basic ARIMA and exponential smoothing models when dealing with real-world data?  
A: Basic ARIMA and exponential smoothing models may not perform well with weekly or hourly data and cannot include additional information like holidays or competitor activity.

## Scraped Course Description

### Summary

Learn how to make predictions about the future using time series forecasting
in R including ARIMA models and exponential smoothing methods.

### Overview

Learn how to make predictions about the future using time series forecasting
in R including ARIMA models and exponential smoothing methods.

Use Forecasting in R for Data-Driven Decision Making

This course provides an introduction to time series forecasting using R.

Forecasting involves making predictions about the future. It is required in
many situations, such as deciding whether to build another power generation
plant in the next ten years or scheduling staff in a call center next week.

Forecasts may be needed several years in advance (for the case of capital
investments), or only a few minutes beforehand (for telecommunication
routing). Whatever the circumstances or time horizons involved, reliable
forecasting is essential to good data-driven decision-making.

Build Accurate Forecast Models with ARIMA and Exponential Smoothing

You’ll start this course by creating time series objects in R to plot your
data and discover trends, seasonality, and repeated cycles. You’ll be
introduced to the concept of white noise and look at how you can conduct a
Ljung-Box test to confirm randomness before moving on to the next chapter,
which details benchmarking methods and forecast accuracy.

Being able to test and measure your forecast accuracy is essential for
developing usable models. This course reviews a variety of methods before
diving into exponential smoothing and ARIMA models, which are two of the
most widely-used approaches to time series forecasting.

Before you complete the course, you’ll learn how to use advanced ARIMA
models to include additional information in them, such as holidays and
competitor activity.

### Syllabus

1. Exploring and visualizing time series in R  
The first thing to do in any data analysis task is to plot the data.
Graphs enable many features of the data to be visualized, including
patterns, unusual observations, and changes over time. The features
that are seen in plots of the data must then be incorporated, as far
as possible, into the forecasting methods to be used.

2. Benchmark methods and forecast accuracy  
In this chapter, you will learn general tools that are useful for
many different forecasting situations. It will describe some methods
for benchmark forecasting, methods for checking whether a
forecasting method has adequately utilized the available
information, and methods for measuring forecast accuracy. Each of
the tools discussed in this chapter will be used repeatedly in
subsequent chapters as you develop and explore a range of
forecasting methods.

3. Exponential smoothing  
Forecasts produced using exponential smoothing methods are weighted
averages of past observations, with the weights decaying
exponentially as the observations get older. In other words, the
more recent the observation, the higher the associated weight. This
framework generates reliable forecasts quickly and for a wide range
of time series, which is a great advantage and of major importance
to applications in business.

4. Forecasting with ARIMA models  
ARIMA models provide another approach to time series forecasting.
Exponential smoothing and ARIMA models are the two most widely-used
approaches to time series forecasting, and provide complementary
approaches to the problem. While exponential smoothing models are
based on a description of the trend and seasonality in the data,
ARIMA models aim to describe the autocorrelations in the data.

5. Advanced methods  
The time series models in the previous chapters work well for many
time series, but they are often not good for weekly or hourly data,
and they do not allow for the inclusion of other information such as
the effects of holidays, competitor activity, changes in the law,
etc. In this chapter, you will look at some methods that handle more
complicated seasonality, and you consider how to extend ARIMA models
in order to allow other information to be included in the them.
