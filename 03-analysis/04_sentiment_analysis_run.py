import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings('ignore')

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)

def find_project_root():
    current = os.getcwd()
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, '02-preprocessing')):
            return current
        current = os.path.dirname(current)
    return os.getcwd()

PROJECT_DIR = find_project_root()
OUTPUT_DIR = os.path.join(PROJECT_DIR, '03-analysis', 'outputs')
FIGURE_DIR = os.path.join(PROJECT_DIR, '03-analysis', 'figures')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

PERSON = 'mimiminu'  # or 'bodeoum_tv'
MODEL_NAME = 'Copycats/koelectra-base-v3-generalized-sentiment-analysis'
BATCH_SIZE = 32

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
print(f"Model: {MODEL_NAME}")
print(f"Person: {PERSON}")
print(f"Project root: {PROJECT_DIR}")

comments_path = os.path.join(PROJECT_DIR, '02-preprocessing', 'outputs', PERSON, 'comments.csv')
comments_df = pd.read_csv(comments_path)

print(f"Total comments: {len(comments_df)}")
print(f"Columns: {comments_df.columns.tolist()}")
print(f"Windows: {comments_df['window'].unique()}")
print(f"Slots: {sorted(comments_df['slot'].unique(), key=lambda x: (x.split('-')[0], int(x.split('-')[1]) if '-' in x else 0))}")
print(f"Empty text_clean: {comments_df['text_clean'].isna().sum()}")

print(f"\nComments per window:")
print(comments_df.groupby('window').size())

print(f"\nComments per slot:")
slot_counts = comments_df.groupby(['window', 'slot']).size().reset_index(name='count')
slot_counts = slot_counts.sort_values(['window', 'slot'])
print(slot_counts.to_string(index=False))

print(f"\nSample comments:")
print(comments_df[['text_clean', 'window', 'slot']].head(3))

# ============================================================
# Phase 3: Model Loading & Sentiment Scoring
# ============================================================

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading model...")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.to(device)
model.eval()

print(f"\nModel label mapping: {model.config.id2label}")
print(f"Number of labels: {model.config.num_labels}")

CONFIDENCE_THRESHOLD = 0.6
NEUTRAL_LOW = 0.4

def convert_to_3class(pred_idx, confidence):
    if model.config.num_labels == 2:
        if pred_idx == 0:
            label = 'NEGATIVE'
        else:
            label = 'POSITIVE'
        if NEUTRAL_LOW <= confidence <= CONFIDENCE_THRESHOLD:
            label = 'NEUTRAL'
    else:
        label = list(model.config.id2label.values())[pred_idx]
    return label

print(f"\nNEUTRAL threshold: {NEUTRAL_LOW} - {CONFIDENCE_THRESHOLD}")
print(f"For 2-class model: confidence in [{NEUTRAL_LOW}, {CONFIDENCE_THRESHOLD}] = NEUTRAL")

from tqdm import tqdm

person_output_dir = os.path.join(OUTPUT_DIR, PERSON)
os.makedirs(person_output_dir, exist_ok=True)

def get_sentiment_batch(texts):
    inputs = tokenizer(texts, return_tensors='pt', padding=True,
                       truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        preds = torch.argmax(probs, dim=-1)
        scores = probs.max(dim=-1).values
    
    return preds.cpu().numpy(), scores.cpu().numpy()

CHECKPOINT_INTERVAL = 2000
predictions = []
confidences = []

print(f"Processing {len(comments_df)} comments...")
print(f"Batch size: {BATCH_SIZE}")

for i in tqdm(range(0, len(comments_df), BATCH_SIZE)):
    batch = comments_df['text_clean'].iloc[i:i+BATCH_SIZE].tolist()
    preds, scores = get_sentiment_batch(batch)
    predictions.extend(preds)
    confidences.extend(scores)
    
    if (i + BATCH_SIZE) % CHECKPOINT_INTERVAL == 0:
        checkpoint_df = comments_df.iloc[:i+BATCH_SIZE].copy()
        checkpoint_df['sentiment_idx'] = predictions[:i+BATCH_SIZE]
        checkpoint_df['sentiment_score'] = confidences[:i+BATCH_SIZE]
        checkpoint_df['sentiment_label'] = [convert_to_3class(p, c) for p, c in 
                                            zip(predictions[:i+BATCH_SIZE], confidences[:i+BATCH_SIZE])]
        checkpoint_path = os.path.join(person_output_dir, f'sentiment_checkpoint_{i+BATCH_SIZE}.csv')
        checkpoint_df.to_csv(checkpoint_path, index=False)
        print(f"\nCheckpoint saved: {checkpoint_path}")

comments_df['sentiment_idx'] = predictions
comments_df['sentiment_score'] = confidences
comments_df['sentiment_label'] = [convert_to_3class(p, c) for p, c in zip(predictions, confidences)]

print(f"\nSentiment distribution:")
print(comments_df['sentiment_label'].value_counts())
print(f"\nSample predictions:")
print(comments_df[['text_clean', 'sentiment_label', 'sentiment_score']].head(5))

# TODO: Aggregate by slot
#
# sentiment_by_slot = comments_df.groupby('slot').agg({
#     'sentiment_score': 'mean',
#     'sentiment_label': lambda x: (x == 'POSITIVE').sum() / len(x) * 100,
#     'sentiment_label': lambda x: (x == 'NEGATIVE').sum() / len(x) * 100,
#     'sentiment_label': lambda x: (x == 'NEUTRAL').sum() / len(x) * 100,
#     'comment_id': 'count'
# }).rename(columns={'comment_id': 'n_comments'})


# TODO: Recovery analysis
#
# pre_mean = sentiment_by_slot.loc[pre_slots, 'mean_sentiment'].mean()
#
# Find nadir (minimum sentiment)
# nadir_slot = sentiment_by_slot['mean_sentiment'].idxmin()
# nadir_value = sentiment_by_slot['mean_sentiment'].min()
#
# Find recovery point (3 consecutive slots >= pre_mean)
# post_slots = [s for s in sentiment_by_slot.index if 'post' in s]
# Check for 3 consecutive slots meeting threshold


# TODO: Visualization
#
# fig, axes = plt.subplots(2, 2, figsize=(14, 10))
#
# 1. Sentiment trajectory line plot
# 2. Bar chart by window
# 3. Markers for nadir and recovery
# 4. Box plot distribution
#
# Save to: 03-analysis/figures/{PERSON}_sentiment_*.png


# TODO: Export outputs
#
# person_output_dir = os.path.join(OUTPUT_DIR, PERSON)
# os.makedirs(person_output_dir, exist_ok=True)
#
# sentiment_by_slot.to_csv(os.path.join(person_output_dir, 'sentiment_by_slot.csv'))
# sentiment_by_window.to_csv(os.path.join(person_output_dir, 'sentiment_by_window.csv'))
# comments_df.to_csv(os.path.join(person_output_dir, 'sentiment_comments.csv'), index=False)
# recovery_df.to_csv(os.path.join(person_output_dir, 'recovery_analysis.csv'))


# ============================================================
# Phase 4: Aggregation
# ============================================================

print("\n" + "="*50)
print("Phase 4: Aggregation")
print("="*50)

# Define slot order (chronological)
pre_slots = [f'pre-{i}' for i in range(1, 11)]
cancel_slots = ['cancel-1']
post_slots = [f'post-{i}' for i in range(1, 11)]
slot_order = pre_slots + cancel_slots + post_slots

# Slot-level aggregation
sentiment_by_slot = comments_df.groupby('slot').agg({
    'sentiment_score': 'mean'
}).rename(columns={'sentiment_score': 'mean_sentiment'})

sentiment_by_slot['n_comments'] = comments_df.groupby('slot')['comment_id'].count()

# Calculate percentages per slot
for label in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
    sentiment_by_slot[f'pct_{label.lower()}'] = comments_df.groupby('slot')['sentiment_label'].apply(
        lambda x: (x == label).sum() / len(x) * 100
    )

# Reorder chronologically
sentiment_by_slot = sentiment_by_slot.reindex(slot_order)

print("\nSentiment by Slot (chronological order):")
print(sentiment_by_slot.round(2))

# Window-level aggregation
sentiment_by_window = comments_df.groupby('window').agg({
    'sentiment_score': 'mean'
}).rename(columns={'sentiment_score': 'mean_sentiment'})

sentiment_by_window['n_comments'] = comments_df.groupby('window')['comment_id'].count()

for label in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
    sentiment_by_window[f'pct_{label.lower()}'] = comments_df.groupby('window')['sentiment_label'].apply(
        lambda x: (x == label).sum() / len(x) * 100
    )

# Reorder: pre, cancel, post
sentiment_by_window = sentiment_by_window.reindex(['pre', 'cancel', 'post'])

print("\nSentiment by Window:")
print(sentiment_by_window.round(2))

# Summary statistics
pre_mean = sentiment_by_window.loc['pre', 'mean_sentiment']
cancel_mean = sentiment_by_window.loc['cancel', 'mean_sentiment']
post_mean = sentiment_by_window.loc['post', 'mean_sentiment']

print("\n" + "="*50)
print("Summary:")
print(f"Pre mean sentiment: {pre_mean:.4f}")
print(f"Cancel mean sentiment: {cancel_mean:.4f}")
print(f"Post mean sentiment: {post_mean:.4f}")
print(f"Cancel vs Pre change: {((cancel_mean - pre_mean) / pre_mean * 100):.1f}%")
print(f"Post vs Pre change: {((post_mean - pre_mean) / pre_mean * 100):.1f}%")
print("="*50)
