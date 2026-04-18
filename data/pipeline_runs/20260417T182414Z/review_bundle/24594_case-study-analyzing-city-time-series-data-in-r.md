# Case Study: Analyzing City Time Series Data in R (`24594`)

## Selected Q/A Pairs

Q: How would my use of xts change with a different time series dataset?  
A: Your use of xts would adapt to the structure and requirements of the new dataset, but the core time series manipulation skills remain the same. You would still use xts for organizing and analyzing time-indexed data, regardless of the dataset's subject.

Q: Why would it be a mistake to analyze the weather data before merging the relevant xts objects?  
A: Analyzing the weather data before merging the relevant xts objects would be a mistake because you might miss important information or relationships that only become clear when the data is combined and complete.

Q: How would this merging step change with a different time series dataset?  
A: The merging step would change based on the structure and time alignment of the new dataset, but the need to merge multiple xts objects before analysis would remain if the data comes from different sources or covers different variables.

Q: What could go wrong if I analyze the full time range when I really need a specific period?  
A: If you analyze the full time range instead of the specific period you need, your results could be misleading or irrelevant because they might include data outside the scope of your analysis.

Q: How would I decide which period to isolate in a new dataset?  
A: You would decide which period to isolate in a new dataset based on the specific analysis goals or the time frame relevant to your question.

Q: When would I reach for xts while working with these time series datasets?  
A: You would use xts when you need to manipulate or analyze data that is organized by time, such as flight arrivals, weather, economic, or sports data.

Q: How do I know when I need to merge multiple xts objects before analysis?  
A: You need to merge multiple xts objects before analysis when your data comes from different sources or covers different variables that need to be analyzed together.

Q: Why would I isolate a specific period before analyzing time series data?  
A: You isolate a specific period before analyzing time series data to focus your analysis on the time frame that is relevant to your question or objective.

## Scraped Course Description

### Summary

Strengthen your knowledge of the topics covered in Manipulating Time Series
in R using real case study data.

### Overview

Flight Data

You've been hired to understand the travel needs of tourists visiting the
Boston area. As your first assignment on the job, you'll practice the skills
you've learned for time series data manipulation in R by exploring data on
flights arriving at Boston's Logan International Airport (BOS) using xts &
zoo.

Weather Data

In this chapter, you'll expand your time series data library to include
weather data in the Boston area. Before you can conduct any analysis, you'll
need to do some data manipulation, including merging multiple xts objects
and isolating certain periods of the data. It's a great opportunity for more
practice!

Economic Data

Now it's time to go further afield. In addition to flight delays, your
client is interested in how Boston's tourism industry is affected by
economic trends. You'll need to manipulate some time series data on economic
indicators, including GDP per capita and unemployment in the United States
in general and Massachusetts (MA) in particular.

Sports Data

Having exhausted other options, your client now believes Boston's tourism
industry must be related to the success of local sports teams. In your final
task on this project, your supervisor has asked you to assemble some time
series data on Boston's sports teams over the past few years.

### Syllabus

1. Flight Data  
You've been hired to understand the travel needs of tourists
visiting the Boston area. As your first assignment on the job,
you'll practice the skills you've learned for time series data
manipulation in R by exploring data on flights arriving at Boston's
Logan International Airport (BOS) using xts & zoo.

2. Weather Data  
In this chapter, you'll expand your time series data library to
include weather data in the Boston area. Before you can conduct any
analysis, you'll need to do some data manipulation, including
merging multiple xts objects and isolating certain periods of the
data. It's a great opportunity for more practice!

3. Economic Data  
Now it's time to go further afield. In addition to flight delays,
your client is interested in how Boston's tourism industry is
affected by economic trends. You'll need to manipulate some time
series data on economic indicators, including GDP per capita and
unemployment in the United States in general and Massachusetts (MA)
in particular.

4. Sports Data  
Having exhausted other options, your client now believes Boston's
tourism industry must be related to the success of local sports
teams. In your final task on this project, your supervisor has asked
you to assemble some time series data on Boston's sports teams over
the past few years.
