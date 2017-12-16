import os
import subprocess
import numpy as np
from hashlib import sha1

import pandas as pd

import keras.models
from keras.preprocessing.sequence import pad_sequences

from glove_keras import pretrained_glove_keras_model_conv
from glove_keras import pretrained_glove_keras_model_lstm

BASE_DIR = '../data'
SENT2VEC_MODEL_PATH = os.path.join(BASE_DIR, 'twitter_bigrams.bin')
FASTTEXT_PATH = os.path.join('..','sent2vec','fasttext')

class KerasModelWrapper:
  def __init__(self, model, id, batch_size, epochs, architecture=None, tokenizer=None, max_seq_len=None):
    self.model = model
    self.id = id
    self.fit_params = {
      'batch_size':batch_size,
      'epochs':epochs
    }
    self.architecture = architecture 
    self.tokenizer = tokenizer
    self.max_seq_len = max_seq_len
    if model is not None:
        self.model_weights = model.get_weights()

  def fit(self, X, y):
    y = y.copy()
    y[y==-1] = 0

    if self.architecture == 'sent2vec':
      X = self._get_sent2vec_embeddings(X)
      self.model.set_weights(self.model_weights)
    elif self.architecture == 'glove_conv':
      self.model, X, self.tokenizer, self.max_seq_len = pretrained_glove_keras_model_conv(X)
    elif self.architecture == 'glove_lstm':
      self.model, X, self.tokenizer, self.max_seq_len = pretrained_glove_keras_model_lstm(X)


    identifier_x = sha1(X).hexdigest()
    identifier_y = sha1(y).hexdigest()

    model_save_filepath = self.id + identifier_x + identifier_y + '.hdf5'

    if os.path.isfile(model_save_filepath):
      self.model = keras.models.load_model(model_save_filepath)
    else:
      self.model.fit(X, y, **self.fit_params)
      self.model.save(model_save_filepath)

  def predict(self, X):
    if self.architecture == 'sent2vec':
        X = self._get_sent2vec_embeddings(X)
    elif self.architecture in ['glove_conv','glove_lstm']:
        X = self.tokenizer.texts_to_sequences(X)
        X = pad_sequences(X, maxlen=self.max_seq_len)

    preds = self.model.predict(X)
    preds[preds==0] = -1
    return preds

  def score(self, X, y):
    if self.sent2vec:
        X = self._get_sent2vec_embeddings(X)
    else:
        X = self.tokenizer.text_to_sequences(X)
        X = pad_sequences(X, maxlen=self.max_seq_len)

    y = y.copy()
    y[y==-1]=0
    preds = self.model.predict(X)

    return (np.count_nonzero(preds == y) * 1.0) / len(y)

  def _get_sent2vec_embeddings(self, tweets):
    SWAP_FILE_TWEETS = 'sent2vec_tweets'
    SWAP_FILE_EMBEDDINGS = 'sent2vec_embeddings'

    with open(SWAP_FILE_TWEETS, 'w', encoding='utf8') as f:
      for tweet in tweets:
        f.write(tweet.strip() + '\n')
      f.flush()

    print(subprocess.call(FASTTEXT_PATH +
                    ' print-sentence-vectors ' +
                    SENT2VEC_MODEL_PATH +
                    ' < ' +
                    SWAP_FILE_TWEETS +
                    ' > ' +
                    SWAP_FILE_EMBEDDINGS, shell=True))


    df = pd.read_csv(SWAP_FILE_EMBEDDINGS, sep=' ', header=None)
    df.drop(df.columns[-1], axis=1, inplace=True)
    embeddings = df.values.astype('float64')

    os.remove(SWAP_FILE_TWEETS)
    os.remove(SWAP_FILE_EMBEDDINGS)

    return embeddings.copy(order='C')
