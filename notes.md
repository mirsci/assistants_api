For Shopping assistant, there is a need to define detailed measures for their main deliverables (design, agent - model, harness to assess their fit for Delta.
Evaluating fine-tuned model needs to start with functional baselining of the overall shopping orchestration (not only routing). 

Worked on model orchestration task for product discovery in the past month and elaborated in the past few days. 
My working hypothesis is that the model involves 5-6 agents:
* Parser
- parses shopping queries 
- extracts critical product slots in structured format
- identifies repeated questions for existing slots (see img6)
- identifies product intent abandonment correctly, reasons about it, drops old product slots and keeps relevant ones (offers for merchant with cashback), all within the same intent of product discovery (see img7)
* Product discovery
knows when it does not have information to make a product search
* Merchant search
* Offer search
* Product catalogue search
* Shopping assistant planner 
- outputs a plan which can be executed by another component (Shopping assistant Controller
- it is different than Controller, as it only outputs an execution plan and it does not execute it.
The benefit for this separation between plan extraction and execution is that it allows the 2 components to run in parallel, evolve designs separately, be more maintainable.
As I understand the orchestration sequence flow functionally, the above aims to cover it completely.

Proved the above flow with out-of-the-box Gemma 4 E4B and prompt engineering (screenshots attached).

Mentioning these here, as it is difficult in meetings to get these points across.
We are evolving these jointly over the next few months. It is going to take few weeks to mature this and present.
This is DoD I am focusing on, while Oumi works on their initial proposal. Expecting the equivalent DoD from them when ready.

<img width="582" height="612" alt="img1" src="https://github.com/user-attachments/assets/a4a5d712-9f1b-4b12-a5c4-1cd9efd322f9" />
<img width="552" height="577" alt="img2" src="https://github.com/user-attachments/assets/ca1981e8-e384-416a-aa8c-4ba6a1e9060f" />
<img width="533" height="558" alt="img3" src="https://github.com/user-attachments/assets/ee79d8a4-9382-4aba-b63a-6676b9667640" />
<img width="545" height="588" alt="img4" src="https://github.com/user-attachments/assets/436dd4e4-01dc-44b5-9ebd-5eab897d9560" />
<img width="536" height="601" alt="img5" src="https://github.com/user-attachments/assets/aeaca3c2-bf44-4be3-a1b3-ae6346b3ea8d" />
<img width="543" height="705" alt="img6" src="https://github.com/user-attachments/assets/31f46a93-1c85-4cc6-9aeb-54c536502826" />
<img width="555" height="648" alt="img7" src="https://github.com/user-attachments/assets/b2d89447-f6d8-431e-87c3-00ea7a36145d" />



------------------------------------------------------------
1) Design lifecycle: inference engines selection criteria considerations:
		1 — Model Format Compatibility; (GGUF / QAT-GGUF native support)
		2 — iOS Platform Integration (Device compatibility, App store compliance, Background execution support) 
		3 — Hardware Backend & Acceleration (Metal GPU acceleration, ANE access)
		4 — Memory Management (Peak RAM footprint, KV cache quantization)
		5 — KV Cache Economics (KV cache stateful persistence, session save / restore, session cloning, KV cache compression, context window management)
		6 — Token Scheduling & Inference Control (Token-level scheduling, Context window size, Time to first token (TTFT))
		7 — OpenAI-Compatible API & Transport
		8 — Resource & Power Management (Thermal state management, battery efficiency, Inference cancellation etc.)
		9 — Model Lifecycle & Distribution
	Bank has design decisioning lifecycle => Oumi's proposed designs needs to align with this process
	Same as with model lifecycle from Oumi.
	And application lifecycle.

2) **DeepEvals update**:
Focusing on DeepEvals tests, using a schema first approach for evaluation. 
Not ready to share yet, as still need to evolve it further.
Key topics for judge model, which should:
- evaluate the functional / process flow steps and their outcome. The same process flow is given to the model under test
- check the output schema validity and compliance
- validate if business rules given to model under test are reflected in the outputs. Metrics need to include the rules
Will also need to compare with Oumi's approach for model lifecycle (baselining - evals etc.).
<img width="821" height="311" alt="Screenshot 2026-07-29 174037" src="https://github.com/user-attachments/assets/e4d2c159-d009-4bd4-9789-fd8bbf3dae02" />
<img width="928" height="601" alt="Screenshot 2026-07-29 171951" src="https://github.com/user-attachments/assets/7db91526-5bf5-4c3a-b1a6-b0e53646f0e3" />
<img width="846" height="687" alt="Screenshot 2026-07-29 171244" src="https://github.com/user-attachments/assets/8b99b60a-e97a-4033-8791-583bc172dbbf" />

---------------------------------
Here I am outlining briefly, certain aspects of LLM lifecycle, with focus on data synthesis and model evals.
Note: generating training data becomes possible, after baselining. 

Key point: it is critical we master this basic methodology as a team, to develop it together with Oumi.

It all starts with data specifications for data synthesis:

A) I built spec based data synthesis in an AI-enabled way, as an extension to DeepEval model evaluation framework.
Note: Oumi has similar support for data synthesis, few details below. 

The task was product discovery. Turns out that Gemma 4 E4B is very good at it, already. 
Took 3 real product categories, with 7 real products each from Shopify product data set. 

Here are few examples using specs and recordings for product discovery task: 
1) Apparel specs, with user personas is included in "hidden facts"
   <img width="1555" height="802" alt="Boots_recording" src="https://github.com/user-attachments/assets/c469ecaf-711e-4c4d-9a22-ff85dbcebe89" />
2) Apparel recording/ transcript based on script
<img width="1455" height="812" alt="Boots_spec" src="https://github.com/user-attachments/assets/216f69f3-3c7f-436b-ac04-8458c6c14453" /> 
3) Summary of specs coverage
   <img width="740" height="782" alt="Summary_coverage" src="https://github.com/user-attachments/assets/111a687b-e3c4-42e6-a31a-aff8c676e3f5" />
5) Summary of regression results
<img width="901" height="877" alt="Regression_results" src="https://github.com/user-attachments/assets/da42faae-90f6-48fe-be6b-10aacfbd413e" />

B) Why data needs to be generated by spec, as opposed to the experimental way we have it now?

Because as the functionality evolves continuously, data synthesis (of the seed data) needs to follow, it needs to be regenerated and re-tested 100x times. 
Also, training data is derived after, based on seed data.
More so, during fine-tuning, model fine-tunning may need to run over 1000x of times with this data, over few months, as functionality, metrics, rules evolve. 

C) How does this relate with Oumi? 
Oumi also has data spec-based synthesis: 
* https://github.com/oumi-ai/oumi/blob/main/configs/examples/synthesis/conversation_synth.yaml
* https://oumi.ai/docs/en/latest/user_guides/synth.html#environment-first-tool-synthesis) 

Will continue later with details on Conversational GEval from DeepEvals and where these fit in. 

The assumption so far from working with Oumi, we need to give them data and they will produce a model.
Based on my knowledge on model lifecycle, evals and state of our functionality definition, this assumption is not realistic at all. 	
Instead we should aim for a DoD that allows tight collaborative iterations over the entire lifecycle data specs - synthesis - evals - tuning (repeat).

As such, recommend that the next step to be to start applying this lifecycle for a functionality we can prove there is a need for fine-tuning, whichever task definition we chose it to be. 
Again, we need to aim collaborative workflow with vendor, instead of expecting model for the data we give them.

P.S. I peaked at Microsoft code and it is anotehr tool, but the tool does not save us from mastering the methodology.
