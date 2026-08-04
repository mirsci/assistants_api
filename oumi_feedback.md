## Questions
The Evals reports are baselining with Gemma OTB, plus prompt engineering or after fine-tuning? 
Is the 97% accuracy score means it works with these tests OTB?
How to decision about necessity of fine-tuning? 
Let us define the overall decision criteria which is always evaluating if we need to fine-tune or not. 
What does it mean "trajectories to filter, not a harness artifact"?
What does trajectory means in this context of evaluation results?
Does this baseline measure handling of emergent intent? Or intent abandonment?
How did the model decide to say "we do not have"? How does the eval benchmark define the correctness of this answer; how to measure correctness of semantic inferences between answers?
<img width="1375" height="667" alt="image" src="https://github.com/user-attachments/assets/00d4be88-0b3c-470b-b408-079f833b866d" />

Product reviews will not be provided by merchant.
<img width="1392" height="767" alt="image" src="https://github.com/user-attachments/assets/3a1a710e-9632-4d37-87ab-be46eab138a7" />

Give examples and point to places in the evals suite where this applies: 
		"Grade the agent's process across the whole conversation: did it use its tools before recommending, honour the stated constraints (budget, deadline, quantity, size/compatibility), ask vs assume when under-specified, cover and organize every part of a multi-part ask"?
		If recommending at every turn, then how it is the eval working at multi-turn / part?
		When it measures across steps? 
Rubric comments: 
		These are more like DeepEval instructions steps, then actual metrics or rubrics
		Overall rules are monolithical, every time we see "and", "or", seems that it is room to better organize and reduce complexity, both for human sake and for guiding the model for what matters more.
		Overall rubrics are … simple
		
		1. This is like asking the model to not exercise any vertical intelligence it might have, that could help answer user's question  (no accrue prod disc knowledge)
		4. How is this exactly measured?
		5.  How is this exactly measured?



