# SQL for Joining Data (`24376`)

## Visible Curated Q/A Pairs

Q: What should I compare when I use cross joins?  
A: When using cross joins, you should compare the number of rows produced (which is the product of the row counts of both tables) and whether you actually need every possible combination of rows from both tables.

Q: What are cross joins?  
A: Cross joins are SQL joins that return the Cartesian product of two tables, meaning every row from the first table is combined with every row from the second table, regardless of any matching condition.

Q: What should I compare when I use outer joins?  
A: When using outer joins, you should compare which records exist in one table but not in the other, and how unmatched rows are handled. Outer joins help you see both matched and unmatched data between tables.

Q: What could I misunderstand about outer joins if I only memorize the term?  
A: If you only memorize the term 'outer join,' you might misunderstand that it always returns all data from both tables, or not realize that unmatched rows from one side will have NULLs for the other table's columns.

Q: What are outer joins?  
A: Outer joins are SQL joins that return all records from one table and the matched records from another table. If there is no match, the result will contain NULLs for columns from the table without a match. Types include left, right, and full outer joins.

Q: How would I know when outer joins is not enough or not the right choice?  
A: You would know outer joins are not enough or not the right choice if you need only matched records (use inner join), or if you need to combine tables without matching rows (use cross join), or if set operations like union or intersect better fit your analysis.

## Hidden But Correct

- Why does introduction to joins matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What are introduction to joins?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- How would I apply introduction to joins to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What should I compare when I use introduction to joins?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- What could I misunderstand about introduction to joins if I only memorize the term?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- What would make introduction to joins fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- When would I need to adapt introduction to joins instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- Why does outer joins matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply outer joins to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- When would I need to adapt outer joins instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does cross joins matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- How would I apply cross joins to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=true required_entry=false
- Why does set theory clauses matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What are set theory clauses?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- How would I apply set theory clauses to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- Why isn't set theory clauses enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- What would make set theory clauses fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- When would I need to adapt set theory clauses instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- Why does subqueries matter in this course?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- What are subqueries?
  delivery_class: analysis_only; reasons: ["analysis_only_low_pedagogical_value"]
  anchor=false required_entry=false
- How would I apply subqueries to the kind of data used here?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- Why isn't subqueries enough on its own?
  delivery_class: analysis_only; reasons: ["analysis_only_low_distinctiveness"]
  anchor=false required_entry=false
- What would make subqueries fail in a realistic case?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false
- When would I need to adapt subqueries instead of applying it the same way every time?
  delivery_class: analysis_only; reasons: ["analysis_only_low_serviceability"]
  anchor=false required_entry=false

## Coverage Warnings

- `WARN` for `Introduction to joins` (`comparison_axis`): visible=0, required_entry_visible=false
- `WARN` for `Set theory clauses` (`concept`): visible=0, required_entry_visible=false
- `WARN` for `Subqueries` (`concept`): visible=0, required_entry_visible=false

## Policy Summary

- validated-correct count: 30
- visible curated count: 6
- hidden correct count: 24
- hard reject count: 0
- cache entries: 0

## Scraped Course Description

### Summary

Join two or three tables together into one, combine tables using set theory,
and work with subqueries in PostgreSQL.

### Overview

Introduction to joins

-In this chapter, you'll be introduced to the concept of joining tables, and
will explore the different ways you can enrich your queries using inner
joins and self joins. You'll also see how to use the case statement to split
up a field into different categories.

Outer joins and cross joins

-In this chapter, you'll come to grips with different kinds of outer joins.
You'll learn how to gain further insights into your data through left joins,
right joins, and full joins. In addition to outer joins, you'll also work
with cross joins.

Set theory clauses

-In this chapter, you'll learn more about set theory using Venn diagrams and
get an introduction to union, union all, intersect, and except clauses.
You'll finish by investigating semi joins and anti joins, which provide a
nice introduction to subqueries.

Subqueries

-In this closing chapter, you'll learn how to use nested queries and you'll
use what you’ve learned in this course to solve three challenge problems.

### Syllabus

1. Introduction to joins  
-In this chapter, you'll be introduced to the concept of joining tables, and will explore the different ways you can enrich your queries using inner joins and self joins. You'll also see how to use the case statement to split up a field into different categories.

2. Outer joins and cross joins  
-In this chapter, you'll come to grips with different kinds of outer joins. You'll learn how to gain further insights into your data through left joins, right joins, and full joins. In addition to outer joins, you'll also work with cross joins.

3. Set theory clauses  
-In this chapter, you'll learn more about set theory using Venn diagrams and get an introduction to union, union all, intersect, and except clauses. You'll finish by investigating semi joins and anti joins, which provide a nice introduction to subqueries.

4. Subqueries  
-In this closing chapter, you'll learn how to use nested queries and you'll use what you’ve learned in this course to solve three challenge problems.
