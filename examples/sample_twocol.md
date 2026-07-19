expanded toolkit is 5.6 compared to the 2.7 (seemingly unrelated) tools in the original BFCL dataset, meaning that three semantically-related functions were added on average to each one of the 200 testcases. Next, we evaluate the FC performance of multiple agents using the generated benchmark.

3 Agentic FC Robustness Evaluation

3.1 Experimental Setup

Models We evaluate several top-performing LLMs from the BFCL leaderboard, both API- accessible and locally hosted, as FC agents. Closed models include GPT4o-mini and o1-mini,4 as well as Claude-3.5-Haiku and Claude-3.5-Sonnet.5 Locally hosted models include Llama3.1-70B and its more advanced version Llama3.3-70B (Dubey et al., 2024), Granite3.1-8B-instruct (Granite Team, 2024), DeepSeek-v2.5 (DeepSeek-AI, 2024), and Qwen2.5-72B (Qwen Team, 2024).

Evaluation Approach BFCL employ a twophase FC evaluation approach: (1) assessment of the generated tool call through the tree-matching abstract syntax tree (AST) methodology, and (2) evaluation of the tool execution in a simulated environment (Patil et al., 2023). Our focus in this study is the evaluation of FC construction provided interventions in its input; we, therefore, adhere to the first evaluation phase – namely, AST. A robust agent will generate correct function call regardless of the precise request wording and of its toolkit size: "thin" (as it comes with the original benchmark), or expanded, simulating a shortlister selection.

3.2 Experimental Results

We report AST averaged over the 200 dataset ex-

amples, including three variants: (a) the original version, (b) original ("thin") toolkit + rephrased user request, (c) expanded toolkit + original user request. Table 2 (left) reports the results. Several insights can be drawn from the figures:

FC Evaluation Approach Weakness(es) A notable (and somewhat unexpected) drop occurs when evaluating the original toolkit on a rephrased request. Closer examination of errors reveals a significant weakness in the common approach to FC evaluation – specifically, in handling arguments that can accept several equivalently valid values (e.g., named entities). Consider the request: "What

4https://platform.openai.com/docs/models 5https://www.anthropic.com/claude

is the humidity level in Miami,Florida in the upcoming 7 days?". The expected response includes the function weather.humidity_forecast() and validates its location parameter by exact match to one of the predefined values: ["Miami", "Miami, Florida", "FL"]. When the request is rephrased as "How will the humidity levels change over the next seven days in Miami,FL?", agents assign the value "Miami, FL" to location, which does not match any of the (incompletely) listed options.

Further systematic analysis of error types distribution reveals that 70–90% of errors indeed stem from mis-match in parameter value assignment. We conclude that the majority of failures in this

case can be attributed to the evaluation approach drawback rather than agents’ sensitivity.

We argue that this issue could potentially be mitigated by applying semantic similarity instead of exact match. Indeed, recent studies adopt a more holistic approach to evaluation of a constructed function call; e.g., Zhong et al. (2025) who use multi-dimensional matching strategy, including FCs’ embeddings similarity and LLM-as-a-Judge matching, ensuring a generated tool call meets its semantic requirements. We leave the exploration of this mitigation strategy in the context of BFCL evaluation framework to future work.

Agents’ Sensitivity to Toolkit Expansion Evidently, expanding an agent’s toolkit with a set of related functions caused performance degradation across the board (Table 2, left). Here, objective agent failures span a range of error types: wrong function selected, wrong number of functions generated (typically two instead of one), wrong parameter assignment to a correctlyselected function, parameter hallucinations, etc. As an example, in response to the request "What is the ranking of Manchester United in Premier League?", an agent with the expanded toolkit produces football_league.ranking("premier league"), retrieving the complete ranking table of the league, instead of the more appropriate sports_ranking("Manchester United", "premier league"), answering the query.

Table 2 (right) presents error breakdown for agents in this study in the expanded toolkit scenario, showing the proportion of each error type within the set of failures stemming from toolkit expansion. While no clear pattern dominates, it is evident that agents struggle with both accurate function selection and parameter assignment.

model (agent) original orig. toolkit

exp. toolkit

reph. query

orig. query

assignment Llama3.1-70B 0.965 0.825 (-15%) 0.925 (-4%) 0.00 0.45 0.10 0.45 Llama3.3-70B 0.945 0.785 (-17%) 0.905 (-4%) 0.00 0.23 0.46 0.31 DeepSeek-V2.5 0.965 0.835 (-14%) 0.950 (-2%) 0.00 0.56 0.00 0.44 Qwen2.5-72B 0.975 0.850 (-13%) 0.965 (-1%) 0.00 0.29 0.00 0.71 Granite3.1-8B-instruct 0.945 0.770 (-19%) 0.870 (-8%) 0.09 0.50 0.18 0.23 Claude-3.5-Haiku 0.925 0.765 (-11%) 0.870 (-2%) 0.00 0.44 0.00 0.56 Claude-3.5-Sonnet 0.915 0.845 ( -8%) 0.890 (-3%) 0.00 0.29 0.00 0.71 gpt4o-mini 0.925 0.765 (-17%) 0.870 (-6%) 0.26 0.42 0.00 0.32 o1-mini 0.905 0.770 (-15%) 0.885 (-2%) 0.33 0.27 0.00 0.43

Table 2: Agentic FC robustness evaluation results. Models’ AST performance drop is evident when rephrasing the original query, and also when using the original query with extended toolokit (left); relative percent drop is specified in brackets. Failures stemming from toolkit expansion vary mostly between wrong function selection and wrong parameter assignment (right). The best result in a column (the lowest performance drop) is boldfaced.

Finally, expanding an agent’s toolkit with additional functions occasionally caused models to "repair" some of their original (baseline) failures in a few cases. Interestingly, this observations highlights the stochastic, generative nature of LLM agents, where seemingly unrelated changes to a model context may entail different output.

4 Conclusions and Future Work

We focus on two aspect of robustness, capturing

input variations that can be expected in real-world agentic deployments: (1) meaning-preserving rephrasings of user requests and (2) agent’s toolkit expansion to include a set of semantically related tools that are likely to be shortlisted by a selection module. We build a benchmark dataset, evaluate the robustness of several SOTA LLM agents, and discuss the breakdown of failures.

Our future work includes testing the robustness of agentic FC with additional and diverse datasets. Moreover, it has been shown that LLMs can be easily distracted by larger context (Shi et al., 2023; Levy et al., 2024). We plan to extend the set of experiments to scenarios were agent’s toolkit is expanded also with non-relevant tools, to compare the performance against the current setting.

5 Limitations

While our study provides valuable insights into

measuring agents’ robustness in the function calling scenario, it has several limitations. First, we evaluate our approach on a single dataset, sufficient for the focused contribution of a short paper, but requiring extension to additional datasets for a broader analysis. Second, our toolkit ex-

robustness evaluation exp. toolkit + orig. query: error analysis (%)

wrong syntax

wrong function

wrong num of functions

wrong param.

pansion scenario relies on multiple LLMs to generate related requests and corresponding tools, a time-consuming process currently performed offline. We are actively exploring ways to streamline this pipeline for improved efficiency and usability.

6 Ethical Considerations

We use publicly available datasets to study the ro-

bustness of agentic function calling. We did not make use of AI-assisted technologies while writing this paper. We also did not hire human annotators at any stage of the research.

Acknowledgements

We are deeply grateful to Michal Jacovi for her

invaluable assistance in carrying out this study. We would like to thank Guy Uziel for his feedback on earlier versions of this paper. Finally, we are thankful to our anonymous reviewers for their useful comments and constructive feedback.

References

Mahyar Abbasian, Iman Azimi, Amir M Rahmani, and

Ramesh Jain. 2023. Conversational health agents: A personalized llm-powered agent framework. arXiv preprint arXiv:2310.02374.

Samuel Ackerman, Ella Rabinovich, Eitan Farchi, and

Ateret Anaby Tavor. 2024. A novel metric for measuring the robustness of large language models in non-adversarial scenarios. In Findings of the Association for Computational Linguistics: EMNLP 2024, pages 2794–2802, Miami, Florida, USA. Association for Computational Linguistics.

Jinze Bai, Shuai Bai, Yunfei Chu, Zeyu Cui, Kai Dang,

Xiaodong Deng, Yang Fan, Wenbin Ge, Yu Han, Fei