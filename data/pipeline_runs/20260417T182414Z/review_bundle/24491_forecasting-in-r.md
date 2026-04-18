# Forecasting in R (`24491`)

## Selected Q/A Pairs

Q: What does forecast accuracy tell me about whether I should trust a forecasting method?  
A: Forecast accuracy tells you how well a forecasting method has used the available information. High accuracy means the method is reliable and you can trust its forecasts; low accuracy suggests the method may not be suitable.

Q: Why do we compare a forecasting model against benchmark methods?  
A: We compare a forecasting model against benchmark methods to check if the model has adequately used the available information and to measure if it performs better than simple alternatives.

Q: How do I know when a benchmark method is no longer enough on its own?  
A: A benchmark method is no longer enough on its own when it does not adequately utilize the available information or when its forecast accuracy is not sufficient for your needs.

Q: How do I measure forecast accuracy?  
A: You measure forecast accuracy by using methods that compare the forecasts to actual outcomes, allowing you to assess how well the forecasting method performs.

Q: Why do more recent observations get more weight in exponential smoothing?  
A: More recent observations get more weight in exponential smoothing because the method uses exponentially decreasing weights, making recent data more influential for reliable forecasts.

Q: When is exponential smoothing a poor fit for the data?  
A: Exponential smoothing is a poor fit when the data has features it cannot handle well, such as complicated seasonality or when other information (like holidays or competitor activity) needs to be included.

Q: How is ARIMA different from exponential smoothing?  
A: ARIMA models focus on describing the autocorrelations in the data, while exponential smoothing models are based on describing trend and seasonality.

Q: When would ARIMA be a better choice than exponential smoothing?  
A: ARIMA would be a better choice when the main feature of the data is autocorrelation rather than just trend or seasonality.

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
