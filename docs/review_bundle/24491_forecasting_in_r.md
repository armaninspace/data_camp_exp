# Forecasting in R (`24491`)

## Q/A Pairs

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

## Scraped Course Description

### Summary

Learn how to make predictions about the future using time series forecasting in R including ARIMA models and exponential smoothing methods.

### Overview

Learn how to make predictions about the future using time series forecasting in R including ARIMA models and exponential smoothing methods.

Use Forecasting in R for Data-Driven Decision Making

This course provides an introduction to time series forecasting using R.

Forecasting involves making predictions about the future. It is required in many situations, such as deciding whether to build another power generation plant in the next ten years or scheduling staff in a call center next week.

Forecasts may be needed several years in advance (for the case of capital investments), or only a few minutes beforehand (for telecommunication routing). Whatever the circumstances or time horizons involved, reliable forecasting is essential to good data-driven decision-making.

Build Accurate Forecast Models with ARIMA and Exponential Smoothing

You’ll start this course by creating time series objects in R to plot your data and discover trends, seasonality, and repeated cycles. You’ll be introduced to the concept of white noise and look at how you can conduct a Ljung-Box test to confirm randomness before moving on to the next chapter, which details benchmarking methods and forecast accuracy.

Being able to test and measure your forecast accuracy is essential for developing usable models. This course reviews a variety of methods before diving into exponential smoothing and ARIMA models, which are two of the most widely-used approaches to time series forecasting.

Before you complete the course, you’ll learn how to use advanced ARIMA models to include additional information in them, such as holidays and competitor activity.

### Syllabus

1. Exploring and visualizing time series in R  
   The first thing to do in any data analysis task is to plot the data. Graphs enable many features of the data to be visualized, including patterns, unusual observations, and changes over time. The features that are seen in plots of the data must then be incorporated, as far as possible, into the forecasting methods to be used.

2. Benchmark methods and forecast accuracy  
   In this chapter, you will learn general tools that are useful for many different forecasting situations. It will describe some methods for benchmark forecasting, methods for checking whether a forecasting method has adequately utilized the available information, and methods for measuring forecast accuracy. Each of the tools discussed in this chapter will be used repeatedly in subsequent chapters as you develop and explore a range of forecasting methods.

3. Exponential smoothing  
   Forecasts produced using exponential smoothing methods are weighted averages of past observations, with the weights decaying exponentially as the observations get older. In other words, the more recent the observation, the higher the associated weight. This framework generates reliable forecasts quickly and for a wide range of time series, which is a great advantage and of major importance to applications in business.

4. Forecasting with ARIMA models  
   ARIMA models provide another approach to time series forecasting. Exponential smoothing and ARIMA models are the two most widely-used approaches to time series forecasting, and provide complementary approaches to the problem. While exponential smoothing models are based on a description of the trend and seasonality in the data, ARIMA models aim to describe the autocorrelations in the data.

5. Advanced methods  
   The time series models in the previous chapters work well for many time series, but they are often not good for weekly or hourly data, and they do not allow for the inclusion of other information such as the effects of holidays, competitor activity, changes in the law, etc. In this chapter, you will look at some methods that handle more complicated seasonality, and you consider how to extend ARIMA models in order to allow other information to be included in them.
