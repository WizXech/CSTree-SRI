DEAFAULT_DATASET_PROMPT = {
    "ALL": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
Information: {ELC}\n\n {queries}\n\n \
### Provide the answers directly, without any introductory phrases or explanations. \
### Your Answer: ",
    "Detail Comprehension": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions are about understanding the details of paragraphs. \
Information: {ELC}\n\n {queries}\n\n \
### Provide the answers directly, without any introductory phrases or explanations. \
### Your Answer: ",
    "Inference & Judgment": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions require you to pay attention to the logical relationship of the information in the paragraph, testing your reasoning ability. \
Information: {ELC}\n\n {queries}\n\n \
### Provide the answers directly, without any introductory phrases or explanations. \
### Your Answer: ",
    "Main Idea & Perspective": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions require you to grasp the main idea of the entire article. \
Information: {ELC}\n\n {queries}\n\n \
### Provide the answers directly, without any introductory phrases or explanations. \
### Your Answer: ",
    "Semantic & Reference": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions require you to understand the meaning of phrases, sentences, or demonstrative pronouns, testing your comprehension of the entire article. \
Information: {ELC}\n\n {queries}\n\n \
### Provide the answers directly, without any introductory phrases or explanations. \
### Your Answer: ",
}

TREESRI_DATASET_PROMPT = {
    "ALL": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
{queries}\n\n \
### Answer: ",
    "Detail Comprehension": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions are about understanding the details of paragraphs. \
{queries}\n\n \
### Answer: ",
    "Inference & Judgment": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions require you to pay attention to the logical relationship of the information in the paragraph, testing your reasoning ability. \
{queries}\n\n \
### Answer: ",
    "Main Idea & Perspective": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions require you to grasp the main idea of the entire article. \
{queries}\n\n \
### Answer: ",
    "Semantic & Reference": "Please answer the following questions based on the following information. \
The content within the angle brackets <> represents paragraph IDs from various articles. These IDs are used to identify specific sections of text within different articles. \
The following questions require you to understand the meaning of phrases, sentences, or demonstrative pronouns, testing your comprehension of the entire article. \
{queries}\n\n \
### Answer: ",
}