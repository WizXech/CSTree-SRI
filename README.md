# CSTree-SRI

## How to evaluate on MTQA-ELC

#### 1. Load Data

You can download and load the MTQA-ELC data through the Hugging Face datasets (🤗 HF Repo): 

```python
from datasets import load_dataset
dataset = load_dataset('WizXech/MTQA-ELC', split='train')
```

Alternatively, you can download the file from [this link](https://huggingface.co/datasets/WizXech/MTQA-ELC) to load the data.

Copy the files under **ELCdataset_shuffled/*** to the **MTQA-ELC_Benchmark folder**, and then you can proceed with the subsequent evaluation.

#### 2. Evaluation

Install the requirements with pip: `pip install -r requirements.txt`.

To run model evaluation, first add your model path and its context window length to `config/`, then follow these steps (we take [Qwen2.5-7B-Instruct] for a running example):

```bash
python pred.py --model Qwen2.5-7B-Instruct --shuffled_choice shuffled
```

-   --shuffled_choice: You can choose shuffled / unshuffled dataset as your evaluation dataset

Finally, run `python eval.py` to export the evaluation results.



## How to run the CSTree-SRI framework on MTQA-ELC

In the MTQA-ELC_Benchmark folder, all files prefixed with **"treesri_*"** are CSTree-SRI framework files.

First, we need to configure the corresponding LLM in the CSTree-SRI framework.

-   Configure the AE expert model in the **"treesri_llm.py"** file.

-   Configure the IE and SE expert models in the **"treesri_openai_gpt.py"** file.

Run CSTree-SRI Evaluation:

```bash
python pred.py --model CSTree-SRI --shuffled_choice shuffled
```

Finally, run `python eval.py` to export the evaluation results.



## Content you may be interested in: Dataset Construction Process

The **Construct ELCdataset folder** contains the construction code for the entire Benchmark test data.Copy all files from **dataset/* in huggingface** to Construct ELCdataset, and then you can start the subsequent process of constructing the dataset

Copy all files from **dataset/* in huggingface** to **Construct ELCdataset folder**, and then you can start the subsequent process of constructing the dataset

Run `python create_ELC.py` to generate the ELCdataset.



