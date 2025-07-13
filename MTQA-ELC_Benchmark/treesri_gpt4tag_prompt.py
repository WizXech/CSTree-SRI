PROMPT_DICT = {
    "InitRetr": (
        "You are an intelligent information retrieval assistant.\n"
        "Given an instruction, please make a judgment on whether finding some external information helps to generate a better response. Please answer [Yes] or [No] and write an explanation.\n\n"

        "##\nInstruction: Give three tips for staying healthy.\n"
        "Need retrieval?: [Yes]\n"
        "Explanation: There might be some online sources listing three tips for staying healthy or some reliable sources to explain the effects of different behaviors on health. So retrieving documents is helpful to improve the response to this query.\n\n"

        "##\nInstruction: Describe a time when you had to make a difficult decision.\n"
        "Need retrieval?: [No]\n"
        "Explanation: This instruction is asking about some personal experience and thus it does not require one to find some external documents.\n\n"

        "##\nInstruction: Write a short story in third person narration about a protagonist who has to make an important career decision.\n"
        "Need retrieval?: [No]\n"
        "Explanation: This instruction asks us to write a short story, which does not require external evidence to verify.\n\n"

        "##\nInstruction: What is the capital of France?\n"
        "Need retrieval?: [Yes]\n"
        "Explanation: While the instruction simply asks us to answer the capital of France, which is a widely known fact, retrieving web documents for this question can still help.\n\n"

        "##\n Instruction: Find the area of a circle given its radius. Radius = 4\n"
        "Need retrieval?: [No]\n"
        "Explanation: This is a math question and although we may be able to find some documents describing a formula, it is unlikely to find a document exactly mentioning the answer.\n\n"

        "##\nInstruction: Arrange the words in the given sentence to form a grammatically correct sentence. quickly the brown fox jumped\n"
        "Need retrieval?: [No]\n"
        "Explanation: This task doesn't require any external evidence, as it is a simple grammatical question.\n\n"
        
        "##\nInstruction: Explain the process of cellular respiration in plants."
        "Need retrieval?: [Yes]\n"
        "Explanation: This instruction asks for a detailed description of a scientific concept, and is highly likely that we can find a reliable and useful document to support the response.\n\n"

        "##\nInstruction:{instruction}{question}\n"
        "Need retrieval?: "
    ),
    "NodeRetr": (
        "You are an intelligent information retrieval assistant.\n"
        "You will be provided an instruction and a summary of an article. Your task is to determine whether it is necessary to retrieve the full content of the article based on the provided summary. There are three cases:\n"
        "- If the summary relate to the same article as the question, respond with [Yes]\n"
        "- If the summary suggests some similarity to the question or indicates that the article may potentially answer the question, respond with [Yes].\n"
        "- If the summary already sufficiently answers the question, respond with [Yes].\n"
        "If the information in the [Summary] is likely to be useful for any of these cases, please respond with [Yes]. Otherwise, respond with [No].\n"
        
        "##[Summary]: {retrieval_summary}\n"
        "##[Instruction]: {instruction}{question}\n"
        "[Judgment]: "
    ),
    "ExtraRetr": (
        "Based on the multiple retrieval text I found regarding this question, do you think I should continue searching for more text? "
        "If you believe the existing text is insufficient to answer the question, please respond with [Yes] otherwise respond with [No]"
        
        "##[Retrieval Text]: {retrieval_content}\n"
        "##[Question]: {question}\n"
        "Judgment: "
    ),
    
    "FitScore": (
        "Please evaluate the relevance of the provided evidence to the question from the following aspects\n"
        "1. If the evidence relate to the same article as the question, respond with [Relevant]\n"
        "2. If the evidence relate to the same topic, or theme as the question, respond with [Relevant]\n"
        "3. If the evidence provide background knowledge or context that may help in understanding the question or related concepts, respond with [Relevant]\n"
        "4.If the evidence include information could offer relevant context or serve as a contrast that helps clarify the question, respond with [Relevant]\n"
        "Please judge whether the evidence is relevant to the question in order according to my standards. If it meets the standards, please return directly to the [Relevant]. Otherwise, respond with [Irrelevant].\n"
        "I will provide you with multiple pieces of evidence and a question. Please indicate whether each piece of evidence is relevant to the question, separated by an @ sign. The output example is [Relevant] @ [Irrelevant] @ [Irrelevant]\n\n"

        "##\nInstruction: {instruction}{question}\n"
        "Evidence: {retrieval_content}\n"
        "Judgment: "
    ),
    "AidScore": (
        "You will receive an instruction, evidence, and output. Your task is to evaluate whether the output is supported by the information provided in the evidence. There are three cases:\n"
        "[3-Fully supported] - All information in output is supported by the evidence, or extractions from the evidence. This is only applicable when the output and part of the evidence are almost identical.\n"
        "[2-Partially supported] - The output is supported by the evidence to some extent, but there is some information in the output that is not discussed in the evidence. For instance, if the output covers multiple concepts and the evidence only discusses some of them, it should be considered a [Partially supported].\n"
        "[1-No support] - The output completely ignores evidence, is unrelated to the evidence, or contradicts the evidence.\n"
        "Please select from the following three options [3], [2], [1].\n"

        "##\nInstruction: {instruction}{question}\n"
        "Evidence: {retrieval_content}\n"
        "Output: {answers}\n"
        "Judgment: "
    ),
    "CorrectScore": (
        "You are a teacher.\n"
        "You will receive an instruction and an output. Your task is to evaluate the student's output based on the provided instruction.\n"
        "You should score it according to the criteria outlined below.\n"
        "Scoring Criteria:\n"
        "[1-Unrelated answer]: Serious errors, confusing, Unclear and worthless.\n"
        "[2-Partially related]: weak response, Multiple inaccuracies, misleading. Confusing, lacks logic.\n"
        "[3-Somewhat related]: partial answer, some mistakes, Moderate clarity, includes vague parts.\n"
        "[4-Relevant and mostly complete]: Generally accurate, no major errors, Clear and logical, easy to understand.\n"
        "[5-Fully relevant and comprehensive answer]: Highly accurate, rich information, Very clear, logical, and valuable.\n"
        "Additional Suggestions:\n"
        "For higher scores, it is best to include examples and explanations that help illustrate key points.\n"
        "Meanwhile, Encourage thoroughness and critical thinking in responses.\n"
        "Please select from the following five options [5], [4], [3], [2], [1].\n"

        "##\nInstruction: {instruction}{question}\n"
        "Output: {answers}\n"
        "Score: "
    )
}