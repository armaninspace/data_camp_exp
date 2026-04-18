# Forecasting in R (`24491`)

## Curated Core Q/A Pairs

Q: How is ARIMA different from exponential smoothing?  
A: Exponential smoothing models describe trend and seasonality, while ARIMA models focus on modeling autocorrelations in the data.

Q: When would ARIMA be a better choice than exponential smoothing?  
A: ARIMA is a better choice when modeling the autocorrelations in the data is important, rather than just trend and seasonality.

Q: Why do we compare a forecasting model against benchmark methods?  
A: We compare against benchmark methods to check if a forecasting model has adequately used the available information and to measure forecast accuracy.

Q: How do I know when a benchmark method is no longer enough on its own?  
A: A benchmark method is no longer enough when it does not adequately utilize the available information or fails to provide accurate forecasts.

Q: Why do more recent observations get more weight in exponential smoothing?  
A: More recent observations get more weight because exponential smoothing assigns higher weights to newer data, with weights decaying exponentially for older observations.

Q: When is exponential smoothing a poor fit for the data?  
A: Exponential smoothing is a poor fit when the data has patterns that cannot be captured by weighted averages of past observations.

Q: What does forecast accuracy tell me about whether I should trust a forecasting method?  
A: Forecast accuracy indicates how well a method uses available information and helps determine if the forecasts are reliable.

Q: How do I know when a time series plot is revealing something my forecasting method needs to capture?  
A: If a time series plot shows patterns, unusual observations, or changes over time, your forecasting method should aim to capture these features.

## Policy Summary

- bucket distribution: {"curated_core": 8, "cache_servable": 12, "analysis_only": 15}
- family coverage: {"bridge": 2, "friction": 16, "entry": 9, "diagnostic": 10, "procedural": 7, "transfer": 3}
- cache entries: 20

## Cache Entries

- canonical: How is ARIMA different from exponential smoothing?
- canonical: What does ARIMA stand for, and what is it trying to model?
- canonical: When would ARIMA be a better choice than exponential smoothing?
- canonical: Why do we compare a forecasting model against benchmark methods?
- canonical: How do I know when a benchmark method is no longer enough on its own?
- canonical: Why do more recent observations get more weight in exponential smoothing?
- canonical: What is exponential smoothing?
- canonical: When is exponential smoothing a poor fit for the data?
- canonical: How do I measure forecast accuracy?
- canonical: What does forecast accuracy tell me about whether I should trust a forecasting method?
- canonical: How do I use ljung-box test to check whether a series looks random?
- canonical: What is ljung-box test?
- canonical: Why isn't repeated cycles enough on its own?
- canonical: What is repeated cycles?
- canonical: Why isn't seasonality enough on its own?
- canonical: What should I look for in a time series plot before choosing a forecasting method?
- canonical: How do I know when a time series plot is revealing something my forecasting method needs to capture?
- canonical: Why isn't trend enough on its own?
- canonical: How do I use white noise to check whether a series looks random?
- canonical: What is white noise?

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
