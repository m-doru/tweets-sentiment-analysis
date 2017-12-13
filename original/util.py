import numpy as np
from sklearn.model_selection import train_test_split
import logging

def shuffle_dataset(X, y):
    p = np.random.permutation(len(y))

    X = X[p]
    y = y[p]

    return X, y

def construct_dataset_from_files(filenames, split_size=0.1):
    logging.info("Loading data from files: " + str(filenames))
    print("Loading data from files: " + str(filenames))

    X = []
    y = []

    for filename, label in filenames.items():
        with open(filename, 'r', encoding='utf8') as f:
            for tweet in f:
                X.append(tweet)
                y.append(label)

    X = np.array(X)
    y = np.array(y)

    X, y = shuffle_dataset(X, y)

    if split_size is not None:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=split_size, random_state=100)
        return X_train, y_train, X_test, y_test

    return X, y

