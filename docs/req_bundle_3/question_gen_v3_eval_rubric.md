# Question Generation V3 Evaluation Rubric

Use this rubric to review selected questions from the V3 pipeline.

## Reviewer instructions

For each selected question, score the following dimensions from 1 to 5.

### 1) Instructional value
- **1**: not useful; mostly filler or paraphrase
- **2**: weak learner value
- **3**: somewhat useful but not especially revealing
- **4**: clearly useful for learning or diagnosis
- **5**: highly useful; exposes meaningful understanding, confusion, or transfer

### 2) Specificity
- **1**: extremely broad
- **2**: broad and loosely tied to source
- **3**: moderately specific
- **4**: clearly tied to a real subtopic or decision
- **5**: sharply targeted and discriminative

### 3) Answer richness
- **1**: answer would be tautological, vague, or mostly "not specified"
- **2**: answer would be thin
- **3**: answer would have some real content
- **4**: answer would support meaningful explanation or contrast
- **5**: answer would support rich explanation, diagnosis, or transfer

### 4) Mastery fit
- **1**: badly mismatched to claimed band
- **2**: somewhat mismatched
- **3**: acceptable fit
- **4**: good fit
- **5**: excellent fit

### 5) Groundedness
- **1**: unsupported
- **2**: weakly supported
- **3**: partly supported
- **4**: well supported
- **5**: strongly grounded in the source and extracted structure

### 6) Non-duplication
- **1**: duplicate of another selected question
- **2**: nearly redundant
- **3**: some overlap but distinct enough
- **4**: meaningfully distinct
- **5**: clearly unique and complementary

---

## Reviewer flags

In addition to scores, flag any of these if present:
- `broad_heading_paraphrase`
- `thin_answer`
- `mostly_not_specified`
- `generic_definition`
- `weak_proficient_question`
- `duplicate_intent`
- `unsupported`
- `mastery_misaligned`

---

## Aggregate metrics

Compute these after each review batch:
- average instructional value
- average specificity
- average answer richness
- average mastery fit
- average groundedness
- average non-duplication
- share of flagged thin-answer questions
- share of flagged duplicate-intent questions
- share of selected proficient questions
- share of friction-linked selected questions

## Pass/fail heuristics

A batch is promising if it shows most of the following:
- average instructional value >= 4.0
- average answer richness >= 3.8
- average groundedness >= 4.0
- thin-answer flag rate <= 10%
- duplicate-intent flag rate <= 10%
- proficient share >= configured minimum
- friction-linked selection rate >= configured minimum

---

## Suggested comparison protocol

When comparing V2 vs V3:
1. blind reviewers to which system produced each question
2. sample equal-sized batches
3. compare mean scores by dimension
4. compare flag rates
5. compare type and mastery distributions

The main outcome should be whether V3 improves **instructional utility**, not just whether it produces more questions.
