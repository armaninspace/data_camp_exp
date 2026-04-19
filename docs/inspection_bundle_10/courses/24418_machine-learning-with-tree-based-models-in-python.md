# Machine Learning with Tree-Based Models in Python (`24418`)

## Visible Curated Q/A Pairs

Q: What should I compare when I use bagging and random forests?  
A: You should compare the performance of bagging and random forests to single trees and other models, and assess how the added randomization in random forests affects results.

Q: What could I misunderstand about bagging and random forests if I only memorize the term?  
A: If you only memorize the terms, you might misunderstand that bagging and random forests are single models rather than ensembles, or overlook the importance of using different data subsets and randomization.

Q: What are bagging and random forests?  
A: Bagging is an ensemble method where the same algorithm is trained multiple times on different subsets of the data. Random forests are a type of bagging that adds randomization at each tree split to increase diversity.

Q: How would I know when bagging and random forests is not enough or not the right choice?  
A: You would know bagging and random forests are not enough or not the right choice if they still overfit or underfit, or if the problem requires more interpretability or a different modeling approach.

Q: What is boosting?  
A: Boosting is an ensemble method where several models are trained sequentially, with each model learning from the errors of the previous ones.

Q: What are classification and regression trees?  
A: Classification and regression trees (CART) are supervised learning models that use a tree structure for solving classification and regression problems.

Q: What is model tuning?  
A: Model tuning is the process of setting the hyperparameters of a machine learning model, which are not learned from data, to optimize performance, often using methods like grid search cross validation.

Q: What should I compare when I use random forests?  
A: When using random forests, you should compare the performance of the ensemble to individual trees and other models, and consider how randomization at each split affects diversity and accuracy.

Q: What could I misunderstand about random forests if I only memorize the term?  
A: If you only memorize the term, you might misunderstand that random forests are just a single tree or that they don't involve randomization and ensemble methods to improve performance.

Q: What are random forests?  
A: Random forests are an ensemble method that builds multiple decision trees using different subsets of the data and introduces randomization at each split to increase diversity among the trees.

Q: How would I know when random forests is not enough or not the right choice?  
A: You would know random forests are not enough or not the right choice if the model still overfits or underfits, or if the problem requires interpretability or handles data types that random forests are not suited for.

Q: What are regression trees?  
A: Regression trees are supervised learning models that use a tree structure to predict continuous values for regression problems.

Q: What is the bias-variance tradeoff?  
A: The bias-variance tradeoff is a fundamental concept in supervised machine learning that involves balancing the problems of overfitting (high variance) and underfitting (high bias) to achieve robust predictions.

## Hidden But Correct

- Why does regression trees matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply regression trees to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't regression trees enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make regression trees fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt regression trees instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does classification and regression trees matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply classification and regression trees to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't classification and regression trees enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make classification and regression trees fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt classification and regression trees instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does the bias-variance tradeoff matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How do I use the bias-variance tradeoff in this course context?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- What could I misunderstand about the bias-variance tradeoff if I only memorize the term?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would the bias-variance tradeoff tell me about whether my approach is working?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- When would I need to adapt the bias-variance tradeoff instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does random forests matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply random forests to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt random forests instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does bagging and random forests matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply bagging and random forests to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt bagging and random forests instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does boosting matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply boosting to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't boosting enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make boosting fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt boosting instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does model tuning matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply model tuning to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't model tuning enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make model tuning fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false

## Coverage Warnings

- none

## Policy Summary

- validated-correct count: 43
- visible curated count: 13
- hidden correct count: 30
- hard reject count: 0
- cache entries: 0

## Scraped Course Description

### Summary

In this course, you'll learn how to use tree-based models and ensembles for
regression and classification using scikit-learn.

### Overview

In this course, you'll learn how to use tree-based models and ensembles for
regression and classification using scikit-learn.

Decision trees are supervised learning models used for problems involving
classification and regression. Tree models present a high flexibility that
comes at a price: on one hand, trees are able to capture complex non-linear
relationships; on the other hand, they are prone to memorizing the noise
present in a dataset. By aggregating the predictions of trees that are
trained differently, ensemble methods take advantage of the flexibility of
trees while reducing their tendency to memorize noise. Ensemble methods are
used across a variety of fields and have a proven track record of winning
many machine learning competitions.

In this course, you'll learn how to use Python to train decision trees and
tree-based models with the user-friendly scikit-learn machine learning
library. You'll understand the advantages and shortcomings of trees and
demonstrate how ensembling can alleviate these shortcomings, all while
practicing on real-world datasets. Finally, you'll also understand how to
tune the most influential hyperparameters in order to get the most out of
your models.

### Syllabus

1. Classification and Regression Trees  
Classification and Regression Trees (CART) are a set of supervised
learning models used for problems involving classification and
regression. In this chapter, you'll be introduced to the CART
algorithm.

2. The Bias-Variance Tradeoff  
The bias-variance tradeoff is one of the fundamental concepts in
supervised machine learning. In this chapter, you'll understand how
to diagnose the problems of overfitting and underfitting. You'll
also be introduced to the concept of ensembling where the
predictions of several models are aggregated to produce predictions
that are more robust.

3. Bagging and Random Forests  
Bagging is an ensemble method involving training the same algorithm
many times using different subsets sampled from the training data.
In this chapter, you'll understand how bagging can be used to create
a tree ensemble. You'll also learn how the random forests algorithm
can lead to further ensemble diversity through randomization at the
level of each split in the trees forming the ensemble.

4. Boosting  
Boosting refers to an ensemble method in which several models are
trained sequentially with each model learning from the errors of its
predecessors. In this chapter, you'll be introduced to the two
boosting methods of AdaBoost and Gradient Boosting.

5. Model Tuning  
The hyperparameters of a machine learning model are parameters that
are not learned from data. They should be set prior to fitting the
model to the training set. In this chapter, you'll learn how to tune
the hyperparameters of a tree-based model using grid search cross
validation.
