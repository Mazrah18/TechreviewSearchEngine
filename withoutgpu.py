# -*- coding: utf-8 -*-
"""withoutgpu.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kzkPvxIdd3RjLEc4FZxjQKSX8-f4lTIX
"""

!pip3 install transformers
!pip3 install faiss-cpu
!pip3 install -U scikit-learn scipy matplotlib

from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-distilroberta-v1')
model = AutoModel.from_pretrained('sentence-transformers/all-distilroberta-v1')

import pandas as pd
df = pd.read_csv('testing.csv')
df = df.dropna()
import csv
# Open the CSV file
with open('testing.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Loop over each row in the CSV file
    for row in reader:
        # Extract the review text
        review = row['review']

        # Split the review text into words
        words = review.split()

        # Join the first 400 words into a new string
        new_review = ' '.join(words[:400])

        # Trim the new string to the last complete sentence
        if len(words) > 400:
            last_period_index = new_review.rfind('.')
            if last_period_index != -1:
                new_review = new_review[:last_period_index+1]

        # Update the row with the truncated review text
        row['review'] = new_review



df['review'] = df['review'].astype(str)
review_section = df['review']

# Remove meaningless semicolons and periods
preprocessed_reviews = []
for review in review_section:
    review = review.replace(';', '') # remove semicolons
    review = review.replace('. ', '.@@@') # temporarily replace valid periods with a unique delimiter
    review = review.replace('.', '') # remove any remaining periods
    review = review.replace('@@@', '. ') # replace the unique delimiter with valid periods
    preprocessed_reviews.append(review)


# split the preprocessed reviews into sentences and store them in a list
# sentences = []
# for review in preprocessed_reviews:
#     sentences += review.split('. ')

sentences= preprocessed_reviews
# # remove any empty sentences from the list
# sentences = [s.strip() for s in sentences if s.strip()]

len(sentences)

# tokens={'input_ids' : [], 'attention_mask': []}
# for sentence in sentences:
#   new_tokens = tokenizer.encode_plus(sentence,max_length=512,truncation=True, padding='max_length', return_tensors='pt')
#   tokens['input_ids'].append(new_tokens['input_ids'][0])
#   tokens['attention_mask'].append(new_tokens['attention_mask'][0])

# tokens['input_ids']= torch.stack(tokens['input_ids'])
# tokens['attention_mask']= torch.stack(tokens['attention_mask'])

import torch
import faiss

batch_size = 32  # adjust as needed
input_ids = []
attention_mask = []

index = faiss.IndexFlatIP(768)
print(index.is_trained)

num_sentences = 0

tokenizer_kwargs = {'max_length': 512, 'truncation': True, 'padding': 'max_length', 'return_tensors': 'pt'}

for i in range(0, len(sentences), batch_size):
    batch = sentences[i:i+batch_size]
    new_tokens = tokenizer.batch_encode_plus(batch, **tokenizer_kwargs)
    input_ids.append(new_tokens['input_ids'])
    attention_mask.append(new_tokens['attention_mask'])

    with torch.no_grad():
        outputs = model(new_tokens['input_ids'], new_tokens['attention_mask'])

    embeddings = outputs.last_hidden_state
    attention_mask_batch = new_tokens['attention_mask'].unsqueeze(-1).expand_as(embeddings).float()
    masked_embeddings = embeddings * attention_mask_batch
    summed = torch.sum(masked_embeddings, 1)
    summed_mask = torch.clamp(attention_mask_batch.sum(1), min=1e-9)
    mean_pooled_batch = summed / summed_mask

    # Add the mean-pooled embeddings to the FAISS index
    index.add(mean_pooled_batch.numpy().astype('float32'))

    num_sentences += len(batch)

    del new_tokens, embeddings, attention_mask_batch, masked_embeddings, summed, summed_mask, mean_pooled_batch

print(index.ntotal)

# import torch
# import faiss
# input_ids = []
# attention_mask = []

# for sentence in sentences:
#     new_tokens = tokenizer.encode_plus(sentence,max_length=512,truncation=True, padding='max_length', return_tensors='pt')
#     input_ids.append(new_tokens['input_ids'][0])
#     attention_mask.append(new_tokens['attention_mask'][0])

# input_ids = torch.stack(input_ids)
# attention_mask = torch.stack(attention_mask)


# with torch.no_grad():
#     outputs = model(input_ids, attention_mask)

# embeddings = outputs.last_hidden_state
# attention_mask = attention_mask.unsqueeze(-1).expand_as(embeddings).float()
# masked_embeddings = embeddings * attention_mask
# summed = torch.sum(masked_embeddings,1)
# summed_mask = torch.clamp(attention_mask.sum(1), min=1e-9)
# mean_pooled = summed / summed_mask

len(mean_pooled)

import faiss
index = faiss.IndexFlatIP(768)
print(index.is_trained)
index.add(mean_pooled)
print(index.ntotal)

#COSINE SIMILARITY PART

def convert_to_embedding(query):
  tokens={'input_ids' : [], 'attention_mask': []}
  new_tokens = tokenizer.encode_plus(query,max_length=512,truncation=True, padding='max_length', return_tensors='pt')
  tokens['input_ids'].append(new_tokens['input_ids'][0])
  tokens['attention_mask'].append(new_tokens['attention_mask'][0])
  tokens['input_ids']= torch.stack(tokens['input_ids'])
  tokens['attention_mask']= torch.stack(tokens['attention_mask'])
  with torch.no_grad():
    outputs = model(**tokens)
  embeddings = outputs.last_hidden_state
  attention_mask = tokens['attention_mask']
  mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
  masked_embeddings = embeddings * mask
  summed = torch.sum(masked_embeddings,1)
  summed_mask = torch.clamp(mask.sum(1), min=1e-9)
  mean_pooled = summed / summed_mask

  return mean_pooled[0] #assuming qeury is a single sentence

query = "Samsung Galaxy"

faiss.write_index(index,"testing1.index")

import faiss
index_loaded = faiss.read_index("testing1.index")

print(index_loaded.ntotal)

# Create a list of tuples containing the sentence and its corresponding similarity score
sentence_sim_scores = []
for i in range(len(I[0])):
    sentence_sim_scores.append((df.iloc[i], D[0][i]))

# Print the list of sentences and their corresponding similarity scores
for sentence, sim_score in sentence_sim_scores:
    print("Sentence: ", sentence)
    print("Similarity score: ", sim_score)
    print("\n")

query_embedding = convert_to_embedding(query)
    D, I = index_loaded.search(query_embedding[None, :], 3)
    related_entries = []
    for i in I[0]:
        if i < len(df):
            related_entries.append(df.iloc[i])
    print(f"Query: {query}")
    print("Related Entries:")
    for entry in related_entries:
        print(entry)
    print()

print(df.head())

print(related_entries)

import torch

torch.cuda.is_available()