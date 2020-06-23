from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers.core import Dense
import random
import numpy as np
import collections


class Agent(object):
    def __init__(self, params):
        self.reward = 0
        self.gamma = 0.9
        self.learning_rate = params["learning_rate"]
        self.first_layer = params["first_layer_size"]
        self.second_layer = params["second_layer_size"]
        self.third_layer = params["third_layer_size"]
        self.memory = collections.deque(maxlen=params["memory_size"])
        self.weights_path = params["weights_path"]
        self.train = params["train"]
        self.model = self.network()

    def network(self):
        model = Sequential()
        model.add(Dense(output_dim=self.first_layer, activation="relu", input_dim=4))
        model.add(Dense(output_dim=self.second_layer, activation="relu"))
        model.add(Dense(output_dim=self.third_layer, activation="relu"))
        model.add(Dense(output_dim=2, activation="softmax"))
        model.compile(loss="mse", optimizer=Adam(self.learning_rate))

        if not self.train:
            model.load_weights(self.weights_path)

        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay_new(self, batch_size):
        if len(self.memory) > batch_size:
            minibatch = random.sample(self.memory, batch_size)
        else:
            minibatch = self.memory
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(
                    self.model.predict(np.array([next_state]))[0]
                )
            target_f = self.model.predict(np.array([state]))
            target_f[0][np.argmax(action)] = target
            self.model.fit(np.array([state]), target_f, epochs=1, verbose=0)

    def train_short_memory(self, state, action, reward, next_state, done):
        target = reward
        if not done:
            target = reward + self.gamma * np.amax(
                self.model.predict(next_state.reshape((1, 4)))[0]
            )
        target_f = self.model.predict(state.reshape((1, 4)))
        target_f[0][np.argmax(action)] = target
        self.model.fit(state.reshape((1, 4)), target_f, epochs=1, verbose=0)
