# Forecasting in R (`24491`)

## Visible Curated Q/A Pairs

Q: How do I know when a time series plot is revealing something my forecasting method needs to capture?  
A: A time series plot reveals features like patterns, trends, seasonality, or unusual observations. If you see these in the plot, your forecasting method should be able to capture them, as these features must be incorporated into the model for accurate forecasts.

Q: Why do we compare a forecasting model against benchmark methods?  
A: We compare a forecasting model against benchmark methods to check if the model is effectively using the available information and to measure its forecast accuracy. This helps ensure the model performs better than simple or standard approaches.

Q: How do I know when a benchmark method is no longer enough on its own?  
A: A benchmark method is no longer enough when it fails to adequately use the available information or when its forecast accuracy is not sufficient for your needs. If more advanced methods consistently outperform the benchmark, it's time to move beyond it.

Q: What does forecast accuracy tell me about whether I should trust a forecasting method?  
A: Forecast accuracy tells you how well a forecasting method predicts future values. High accuracy means the method is reliable and you can trust its forecasts; low accuracy suggests the method may not be suitable for your data.

Q: Why do more recent observations get more weight in exponential smoothing?  
A: More recent observations get more weight in exponential smoothing because the method uses exponentially decaying weights, making recent data more influential. This helps the forecast quickly adapt to recent changes in the time series.

Q: When is exponential smoothing a poor fit for the data?  
A: Exponential smoothing is a poor fit when the data has complex patterns, such as complicated seasonality or when other external factors (like holidays or competitor activity) significantly affect the series, since the method may not capture these complexities.

Q: How is ARIMA different from exponential smoothing?  
A: ARIMA is different from exponential smoothing because ARIMA models focus on describing the autocorrelations in the data, while exponential smoothing models are based on describing trend and seasonality.

Q: When would ARIMA be a better choice than exponential smoothing?  
A: ARIMA would be a better choice when your data shows strong autocorrelations that need to be modeled, rather than just trend or seasonality. It's also useful when exponential smoothing does not adequately capture the data's structure.

## Hidden But Correct

- Why is plotting a time series the first step in analysis?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What should I look for in a time series plot before choosing a forecasting method?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- How do I measure forecast accuracy?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What is exponential smoothing?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=true
- What does ARIMA stand for, and what is it trying to model?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=true
- Why does trend matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply trend to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't trend enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make trend fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt trend instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does seasonality matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply seasonality to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't seasonality enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make seasonality fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would my use of seasonality change in a different real-world context?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- What is white noise?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=true
- How do I use white noise to check whether a series looks random?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would white noise tell me about whether I should keep using my current forecasting approach?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- What is ljung-box test?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=true
- How do I use ljung-box test to check whether a series looks random?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would ljung-box test tell me about whether I should keep using my current forecasting approach?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does repeated cycles matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- What is repeated cycles?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=true
- How would I apply repeated cycles to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't repeated cycles enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make repeated cycles fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt repeated cycles instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false

## Coverage Warnings

- `definition_generation_failed` for `Benchmark methods`: Foundational anchor 'Benchmark methods' has no generated definition candidate.
- `definition_generation_failed` for `forecast accuracy`: Foundational anchor 'forecast accuracy' has no generated definition candidate.
- `only_hidden_correct_entry_exists` for `Exponential smoothing`: Foundational anchor 'Exponential smoothing' has hidden correct definition variants but no visible canonical entry.
- `only_hidden_correct_entry_exists` for `ARIMA models`: Foundational anchor 'ARIMA models' has hidden correct definition variants but no visible canonical entry.
- `definition_generation_failed` for `trend`: Foundational anchor 'trend' has no generated definition candidate.
- `definition_generation_failed` for `seasonality`: Foundational anchor 'seasonality' has no generated definition candidate.
- `definition_generation_failed` for `Advanced methods`: Foundational anchor 'Advanced methods' has no generated definition candidate.
- `definition_generation_failed` for `ARIMA`: Foundational anchor 'ARIMA' has no generated definition candidate.
- `only_hidden_correct_entry_exists` for `white noise`: Foundational anchor 'white noise' has hidden correct definition variants but no visible canonical entry.
- `only_hidden_correct_entry_exists` for `Ljung-Box test`: Foundational anchor 'Ljung-Box test' has hidden correct definition variants but no visible canonical entry.
- `only_hidden_correct_entry_exists` for `repeated cycles`: Foundational anchor 'repeated cycles' has hidden correct definition variants but no visible canonical entry.

## Policy Summary

- validated-correct count: 35
- visible curated count: 8
- hidden correct count: 27
- hard reject count: 0
- cache entries: 8

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
