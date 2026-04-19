# Unsupervised Learning in Python (`24401`)

## Visible Curated Q/A Pairs

Q: What is clustering for dataset exploration?  
A: Clustering for dataset exploration is the process of discovering underlying groups, or 'clusters', in a dataset based on similarities in their features, such as clustering companies by stock prices or distinguishing species by their measurements.

Q: What is decorrelating your data?  
A: Decorrelating your data means using techniques like Principal Component Analysis (PCA) to summarize a dataset by removing correlations between features, making the data easier to analyze and use for clustering or modeling.

Q: What is dimension reduction?  
A: Dimension reduction is the process of summarizing a dataset using its most common patterns, often by reducing the number of features while retaining important information, such as with Principal Component Analysis (PCA).

Q: What are discovering interpretable features?  
A: Discovering interpretable features involves using techniques like Non-negative Matrix Factorization (NMF) to express data samples as combinations of understandable parts, such as topics in documents or visual patterns in images.

Q: Why isn't visualization with hierarchical clustering enough on its own?  
A: Visualization with hierarchical clustering alone isn't enough because it only shows the hierarchy of clusters, not the actual proximity of samples in a lower-dimensional space. Techniques like t-SNE are also needed to visualize how close samples are to each other.

Q: Why isn't visualization with hierarchical clustering and t-sne enough on its own?  
A: Visualization with hierarchical clustering and t-SNE helps understand data structure, but it's not enough on its own because these methods only show patterns or groupings visually; further analysis is needed to extract actionable insights or build models.

## Hidden But Correct

- Why does clustering for dataset exploration matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply clustering for dataset exploration to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- What should I compare when I use clustering for dataset exploration?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What could I misunderstand about clustering for dataset exploration if I only memorize the term?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make clustering for dataset exploration fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt clustering for dataset exploration instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does visualization with hierarchical clustering matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What is visualization with hierarchical clustering?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- How do I use visualization with hierarchical clustering in this course context?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What would make visualization with hierarchical clustering fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- When would I need to adapt visualization with hierarchical clustering instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- Why does visualization with hierarchical clustering and t-sne matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What is visualization with hierarchical clustering and t-sne?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- How do I use visualization with hierarchical clustering and t-sne in this course context?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- Why does decorrelating your data matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply decorrelating your data to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't decorrelating your data enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make decorrelating your data fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt decorrelating your data instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does dimension reduction matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply dimension reduction to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't dimension reduction enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make dimension reduction fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt dimension reduction instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does discovering interpretable features matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply discovering interpretable features to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why isn't discovering interpretable features enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=true required_entry=false
- What would make discovering interpretable features fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt discovering interpretable features instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false

## Coverage Warnings

- none

## Policy Summary

- validated-correct count: 35
- visible curated count: 6
- hidden correct count: 29
- hard reject count: 0
- cache entries: 0

## Scraped Course Description

### Summary

Learn how to cluster, transform, visualize, and extract insights from
unlabeled datasets using scikit-learn and scipy.

### Overview

Learn how to cluster, transform, visualize, and extract insights from
unlabeled datasets using scikit-learn and scipy.

Say you have a collection of customers with a variety of characteristics
such as age, location, and financial history, and you wish to discover
patterns and sort them into clusters. Or perhaps you have a set of texts,
such as Wikipedia pages, and you wish to segment them into categories based
on their content. This is the world of unsupervised learning, called as such
because you are not guiding, or supervising, the pattern discovery by some
prediction task, but instead uncovering hidden structure from unlabeled
data. Unsupervised learning encompasses a variety of techniques in machine
learning, from clustering to dimension reduction to matrix factorization. In
this course, you'll learn the fundamentals of unsupervised learning and
implement the essential algorithms using scikit-learn and SciPy. You will
learn how to cluster, transform, visualize, and extract insights from
unlabeled datasets, and end the course by building a recommender system to
recommend popular musical artists.

The videos contain live transcripts you can reveal by clicking "Show
transcript" at the bottom left of the videos.

The course glossary can be found on the right in the resources section.

To obtain CPE credits you need to complete the course and reach a score of
70% on the qualified assessment. You can navigate to the assessment by
clicking on the CPE credits callout on the right.

### Syllabus

1. Clustering for Dataset Exploration  
Learn how to discover the underlying groups (or "clusters") in a
dataset. By the end of this chapter, you'll be clustering companies
using their stock market prices, and distinguishing different
species by clustering their measurements.

2. Visualization with Hierarchical Clustering and t-SNE  
In this chapter, you'll learn about two unsupervised learning
techniques for data visualization, hierarchical clustering and
t-SNE. Hierarchical clustering merges the data samples into
ever-coarser clusters, yielding a tree visualization of the
resulting cluster hierarchy. t-SNE maps the data samples into 2d
space so that the proximity of the samples to one another can be
visualized.

3. Decorrelating Your Data and Dimension Reduction  
Dimension reduction summarizes a dataset using its common occuring
patterns. In this chapter, you'll learn about the most fundamental
of dimension reduction techniques, "Principal Component Analysis"
("PCA"). PCA is often used before supervised learning to improve
model performance and generalization. It can also be useful for
unsupervised learning. For example, you'll employ a variant of PCA
will allow you to cluster Wikipedia articles by their content!

4. Discovering Interpretable Features  
In this chapter, you'll learn about a dimension reduction technique
called "Non-negative matrix factorization" ("NMF") that expresses
samples as combinations of interpretable parts. For example, it
expresses documents as combinations of topics, and images in terms
of commonly occurring visual patterns. You'll also learn to use NMF
to build recommender systems that can find you similar articles to
read, or musical artists that match your listening history!
