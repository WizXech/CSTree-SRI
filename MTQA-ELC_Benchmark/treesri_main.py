import sys
sys.stdout = open("output.txt", "w")
# sys.stderr = open("output.txt", "w")
import os
import json
import torch
import argparse

import numpy as np

from tqdm import tqdm

from treesri_SE import SummaryModel
from treesri_rank_bm25 import BM25Okapi
from treesri_IE import IntrospectiveModel
from treesri_llm import LLM

# LLM_PROMPT_TEMPLATE = "Please answer the questions in the [Query] based solely on the [Content] provided. Do not refer to any other information. Provide the answers directly, without any introductory phrases or explanations. Only include the essential information needed. \n [Content]: {content} [Query]: {query} "
# LLM_REGENERATE_TEMPLATE = "Please only answer the questions in the [Query] based on the following [Content] and do not refer to any other information. However, I think the ##{preanswer} was incorrect. \n [Content]: {content}\n [Query]: {query}\n"
# LLM_PROMPT_TEMPLATE = "Please refer to the [Content] and follow the requirements in the [Instruction] to provide an [Answer].\n [Content]: {} [Instruction]: {} \n ##Provide the answers directly, without any introductory phrases or explanations."
# LLM_REGENERATE_TEMPLATE = "Please refer to the [Content] and follow the requirements in the [Instruction] to provide an [Answer]. However, I think the ##{} was incorrect.\n [Content]: {} [Instruction]: {} ##Provide the answers directly, without any introductory phrases or explanations."

LLM_PROMPT_TEMPLATE = "{content}\n {query}\n ### Provide the answers directly, without any introductory phrases or explanations. ### Your Answer:"
LLM_REGENERATE_TEMPLATE = "{content}\n{query}\n##This answer is wrong [{preanswer}]\n ###Don't apologize, only provide the answers directly, without any introductory phrases or explanations. "

DEFAULT_INSTRUCTION = "Answer the following question.\n"

class LITNode:
    def __init__(self, text = "", summary = "", id = -1, layer = -1, son_list = None):
        if son_list is None:
            son_list = []
        self.text = text
        self.summary = summary
        self.id = id
        self.layer = layer
        self.son_list = son_list
    def __str__(self):
        if self.id == -1:
            return "None"
        else:
            return (f"LITNode(\n"
                    f"  text: {self.text},\n"
                    f"  summary: {self.summary},\n"
                    f"  id: {self.id}, layer: {self.layer}, son_list: {self.son_list})\n")
    def __repr__(self):
        return self.__str__()
    
class LIT:
    def __init__(self, original_chunks, SE):
        self.docs_layer = []
        self.paras_layer = []
        self.texts_layer = [LITNode() for _ in range(len(original_chunks))]

        self.SE = SE
    
    def __str__(self):
        return (f"LIT(\n"
                f"  docs_layer: {self.docs_layer},\n"
                f"  paras_layer: {self.paras_layer},\n"
                f"  texts_layer: {self.texts_layer},\n"
                f")\n")
    def __repr__(self):
        return self.__str__()
    
    def add_text_fa(self, chunks, Paras = False):
        sonlist = [chunk.id for chunk in chunks]
            
        if Paras == True:
            for layer in self.docs_layer:
                is_subset = set(sonlist).issubset(set(layer.son_list))
                if is_subset: return

            # Add_edge(Docs,Paras)
            total_text = ""
            for chunk in chunks:
                total_text += chunk.text
                
            summary = self.SE.generate([total_text])
            
            fa_id = len(self.docs_layer)
            self.docs_layer.append(LITNode(text=total_text, summary=summary[0], id=fa_id, layer=0))
            for chunk in chunks:
                self.docs_layer[fa_id].son_list.append(chunk.id)
            self.docs_layer[fa_id].son_list.sort()
        else:
            for layer in self.paras_layer:
                is_subset = set(sonlist).issubset(set(layer.son_list))
                if is_subset: return
            # Add_edge(Paras, Texts)
            total_text = ""
            for chunk in chunks:
                self.texts_layer[chunk.id] = LITNode(text=chunk.text, summary=chunk.summary, id=chunk.id, layer=2)
                total_text += chunk.text
                
            summary = self.SE.generate([total_text])
            
            fa_id = len(self.paras_layer)
            self.paras_layer.append(LITNode(text=total_text, summary=summary[0], id=fa_id, layer=1))
            for chunk in chunks:
                self.paras_layer[fa_id].son_list.append(chunk.id)
            self.paras_layer[fa_id].son_list.sort()

class TreeSRI:
    def __init__(self, chunk_size, per_chunk):
        self.chunk_size = chunk_size
        self.per_chunk = per_chunk
        self.original_chunks = []

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.SE = SummaryModel()
        self.IE = IntrospectiveModel()
        self.LLM = LLM()

        self.flat_index = 0
        self.logit_chunks = {}
        self.Tree = None
        self.doc_scores = None

    def clean_cache(self):
        self.original_chunks = []
        self.flat_index = 0
        self.logit_chunks = {}
        self.Tree = None
        self.doc_scores = None
        
    def split_chunk(self, data, chunk_size):
        split_list = []
        for index in range(0, len(data), chunk_size):
            split_list.append(data[index, min(len(data), index + chunk_size)])
        return split_list
    
    def preprocess(self, ELC, flag = False):
        if flag == True:
            paragraph_all = [s.strip() for s in ELC.split("\n") if s.strip()]
        else:
            paragraph_all = [ELC]

        chunk_list = []
        for para in paragraph_all:
            para = para.replace('<', '-!-').replace('>', '-@-')
            para_ds = self.LLM.tokenizer.encode(para, add_special_tokens=True)
            chunks = [para_ds[i: min(len(para_ds), i + self.chunk_size)] for i in range(0, len(para_ds), self.chunk_size)]
            chunk_text = [self.LLM.tokenizer.decode(chunk, skip_special_tokens=True).replace('-!-', '<').replace('-@-', '>') for chunk in chunks]
            chunk_list.extend(chunk_text)

        self.original_chunks = [LITNode(text = text, id = index) for index, text in enumerate(chunk_list)]
        self.Tree = LIT(self.original_chunks, self.SE)

    def flat_search(self, flat_ELC, query, tree_chunk_id, n = 5):
        if self.flat_index == 0:
            tokenized_corpus = [doc.text.split(" ") for doc in flat_ELC]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.split(" ")
            self.doc_scores = bm25.get_scores(tokenized_query)
        
        retrieve_chunk = []
        for x in np.argsort(self.doc_scores)[::-1][self.flat_index:]:
            self.flat_index += 1
            if self.doc_scores[x] > 0 and self.original_chunks[x].id not in tree_chunk_id:
                retrieve_chunk.append(self.original_chunks[x])
                if len(retrieve_chunk) == n:
                    break
        
        return retrieve_chunk
    
    def request_LLM(self, select_chunks, query):
        retrieval_content = ""
        retrieval_summary = ""
        for r in select_chunks:
            retrieval_content += r.text
            retrieval_summary += r.summary
        prompt = LLM_PROMPT_TEMPLATE.format(content = retrieval_content, 
                                            query = query)
        pre_LLM_response = ""
        it_cnt = 0
        while True:
            LLM_response = self.LLM.generate(prompt)
            if LLM_response not in pre_LLM_response:
                pre_LLM_response += "##" + LLM_response[:20]
            #AidScore
            inputs = [{
                "instruction": "",
                "question": query,
                "retrieval_content": retrieval_content, 
                "retrieval_summary": retrieval_summary,
                "answers": LLM_response
            }]
            AidScore = self.IE.generate(task_types=["AidScore" for _ in range(len(inputs))],
                                        inputs=inputs)

            #CorrectScore
            CorrectScore = self.IE.generate(task_types=["CorrectScore" for _ in range(len(inputs))],
                                            inputs=inputs)
            it_cnt += 1
            if (int(AidScore[0]) >= 2 and int(CorrectScore[0]) >= 3) or it_cnt > 1:
                break
            
            prompt = LLM_REGENERATE_TEMPLATE.format(preanswer = pre_LLM_response, content = retrieval_content, query = query)

        return LLM_response
    
    def search_tree(self, query, build_n = 3, search_n = 5):
        if self.Tree.docs_layer == [] and self.Tree.paras_layer == []:
            return []
        
        # Control the generation quantity of docs_layer
        if self.Tree.paras_layer != [] and int(len(self.Tree.paras_layer) / 2 / build_n) > len(self.Tree.docs_layer):
            tokenized_corpus = [chunk.text.split(" ") for chunk in self.Tree.paras_layer]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.split(" ")
            doc_scores = bm25.get_scores(tokenized_query)

            top_n = np.argsort(doc_scores)[::-1][:build_n]
            logit_paras = [self.Tree.paras_layer[i] for i in top_n if doc_scores[i] > 0]
            if len(logit_paras) > 1:
                self.Tree.add_text_fa(logit_paras, Paras=True)

        # Retrieve from top to bottom, starting with document level retrieval
        fit_docs_chunk = []
        need_miss_para_chunk = []
        if self.Tree.docs_layer != []:
            inputs = []
            for r in self.Tree.docs_layer:
                inputs.append({
                    "instruction": "",
                    "question": query,
                    "retrieval_content": "", 
                    "retrieval_summary": r.summary,
                    "answers": ""
                })
            NodeRetr = self.IE.generate(task_types=["NodeRetr" for _ in range(len(inputs))],
                                        inputs=inputs)
            fit_docs_chunk = []
            for retr, chunk in zip(NodeRetr, self.Tree.docs_layer):
                if retr == "YES":
                    fit_docs_chunk.append(chunk)
                else:
                    need_miss_para_chunk += chunk.son_list

        
        fit_paras_chunk = []
        if fit_docs_chunk != []:
            inputs = []
            son_list = []
            for chunk in fit_docs_chunk:
                for id in chunk.son_list:
                    if id not in son_list:
                        son_list.append(id)
                    inputs.append({
                        "instruction": "",
                        "question": query,
                        "retrieval_content": "", 
                        "retrieval_summary": self.Tree.paras_layer[id].summary,
                        "answers": ""
                    })
            
            NodeRetr = self.IE.generate(task_types=["NodeRetr" for _ in range(len(inputs))],
                                        inputs=inputs)
            for retr, id in zip(NodeRetr, son_list):
                if retr == "YES":
                    fit_paras_chunk.append(self.Tree.paras_layer[id])
        # Search from top to bottom, paragraph level search
        elif self.Tree.paras_layer != []:
            inputs = []
            for r in self.Tree.paras_layer:
                if r.id in need_miss_para_chunk: continue

                inputs.append({
                    "instruction": "",
                    "question": query,
                    "retrieval_content": "", 
                    "retrieval_summary": r.summary,
                    "answers": ""
                })
            NodeRetr = self.IE.generate(task_types=["NodeRetr" for _ in range(len(inputs))],
                                        inputs=inputs)
            for retr, chunk in zip(NodeRetr, self.Tree.paras_layer):
                if retr == "YES":
                    fit_paras_chunk.append(chunk)

        # Search from top to bottom, sentence level search
        fit_texts_chunk = []
        if fit_paras_chunk != []:
            son_list = []
            for chunk in fit_paras_chunk:
                for id in chunk.son_list:
                    if id not in son_list:
                        son_list.append(id)

            tokenized_corpus = [self.Tree.texts_layer[id].text.split(" ") for id in son_list]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.split(" ")
            doc_scores = bm25.get_scores(tokenized_query)

            top_n = np.argsort(doc_scores)[::-1][:search_n]
            fit_texts_chunk = [self.Tree.texts_layer[son_list[i]] for i in top_n if doc_scores[i] > 0]
       
        return fit_texts_chunk

    def newiteration(self, query, tree_chunk_id):

        flat_chunk = self.flat_search(self.original_chunks, query = query, tree_chunk_id = tree_chunk_id)
        retrieve_chunk = flat_chunk

        if retrieve_chunk == []:
            return flat_chunk == []
        #FitScore
        inputs = []
        for r in retrieve_chunk:
            inputs.append({
                "instruction": "",
                "question": query,
                "retrieval_content": r.text, 
                "retrieval_summary": "",
                "answers": ""
            })
        FitScore = self.IE.generate(task_types=["FitScore" for _ in range(len(inputs))],
                                    inputs=inputs)
        fit_chunk_list = []
        for score, chunk in zip(FitScore, retrieve_chunk):
            if score == "1":
                fit_chunk_list.append(chunk)
                self.logit_chunks[chunk.id] = chunk

        return flat_chunk == []

    def build_Tree(self, select_chunks):
        if len(select_chunks) <= 1: return
        chunk_list = [chunk for chunk in select_chunks.values()]

        for id in select_chunks.keys():
            if self.Tree.texts_layer[id].id == -1:
                self.Tree.add_text_fa(chunk_list)
                break
        
    def inference(self, query):
        if self.original_chunks != []:
            InitRetr = self.IE.generate(task_types=["InitRetr"], 
                                        inputs=[{
                                            "instruction": "",
                                            "question": query,
                                            "retrieval_content": "", 
                                            "retrieval_summary": "",
                                            "answers": "",
                                            }])
            self.doc_scores = None
            self.flat_index = 0
            self.logit_chunks = {}
            iter_cnt = 0
            if InitRetr[0] == "YES":
                tree_chunk = self.search_tree(query)
                
                ExtraRetr = "YES"
                if tree_chunk != []:
                    retrieval_content = ""
                    for index, chunk in enumerate(tree_chunk):
                        retrieval_content += "[Text {}]: {}".format(index + 1, chunk.text)
                    ExtraRetr = self.IE.generate(task_types=["ExtraRetr"],
                                                inputs=[{
                                                    "instruction": "",
                                                    "question": query,
                                                    "retrieval_content": retrieval_content, 
                                                    "retrieval_summary": "",
                                                    "answers": "",
                                                }])
                
                tree_chunk_id = [chunk.id for chunk in tree_chunk]
                if len(tree_chunk) < self.per_chunk and ExtraRetr == "YES":
                    while True:
                        iter_cnt += 1
                        no_more_chunk_flag = self.newiteration(query, tree_chunk_id)

                        if no_more_chunk_flag == True or len(tree_chunk) + len(self.logit_chunks) >= self.per_chunk or iter_cnt > 5:
                            break
                
                if self.logit_chunks != []:
                    for chunk in tree_chunk:
                        self.logit_chunks[chunk.id] = chunk
                    self.build_Tree(self.logit_chunks)
                
                select_chunks = [chunk for chunk in self.logit_chunks.values()]
                select_chunks = select_chunks[0:self.per_chunk - 1]
                
                LLM_response = self.request_LLM(select_chunks=select_chunks, query=query)
                return LLM_response
        result = self.LLM.generate(query)
        return result